from tests.conftest import API


def test_admin_identifica_cuentas_por_correo(app_cliente, admin, empresa_a):
    for cuenta in (admin, empresa_a):
        respuesta = app_cliente.get(
            f"{API}/admin/users", headers=admin["headers"],
            params={"search": cuenta["email"]})
        assert respuesta.status_code == 200, respuesta.text
        usuarios = respuesta.json()["items"]
        assert len(usuarios) == 1
        assert usuarios[0]["id"] == cuenta["user_id"]
        assert usuarios[0]["email"] == cuenta["email"]
        assert "password_hash" not in usuarios[0]
        assert "auth_version" not in usuarios[0]


def test_identidad_administrativa_restringida(app_cliente, empresa_a):
    ruta = f"{API}/admin/users"
    assert app_cliente.get(ruta, headers=empresa_a["headers"]).status_code == 403
    assert app_cliente.get(ruta).status_code == 401


def test_cambio_de_alcance_exige_motivo(app_cliente, admin, empresa_a,
                                         contrato_a):
    respuesta = app_cliente.patch(
        f"{API}/admin/users/{empresa_a['user_id']}",
        headers=admin["headers"],
        json={
            "role": "contract_admin",
            "company_id": empresa_a["company_id"],
            "contrato_id": contrato_a["id"],
        },
    )
    assert respuesta.status_code == 400
    assert respuesta.json()["error"]["code"] == "MOTIVO_REQUERIDO"

    listado = app_cliente.get(
        f"{API}/admin/users", headers=admin["headers"],
        params={"search": empresa_a["email"]})
    assert listado.json()["items"][0]["role"] == "company"


def test_cambio_de_alcance_guarda_motivo_y_valores_en_auditoria(
        app_cliente, admin, empresa_a, empresa_b, contrato_b):
    motivo = "Cambio aprobado por reasignación de cuenta"
    respuesta = app_cliente.patch(
        f"{API}/admin/users/{empresa_a['user_id']}",
        headers=admin["headers"],
        json={
            "role": "contract_admin",
            "company_id": empresa_b["company_id"],
            "contrato_id": contrato_b["id"],
            "motivo": motivo,
        },
    )
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["role"] == "contract_admin"
    assert respuesta.json()["company_id"] == empresa_b["company_id"]
    assert respuesta.json()["contrato_id"] == contrato_b["id"]
    sesion_anterior = app_cliente.get(
        f"{API}/auth/me", headers=empresa_a["headers"])
    assert sesion_anterior.status_code == 401, sesion_anterior.text

    audit = app_cliente.get(
        f"{API}/admin/users/audit", headers=admin["headers"],
        params={"page_size": 25})
    assert audit.status_code == 200, audit.text
    entry = next(item for item in audit.json()["items"]
                 if item["usuario_id"] == empresa_a["user_id"])
    assert entry["motivo"] == motivo
    assert entry["cambios"]["role"] == {
        "antes": "company", "despues": "contract_admin"}
    assert entry["cambios"]["company_id"] == {
        "antes": empresa_a["company_id"], "despues": empresa_b["company_id"]}
    assert entry["cambios"]["contrato_id"] == {
        "antes": None, "despues": contrato_b["id"]}
