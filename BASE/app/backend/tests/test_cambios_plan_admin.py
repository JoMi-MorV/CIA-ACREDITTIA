from __future__ import annotations

import uuid
from datetime import date, timedelta

from sqlalchemy import text

from tests.conftest import API


def _crear_plan(motor_admin, *, activo: bool = True) -> tuple[str, str]:
    nombre = f"Plan autorización {uuid.uuid4().hex[:10]}"
    with motor_admin.begin() as conn:
        plan_id = conn.execute(text(
            "INSERT INTO planes (nombre, precio, moneda, periodo, activo) "
            "VALUES (:nombre, 1, 'UF', 'mensual', :activo) RETURNING id"),
            {"nombre": nombre, "activo": activo}).scalar_one()
    return str(plan_id), nombre


def _crear_suscripcion(
        motor_admin, company_id: str, plan_id: str, *, estado: str = "morosa"
) -> dict:
    inicio = date.today()
    termino = inicio + timedelta(days=30)
    with motor_admin.begin() as conn:
        suscripcion_id = conn.execute(text(
            "INSERT INTO suscripciones "
            "(company_id, plan_id, estado, periodo_actual_desde, "
            "periodo_actual_hasta) "
            "VALUES (:company_id, :plan_id, :estado, :inicio, :termino) "
            "RETURNING id"),
            {"company_id": company_id, "plan_id": plan_id,
             "estado": estado, "inicio": inicio, "termino": termino}).scalar_one()
    return {"id": str(suscripcion_id), "inicio": inicio, "termino": termino}


def test_empresa_no_puede_cambiar_plan_de_suscripcion_existente(
        app_cliente, motor_admin, empresa_a):
    plan_actual, _ = _crear_plan(motor_admin)
    plan_nuevo, _ = _crear_plan(motor_admin)
    _crear_suscripcion(motor_admin, empresa_a["company_id"], plan_actual)

    respuesta = app_cliente.post(
        f"{API}/suscripcion", headers=empresa_a["headers"],
        json={"plan_id": plan_nuevo})

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "AUTORIZACION_ADMIN_REQUERIDA"
    with motor_admin.connect() as conn:
        plan_guardado = conn.execute(text(
            "SELECT plan_id FROM suscripciones WHERE company_id = :company_id"),
            {"company_id": empresa_a["company_id"]}).scalar_one()
    assert str(plan_guardado) == plan_actual


def test_empresa_puede_iniciar_el_trial_inicial(
        app_cliente, motor_admin, empresa_a):
    plan_id, _ = _crear_plan(motor_admin)

    respuesta = app_cliente.post(
        f"{API}/suscripcion", headers=empresa_a["headers"],
        json={"plan_id": plan_id})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["suscripcion"]["plan"]["id"] == plan_id
    assert respuesta.json()["suscripcion"]["estado"] == "trial"


def test_empresa_puede_reactivar_suscripcion_con_el_mismo_plan(
        app_cliente, motor_admin, empresa_a):
    plan_id, _ = _crear_plan(motor_admin)
    _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_id, estado="cancelada")

    respuesta = app_cliente.post(
        f"{API}/suscripcion", headers=empresa_a["headers"],
        json={"plan_id": plan_id})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["suscripcion"]["estado"] == "activa"


def test_cancelacion_conserva_acceso_hasta_fin_del_periodo(
        app_cliente, motor_admin, empresa_a):
    plan_id, _ = _crear_plan(motor_admin)
    suscripcion = _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_id, estado="activa")

    respuesta = app_cliente.delete(
        f"{API}/suscripcion", headers=empresa_a["headers"])

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado"] == "cancelada"
    assert respuesta.json()["acceso"] == "completo"
    assert respuesta.json()["vigente_hasta"] == suscripcion["termino"].isoformat()
    with motor_admin.connect() as conn:
        periodo_guardado = conn.execute(text(
            "SELECT periodo_actual_hasta FROM suscripciones "
            "WHERE company_id = :company_id"),
            {"company_id": empresa_a["company_id"]}).scalar_one()
    assert periodo_guardado == suscripcion["termino"]


def test_cancelada_vencida_solo_permite_lectura_y_reactivacion(
        app_cliente, motor_admin, empresa_a):
    plan_id, _ = _crear_plan(motor_admin)
    _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_id, estado="cancelada")
    ayer = date.today() - timedelta(days=1)
    anteayer = date.today() - timedelta(days=2)
    with motor_admin.begin() as conn:
        conn.execute(text(
            "UPDATE suscripciones SET periodo_actual_desde = :anteayer, "
            "periodo_actual_hasta = :ayer "
            "WHERE company_id = :company_id"),
            {"anteayer": anteayer, "ayer": ayer,
             "company_id": empresa_a["company_id"]})

    lectura = app_cliente.get(
        f"{API}/suscripcion", headers=empresa_a["headers"])
    assert lectura.status_code == 200, lectura.text
    assert lectura.json()["acceso"] == "solo_lectura"

    escritura = app_cliente.post(
        f"{API}/company/usuarios", headers=empresa_a["headers"],
        json={"email": "bloqueado@empresa.cl", "nombre": "Bloqueado",
              "role": "company"})
    assert escritura.status_code == 403
    assert escritura.json()["error"]["code"] == "SUSCRIPCION_SOLO_LECTURA"

    reactivada = app_cliente.post(
        f"{API}/suscripcion", headers=empresa_a["headers"],
        json={"plan_id": plan_id})
    assert reactivada.status_code == 200, reactivada.text
    assert reactivada.json()["suscripcion"]["estado"] == "activa"
    assert reactivada.json()["suscripcion"]["acceso"] == "completo"


def test_solicitud_de_plan_espera_aprobacion_admin_y_conserva_periodo(
        app_cliente, motor_admin, admin, empresa_a):
    plan_actual, nombre_actual = _crear_plan(motor_admin)
    plan_solicitado, nombre_solicitado = _crear_plan(motor_admin)
    suscripcion = _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_actual)
    body = {
        "tipo": "cambio_plan",
        "plan_id": plan_solicitado,
        "motivo": "Necesitamos ampliar los usuarios del servicio",
    }

    solicitud = app_cliente.post(
        f"{API}/suscripcion/solicitudes",
        headers=empresa_a["headers"], json=body)

    assert solicitud.status_code == 201, solicitud.text
    solicitud_data = solicitud.json()
    assert solicitud_data["estado"] == "pendiente"
    assert solicitud_data["plan"]["id"] == plan_solicitado
    propias = app_cliente.get(
        f"{API}/suscripcion/solicitudes", headers=empresa_a["headers"])
    assert propias.status_code == 200
    assert propias.json()["items"][0]["id"] == solicitud_data["id"]
    admin_listado = app_cliente.get(
        f"{API}/admin/suscripciones/{empresa_a['company_id']}/solicitudes",
        headers=admin["headers"])
    assert admin_listado.status_code == 200
    assert admin_listado.json()["items"][0]["estado"] == "pendiente"
    bandeja = app_cliente.get(
        f"{API}/admin/suscripciones/solicitudes?page_size=10",
        headers=admin["headers"])
    assert bandeja.status_code == 200
    assert any(item["id"] == solicitud_data["id"]
               for item in bandeja.json()["items"])
    with motor_admin.connect() as conn:
        fila = conn.execute(text(
            "SELECT plan_id FROM suscripciones WHERE company_id = :company_id"),
            {"company_id": empresa_a["company_id"]}).scalar_one()
    assert str(fila) == plan_actual

    no_admin = app_cliente.patch(
        f"{API}/admin/suscripciones/solicitudes/"
        f"{solicitud_data['id']}/resolver",
        headers=empresa_a["headers"],
        json={"decision": "aprobada", "motivo": "Revisión autorizada por admin"})
    assert no_admin.status_code == 403
    assert no_admin.json()["error"]["code"] == "SOLO_ADMIN"

    motivo_invalido = app_cliente.patch(
        f"{API}/admin/suscripciones/solicitudes/"
        f"{solicitud_data['id']}/resolver",
        headers=admin["headers"],
        json={"decision": "aprobada", "motivo": "corto"})
    assert motivo_invalido.status_code == 422

    respuesta = app_cliente.patch(
        f"{API}/admin/suscripciones/solicitudes/"
        f"{solicitud_data['id']}/resolver",
        headers=admin["headers"],
        json={"decision": "aprobada", "motivo": "Revisión autorizada por admin"})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["solicitud"]["estado"] == "aprobada"
    assert respuesta.json()["suscripcion"]["plan"]["id"] == plan_solicitado
    assert respuesta.json()["suscripcion"]["estado"] == "morosa"
    assert respuesta.json()["suscripcion"]["periodo_actual_desde"] == (
        suscripcion["inicio"].isoformat())
    assert respuesta.json()["suscripcion"]["periodo_actual_hasta"] == (
        suscripcion["termino"].isoformat())
    with motor_admin.connect() as conn:
        registro = conn.execute(text(
            "SELECT user_id, metadata FROM actividad "
            "WHERE entidad_tipo = 'solicitud_suscripcion' AND entidad_id = :id "
            "ORDER BY id DESC LIMIT 1"),
            {"id": solicitud_data["id"]}).mappings().one()
    assert str(registro["user_id"]) == admin["user_id"]
    assert registro["metadata"]["decision"] == "aprobada"
    assert registro["metadata"]["motivo_resolucion"] == "Revisión autorizada por admin"
    assert registro["metadata"]["cambios"]["plan"]["antes"] == nombre_actual
    assert registro["metadata"]["cambios"]["plan"]["despues"] == nombre_solicitado


def test_solicitud_plan_exige_suscripcion_y_plan_activo(
        app_cliente, motor_admin, empresa_a, empresa_b):
    plan_inactivo, _ = _crear_plan(motor_admin, activo=False)
    plan_activo, _ = _crear_plan(motor_admin)
    _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_activo)

    inactivo = app_cliente.post(
        f"{API}/suscripcion/solicitudes", headers=empresa_a["headers"],
        json={
            "tipo": "cambio_plan",
            "plan_id": plan_inactivo,
            "motivo": "Solicito el cambio de plan indicado",
        })
    assert inactivo.status_code == 400
    assert inactivo.json()["error"]["code"] == "PLAN_INACTIVO"

    sin_suscripcion = app_cliente.post(
        f"{API}/suscripcion/solicitudes", headers=empresa_b["headers"],
        json={
            "tipo": "cambio_plan",
            "plan_id": plan_activo,
            "motivo": "Solicito el cambio de plan indicado",
        })
    assert sin_suscripcion.status_code == 409
    assert sin_suscripcion.json()["error"]["code"] == "SIN_SUSCRIPCION"


def test_regularizacion_pendiente_requiere_admin_y_no_modifica_facturas(
        app_cliente, motor_admin, admin, empresa_a):
    plan_id, _ = _crear_plan(motor_admin)
    suscripcion = _crear_suscripcion(
        motor_admin, empresa_a["company_id"], plan_id, estado="activa")
    with motor_admin.begin() as conn:
        factura_id = conn.execute(text(
            "INSERT INTO facturas "
            "(suscripcion_id, company_id, monto, moneda, estado, emitida_at) "
            "VALUES (:suscripcion_id, :company_id, 100, 'CLP', 'pendiente', "
            "now() - interval '45 days') RETURNING id"),
            {"suscripcion_id": suscripcion["id"],
             "company_id": empresa_a["company_id"]}).scalar_one()

    estado_inicial = app_cliente.get(
        f"{API}/suscripcion", headers=empresa_a["headers"])
    assert estado_inicial.status_code == 200, estado_inicial.text
    assert estado_inicial.json()["estado_cuenta"] == "moroso"

    solicitud = app_cliente.post(
        f"{API}/suscripcion/solicitudes",
        headers=empresa_a["headers"],
        json={
            "tipo": "regularizacion",
            "motivo": "La cuenta fue revisada con administración",
        })

    assert solicitud.status_code == 201, solicitud.text
    assert solicitud.json()["estado"] == "pendiente"
    estado_pendiente = app_cliente.get(
        f"{API}/suscripcion", headers=empresa_a["headers"])
    assert estado_pendiente.json()["estado_cuenta"] == "moroso"

    respuesta = app_cliente.patch(
        f"{API}/admin/suscripciones/solicitudes/"
        f"{solicitud.json()['id']}/resolver",
        headers=admin["headers"],
        json={"decision": "aprobada", "motivo": "Regularización administrativa aprobada"})

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["estado_cuenta"] == "al_dia"
    with motor_admin.connect() as conn:
        estado, pagada_at = conn.execute(text(
            "SELECT estado, pagada_at FROM facturas WHERE id = :id"),
            {"id": str(factura_id)}).one()
        auditoria = conn.execute(text(
            "SELECT user_id, metadata FROM actividad "
            "WHERE entidad_tipo = 'solicitud_suscripcion' AND entidad_id = :id "
            "ORDER BY id DESC LIMIT 1"),
            {"id": solicitud.json()["id"]}).mappings().one()
    assert estado == "pendiente"
    assert pagada_at is None
    assert str(auditoria["user_id"]) == admin["user_id"]
    assert auditoria["metadata"]["cambios"]["estado_cuenta"] == {
        "antes": "moroso", "despues": "al_dia"}
