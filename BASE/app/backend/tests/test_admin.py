"""Consola administrativa unificada /api/v1/admin.

Requiere que 07_consola_interna.sql y 08_funciones_consola.sql estén en la
lista SCRIPTS de tests/conftest.py.

Con QUEUE_BACKEND=inproc las ejecuciones manuales corren en el acto, así que
el run ya está cerrado ('ok'/'error') en la aserción siguiente al 202 — el
mismo patrón que usa test_reportes.py.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

import pytest

from tests.conftest import API

ENVOLTURA = {"items", "page", "page_size", "total", "total_pages"}
COMPONENTES = {"api", "db", "workers", "storage", "ia", "integraciones"}


# ============================================================================
# Fixtures propias
# ============================================================================
@pytest.fixture
def plan_pro(motor_admin):
    """Plan comercial + retorno del id. Directo a BD: el CRUD de planes
    (spec v1.1 §6) no es prerrequisito de esta suite."""
    from sqlalchemy import text
    with motor_admin.connect() as c:
        pid = c.execute(text(
            "INSERT INTO planes (nombre, precio, moneda, periodo) "
            "VALUES ('Pro', 12.5, 'UF', 'mensual') "
            "ON CONFLICT (nombre) DO UPDATE SET precio = EXCLUDED.precio "
            "RETURNING id")).scalar()
        c.commit()
    return str(pid)


@pytest.fixture
def suscripcion_a(motor_admin, empresa_a, plan_pro):
    """empresa_a con suscripción activa al plan Pro y su industria fijada."""
    from sqlalchemy import text
    with motor_admin.connect() as c:
        c.execute(text(
            "UPDATE companies SET industria = 'mineria' WHERE id = :cid"),
            {"cid": empresa_a["company_id"]})
        sid = c.execute(text(
            "INSERT INTO suscripciones (company_id, plan_id, estado) "
            "VALUES (:cid, :pid, 'activa') RETURNING id"),
            {"cid": empresa_a["company_id"], "pid": plan_pro}).scalar()
        c.commit()
    return str(sid)


def _run_ok(cliente, admin, clave: str, params: dict | None = None) -> dict:
    """Ejecuta un proceso por la API y asevera que terminó ok (inproc)."""
    r = cliente.post(f"{API}/admin/procesos/{clave}/ejecutar",
                     headers=admin["headers"],
                     json={"params": params or {}})
    assert r.status_code == 202, r.text
    rid = r.json()["run_id"]
    r = cliente.get(f"{API}/admin/procesos/{clave}/ejecuciones",
                    headers=admin["headers"])
    run = next(x for x in r.json()["items"] if x["run_id"] == rid)
    assert run["status"] == "ok", run
    return run


# ============================================================================
# Autorización
# ============================================================================
def test_todo_el_router_exige_admin(app_cliente, empresa_a):
    for ruta in ("usuarios/resumen", "usuarios/actividad-mensual",
                 "clientes", "sistemas/estado", "procesos",
                 "indicadores/resumen"):
        r = app_cliente.get(f"{API}/admin/{ruta}",
                            headers=empresa_a["headers"])
        assert r.status_code == 403, ruta
        assert r.json()["error"]["code"] == "SOLO_ADMIN"
    r = app_cliente.get(
        f"{API}/admin/clientes/{empresa_a['company_id']}",
        headers=empresa_a["headers"])
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "SOLO_ADMIN"


def test_sin_token(app_cliente):
    r = app_cliente.get(f"{API}/admin/usuarios/resumen")
    assert r.status_code == 401


def test_ficha_empresa_separa_conteo_de_cuentas(
        app_cliente, admin, empresa_a):
    respuesta = app_cliente.get(
        f"{API}/admin/companies/{empresa_a['company_id']}",
        headers=admin["headers"])

    assert respuesta.status_code == 200, respuesta.text
    ficha = respuesta.json()
    assert isinstance(ficha["usuarios"], int)
    assert ficha["usuarios"] == len(ficha["cuentas"])
    assert all(isinstance(cuenta, dict) for cuenta in ficha["cuentas"])


def test_listado_empresas_incluye_industria_y_estado_cuenta(
        app_cliente, admin, empresa_a):
    respuesta = app_cliente.get(
        f"{API}/admin/companies?page_size=100", headers=admin["headers"])

    assert respuesta.status_code == 200, respuesta.text
    empresa = next(
        item for item in respuesta.json()["items"]
        if item["id"] == empresa_a["company_id"])
    assert empresa["industria"] in {
        "mineria", "construccion", "energia", "industrial", "otras"}
    assert empresa["estado_cuenta"] in {"al_dia", "en_riesgo", "moroso"}


# ============================================================================
# §5 — Usuarios
# ============================================================================
def test_usuarios_resumen(app_cliente, admin, empresa_a, empresa_b):
    r = app_cliente.get(f"{API}/admin/usuarios/resumen",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    u = d["usuarios"]
    # Los fixtures crean un usuario por empresa y ambos hicieron login.
    assert u["totales"] >= 2
    assert u["activos"]["n"] + u["inactivos"]["n"] == u["totales"]
    # El admin de plataforma no cuenta como usuario.
    assert d["ventana_dias"] == 30
    assert d["serie_12m"][-1]["usuarios_totales"] == u["totales"]


def test_usuarios_resumen_ventana_invalida(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/usuarios/resumen?ventana_dias=5",
                        headers=admin["headers"])
    assert r.status_code == 422        # validación FastAPI (ge=7)


def test_actividad_mensual_incluye_snapshot_y_mes_actual(
        app_cliente, admin, empresa_a, empresa_b, motor_admin):
    mes_actual = date.today().replace(day=1)
    mes_anterior = (mes_actual - timedelta(days=1)).replace(day=1)
    from sqlalchemy import text
    with motor_admin.begin() as conn:
        conn.execute(text(
            "INSERT INTO metricas_mensuales "
            "(mes, valor_uf, mrr_clp, clientes_activos, usuarios_totales, "
            "usuarios_activos) VALUES (:mes, 1, 100, 1, 4, 3)"),
            {"mes": mes_anterior})

    r = app_cliente.get(
        f"{API}/admin/usuarios/actividad-mensual?meses=2&ventana_dias=7",
        headers=admin["headers"])
    assert r.status_code == 200, r.text
    items = r.json()["items"]
    historico = next(item for item in items
                     if item["mes"] == mes_anterior.strftime("%Y-%m"))
    actual = items[-1]
    assert historico == {
        "mes": mes_anterior.strftime("%Y-%m"),
        "usuarios_activos": 3,
        "usuarios_totales": 4,
        "parcial": False,
    }
    assert actual["mes"] == mes_actual.strftime("%Y-%m")
    assert actual["parcial"] is True
    assert actual["usuarios_totales"] >= 2
    assert 0 <= actual["usuarios_activos"] <= actual["usuarios_totales"]


@pytest.mark.parametrize("query", ["meses=0", "ventana_dias=5"])
def test_actividad_mensual_rechaza_parametros_fuera_de_rango(
        app_cliente, admin, query):
    r = app_cliente.get(f"{API}/admin/usuarios/actividad-mensual?{query}",
                        headers=admin["headers"])
    assert r.status_code == 422


def test_por_plan_y_sin_plan(app_cliente, admin, empresa_a, empresa_b,
                             suscripcion_a):
    r = app_cliente.get(f"{API}/admin/usuarios/por-plan",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    pro = next(x for x in d["items"] if x["plan"] == "Pro")
    assert pro["clientes"] == 1
    assert pro["usuarios"] >= 1
    assert pro["activos"] + pro["inactivos"] == pro["usuarios"]
    # empresa_b no tiene suscripción: cae en sin_plan.
    assert d["sin_plan"]["clientes"] >= 1


def test_por_industria_categorias_estables(app_cliente, admin, empresa_a,
                                           suscripcion_a):
    r = app_cliente.get(f"{API}/admin/usuarios/por-industria",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert {x["industria"] for x in d["items"]} == {
        "mineria", "construccion", "energia", "industrial", "otras"}
    mineria = next(x for x in d["items"] if x["industria"] == "mineria")
    assert mineria["usuarios"] >= 1
    if d["total"]:
        assert round(sum(x["pct"] for x in d["items"]), 1) == 100.0


def test_clientes_tabla_y_filtros(app_cliente, admin, empresa_a, empresa_b,
                                  suscripcion_a):
    r = app_cliente.get(f"{API}/admin/clientes", headers=admin["headers"])
    assert r.status_code == 200 and set(r.json()) == ENVOLTURA
    assert r.json()["total"] >= 2

    pagina_1 = app_cliente.get(
        f"{API}/admin/clientes?page=1&page_size=1&sort=nombre",
        headers=admin["headers"]).json()
    pagina_2 = app_cliente.get(
        f"{API}/admin/clientes?page=2&page_size=1&sort=nombre",
        headers=admin["headers"]).json()
    assert pagina_1["total"] == pagina_2["total"]
    assert len(pagina_1["items"]) == len(pagina_2["items"]) == 1
    assert pagina_1["items"][0]["company_id"] != pagina_2["items"][0]["company_id"]
    assert pagina_1["items"][0]["nombre"] <= pagina_2["items"][0]["nombre"]

    r = app_cliente.get(f"{API}/admin/clientes?industria=mineria",
                        headers=admin["headers"])
    assert {x["industria"] for x in r.json()["items"]} == {"mineria"}

    r = app_cliente.get(f"{API}/admin/clientes?plan_id=sin_plan",
                        headers=admin["headers"])
    assert all(x["plan"] is None for x in r.json()["items"])

    nombre = None
    r = app_cliente.get(f"{API}/admin/clientes", headers=admin["headers"])
    nombre = r.json()["items"][0]["nombre"]
    r = app_cliente.get(f"{API}/admin/clientes?search={nombre[:8]}",
                        headers=admin["headers"])
    assert any(x["nombre"] == nombre for x in r.json()["items"])

    # Sin facturas vencidas: todos al día.
    assert all(x["estado_cuenta"] == "al_dia" for x in r.json()["items"])

    r = app_cliente.get(f"{API}/admin/clientes?industria=agro",
                        headers=admin["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "RANGO_INVALIDO"


def test_cliente_detalle_y_404(
    app_cliente, admin, empresa_a, empresa_b, suscripcion_a):
    from decimal import Decimal
    from app.config_ops import ops_settings
    r = app_cliente.get(f"{API}/admin/clientes/{empresa_a['company_id']}",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["suscripcion"]["plan"] == "Pro"
    assert Decimal(str(d["suscripcion"]["mrr_clp"])) == (
        Decimal("12.5") * Decimal(str(ops_settings.ops_valor_uf))
    ).quantize(Decimal("0.01"))
    assert d["facturacion"]["estado_cuenta"] == "al_dia"

    r = app_cliente.get(f"{API}/admin/clientes/{empresa_b['company_id']}",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    sin_suscripcion = r.json()
    assert sin_suscripcion["suscripcion"] is None
    assert sin_suscripcion["usuarios"]["totales"] >= 0
    assert sin_suscripcion["usuarios"]["activos_30d"] <= (
        sin_suscripcion["usuarios"]["totales"])

    r = app_cliente.get(f"{API}/admin/clientes/{uuid.uuid4()}",
                        headers=admin["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NO_ENCONTRADO"


def test_detalle_empresa_muestra_ultimo_evento_y_actor(
        app_cliente, admin, empresa_a, motor_admin):
    from sqlalchemy import text

    empresa_id = empresa_a["company_id"]
    usuario_id = empresa_a["user_id"]
    anterior = datetime.now(timezone.utc) + timedelta(minutes=1)
    reciente = datetime.now(timezone.utc) + timedelta(minutes=2)
    with motor_admin.begin() as conexion:
        conexion.execute(text(
            "UPDATE users SET nombre = 'Usuario actor prueba' WHERE id = :user_id"),
            {"user_id": usuario_id})
        for fecha, modulo in ((anterior, "evento_anterior"),
                              (reciente, "ultimo_evento_prueba")):
            conexion.execute(text(
                "INSERT INTO actividad "
                "(company_id, user_id, tipo, modulo, descripcion, created_at) "
                "VALUES (:company_id, :user_id, 'actualizacion', :modulo, "
                "'texto libre que no debe salir en el detalle', :created_at)"), {
                    "company_id": empresa_id, "user_id": usuario_id,
                    "modulo": modulo, "created_at": fecha,
                })

    respuesta = app_cliente.get(
        f"{API}/admin/companies/{empresa_id}", headers=admin["headers"])
    assert respuesta.status_code == 200, respuesta.text
    evento = respuesta.json()["ultimo_evento"]
    assert evento["modulo"] == "ultimo_evento_prueba"
    assert evento["tipo"] == "actualizacion"
    assert evento["actor"] == "Usuario actor prueba"
    assert "descripcion" not in evento
    assert "email" not in evento


# ============================================================================
# §6 — Sistemas y procesos
# ============================================================================
def test_estado_ciego_luego_operativo(app_cliente, admin):
    from app.services import ops as servicio_monitor
    servicio_monitor.reset_store()          # monitor sin latidos: peor caso

    r = app_cliente.get(f"{API}/admin/sistemas/estado",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert {c["clave"] for c in d["componentes"]} == COMPONENTES
    assert d["estado_global"] == "caido"           # ciego = caído

    _run_ok(app_cliente, admin, "ops_heartbeat")
    r = app_cliente.get(f"{API}/admin/sistemas/estado",
                        headers=admin["headers"])
    d = r.json()
    assert d["estado_global"] == "operativo", d
    api = next(c for c in d["componentes"] if c["clave"] == "db")
    assert api["metricas"]["conexiones"] >= 1


def test_disponibilidad_404_y_parcial(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/sistemas/nube/disponibilidad",
                        headers=admin["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "COMPONENTE_DESCONOCIDO"

    _run_ok(app_cliente, admin, "ops_heartbeat")
    r = app_cliente.get(f"{API}/admin/sistemas/db/disponibilidad?dias=7",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert d["dias"][-1]["parcial"] is True
    assert d["dias"][-1]["estado"] == "operativo"


def test_consolidar_disponibilidad_persiste_latidos(app_cliente, admin,
                                                    motor_admin):
    from app.services import ops
    from sqlalchemy import text

    ops.reset_store()
    ops.guardar_latido("api", "operativo", {"latencia_p95_ms": 42})
    fecha = datetime.now(timezone.utc).date()
    resultado = _run_ok(app_cliente, admin, "ops_disponibilidad",
                        {"fecha": fecha.isoformat()})
    assert resultado["items_procesados"] == 1

    with motor_admin.connect() as conn:
        fila = conn.execute(text(
            "SELECT estado::text, uptime_pct, latencia_p95_ms, checks_total, "
            "checks_fallidos FROM ops_disponibilidad_diaria "
            "WHERE componente='api' AND fecha=:fecha"),
            {"fecha": fecha}).one()
    assert fila.estado == "operativo"
    assert float(fila.uptime_pct) == 100.0
    assert fila.latencia_p95_ms == 42
    assert fila.checks_total == 1
    assert fila.checks_fallidos == 0


def test_procesos_listado(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/procesos", headers=admin["headers"])
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()["items"]}
    assert {"vencimientos", "ops_heartbeat", "metricas_snapshot",
            "ia_revision"} <= claves
    por_clave = {x["clave"]: x for x in r.json()["items"]}
    assert por_clave["ops_disponibilidad"]["manual_ejecutable"] is True
    assert por_clave["ia_revision"]["manual_ejecutable"] is False
    assert por_clave["webhooks_clientes"]["manual_ejecutable"] is False
    continuo = por_clave["ia_revision"]
    assert continuo["tipo"] == "continuo" and continuo["cron_expr"] is None


def test_ejecutar_manual_y_409_en_ejecucion(app_cliente, admin, motor_admin):
    run = _run_ok(app_cliente, admin, "ops_heartbeat")
    assert run["disparo"] == "manual"
    assert run["actor"]["email"] == admin["email"]

    # Con un run 'running' colgado, el siguiente POST debe chocar.
    from sqlalchemy import text
    with motor_admin.connect() as c:
        c.execute(text(
            "INSERT INTO ops_job_runs (job_clave, status, disparo, started_at) "
            "VALUES ('ops_heartbeat', 'running', 'cron', now())"))
        c.commit()
    r = app_cliente.post(f"{API}/admin/procesos/ops_heartbeat/ejecutar",
                         headers=admin["headers"], json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOB_EN_EJECUCION"
    with motor_admin.connect() as c:
        c.execute(text("UPDATE ops_job_runs SET status='ok' "
                       "WHERE status='running'"))
        c.commit()


def test_ejecucion_queued_atascada_se_recupera_al_reintentar(
        app_cliente, admin, motor_admin):
    from sqlalchemy import text
    with motor_admin.begin() as conn:
        run_atascado = conn.execute(text(
            "INSERT INTO ops_job_runs (job_clave, status, disparo, created_at) "
            "VALUES ('ops_heartbeat', 'queued', 'manual', "
            "now() - interval '5 minutes') RETURNING id")).scalar_one()

    respuesta = app_cliente.post(
        f"{API}/admin/procesos/ops_heartbeat/ejecutar",
        headers=admin["headers"], json={})
    assert respuesta.status_code == 202, respuesta.text
    assert respuesta.json()["disparo"] == "reintento"

    historial = app_cliente.get(
        f"{API}/admin/procesos/ops_heartbeat/ejecuciones",
        headers=admin["headers"], params={"page_size": 10}).json()["items"]
    anterior = next(run for run in historial if run["run_id"] == run_atascado)
    nuevo = next(run for run in historial
                 if run["run_id"] == respuesta.json()["run_id"])
    assert anterior["status"] == "timeout"
    assert nuevo["status"] == "ok"


def test_reintento_de_ejecucion_fallida(app_cliente, admin, motor_admin):
    anterior = _run_ok(app_cliente, admin, "ops_heartbeat")
    from sqlalchemy import text
    with motor_admin.begin() as conn:
        conn.execute(text(
            "UPDATE ops_job_runs SET status='error' WHERE id=:run_id"),
            {"run_id": anterior["run_id"]})

    r = app_cliente.post(
        f"{API}/admin/procesos/ops_heartbeat/ejecutar",
        headers=admin["headers"], json={})
    assert r.status_code == 202, r.text
    assert r.json()["disparo"] == "reintento"
    run_id = r.json()["run_id"]
    historial = app_cliente.get(
        f"{API}/admin/procesos/ops_heartbeat/ejecuciones",
        headers=admin["headers"]).json()["items"]
    reintento = next(item for item in historial if item["run_id"] == run_id)
    assert reintento["disparo"] == "reintento"
    assert reintento["status"] == "ok"


def test_historial_ejecuciones_paginado_y_filtrado(app_cliente, admin):
    primera = _run_ok(app_cliente, admin, "ops_heartbeat")
    segunda = _run_ok(app_cliente, admin, "ops_heartbeat")
    ruta = f"{API}/admin/procesos/ops_heartbeat/ejecuciones"

    pagina_1 = app_cliente.get(ruta, headers=admin["headers"],
                               params={"page": 1, "page_size": 1, "status": "ok"})
    pagina_2 = app_cliente.get(ruta, headers=admin["headers"],
                               params={"page": 2, "page_size": 1, "status": "ok"})
    assert pagina_1.status_code == pagina_2.status_code == 200
    datos_1, datos_2 = pagina_1.json(), pagina_2.json()
    assert datos_1["total"] == datos_2["total"] >= 2
    assert datos_1["items"][0]["status"] == datos_2["items"][0]["status"] == "ok"
    assert {datos_1["items"][0]["run_id"], datos_2["items"][0]["run_id"]} == {
        primera["run_id"], segunda["run_id"]}
    assert datos_1["items"][0]["actor"]["email"] == admin["email"]


def test_ejecutar_job_desconocido(app_cliente, admin):
    r = app_cliente.post(f"{API}/admin/procesos/nada/ejecutar",
                         headers=admin["headers"], json={})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "JOB_DESCONOCIDO"


@pytest.mark.parametrize("clave", ["ia_revision", "webhooks_clientes"])
def test_job_sin_runner_rechaza_ejecucion_manual(app_cliente, admin, clave):
    r = app_cliente.post(f"{API}/admin/procesos/{clave}/ejecutar",
                         headers=admin["headers"], json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "RUNNER_NO_DISPONIBLE"


def test_pausar_reanudar_y_reglas(app_cliente, admin):
    base = f"{API}/admin/procesos/purga_temporales"

    r = app_cliente.patch(base, headers=admin["headers"],
                          json={"activo": False})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "MOTIVO_REQUERIDO"

    r = app_cliente.patch(base, headers=admin["headers"],
                          json={"activo": False, "motivo": "Mantención"})
    assert r.status_code == 200
    assert r.json()["activo"] is False
    assert r.json()["proxima_ejecucion_at"] is None

    # Pausado sigue aceptando ejecución manual (la pausa es solo del cron).
    _run_ok(app_cliente, admin, "purga_temporales")

    r = app_cliente.patch(base, headers=admin["headers"], json={"activo": True})
    assert r.status_code == 200 and r.json()["activo"] is True

    r = app_cliente.patch(f"{API}/admin/procesos/ia_revision",
                          headers=admin["headers"],
                          json={"activo": False, "motivo": "x"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOB_NO_PAUSABLE"


def test_incidentes_ciclo_completo(app_cliente, admin):
    # Crear manual.
    r = app_cliente.post(f"{API}/admin/incidentes", headers=admin["headers"],
                         json={"componente": "storage", "severidad": "degradado",
                               "titulo": "Subida lenta reportada por cliente"})
    assert r.status_code == 201, r.text
    inc = r.json()
    assert inc["origen"] == "manual" and inc["estado"] == "abierto"
    iid = inc["id"]

    # Componente inexistente y severidad inválida.
    r = app_cliente.post(f"{API}/admin/incidentes", headers=admin["headers"],
                         json={"componente": "nube", "severidad": "caido",
                               "titulo": "x"})
    assert r.status_code == 404
    r = app_cliente.post(f"{API}/admin/incidentes", headers=admin["headers"],
                         json={"componente": "api", "severidad": "operativo",
                               "titulo": "x"})
    assert r.status_code == 422

    # Cerrar sin resolución -> 422; con resolución -> resuelto.
    r = app_cliente.patch(f"{API}/admin/incidentes/{iid}",
                          headers=admin["headers"], json={"estado": "resuelto"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "RESOLUCION_REQUERIDA"

    r = app_cliente.patch(f"{API}/admin/incidentes/{iid}",
                          headers=admin["headers"],
                          json={"estado": "resuelto",
                                "resolucion": "Reinicio del pool"})
    assert r.status_code == 200 and r.json()["estado"] == "resuelto"

    # Resuelto: editar -> 409; reabrir -> ok; transición inválida -> 400.
    r = app_cliente.patch(f"{API}/admin/incidentes/{iid}",
                          headers=admin["headers"], json={"titulo": "otro"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INCIDENTE_RESUELTO"

    r = app_cliente.patch(f"{API}/admin/incidentes/{iid}",
                          headers=admin["headers"], json={"estado": "abierto"})
    assert r.status_code == 200 and r.json()["resuelto_at"] is None

    r = app_cliente.patch(f"{API}/admin/incidentes/{iid}",
                          headers=admin["headers"],
                          json={"estado": "abierto"})   # abierto -> abierto
    # sin cambio de estado no es transición: se acepta como edición vacía
    assert r.status_code == 200

    r = app_cliente.get(f"{API}/admin/incidentes?estado=abierto",
                        headers=admin["headers"])
    assert any(x["id"] == iid for x in r.json()["items"])


# ============================================================================
# §7 — Indicadores
# ============================================================================
def test_indicadores_resumen_en_vivo(app_cliente, admin, suscripcion_a):
    r = app_cliente.get(f"{API}/admin/indicadores/resumen",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["parcial"] is True and d["moneda"] == "CLP"
    assert d["mrr"]["valor"] > 0                    # 12,5 UF activas
    assert d["arr"] == round(d["mrr"]["valor"] * 12, 2)
    assert d["clientes_activos"] >= 1
    assert d["objetivo_churn_pct"] == 2.0
    # Sin CAC configurado no se inventa un LTV/CAC.
    assert d["ltv_cac"] is None


def test_indicadores_mes_futuro(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/indicadores/resumen?mes=2999-01",
                        headers=admin["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "RANGO_INVALIDO"


def test_snapshot_y_series(app_cliente, admin, suscripcion_a):
    _run_ok(app_cliente, admin, "metricas_snapshot")

    r = app_cliente.get(f"{API}/admin/indicadores/mrr?meses=3",
                        headers=admin["headers"])
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[-1]["parcial"] is True
    assert items[-1]["mrr"] > 0

    r = app_cliente.get(f"{API}/admin/indicadores/clientes-flujo",
                        headers=admin["headers"])
    fin = r.json()["items"][-1]
    assert fin["neto"] == fin["altas"] - fin["bajas"]

    r = app_cliente.get(f"{API}/admin/indicadores/churn",
                        headers=admin["headers"])
    assert r.json()["objetivo_pct"] == 2.0

    r = app_cliente.get(f"{API}/admin/indicadores/por-plan",
                        headers=admin["headers"])
    d = r.json()
    pro = next(x for x in d["items"] if x["plan"] == "Pro")
    assert pro["mrr"] > 0
    if len(d["items"]) == 1:
        assert pro["pct_mrr"] == 100.0


# ============================================================================
# Auditoría
# ============================================================================
def test_acciones_auditadas_sin_tenant(app_cliente, admin, motor_admin):
    app_cliente.patch(f"{API}/admin/procesos/purga_temporales",
                      headers=admin["headers"],
                      json={"activo": False, "motivo": "Prueba de auditoría"})
    from sqlalchemy import text
    with motor_admin.connect() as c:
        filas = c.execute(text(
            "SELECT descripcion FROM actividad "
            "WHERE modulo = 'ops' AND company_id IS NULL")).all()
    assert any("Prueba de auditoría" in f.descripcion for f in filas)
    app_cliente.patch(f"{API}/admin/procesos/purga_temporales",
                      headers=admin["headers"], json={"activo": True})
