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
