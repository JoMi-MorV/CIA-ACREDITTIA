import pytest

from tests.conftest import API, CLAVE


@pytest.mark.parametrize("via", ["revoke", "patch"])
def test_revocar_reactivar_no_recupera_sesiones(app_cliente, admin, empresa_a, via):
    ruta = f"{API}/admin/users/{empresa_a['user_id']}"
    assert app_cliente.get(f"{API}/auth/me", headers=empresa_a["headers"]).status_code == 200
    if via == "revoke":
        respuesta = app_cliente.post(ruta + "/revoke", headers=admin["headers"], json={})
    else:
        respuesta = app_cliente.patch(ruta, headers=admin["headers"], json={"activo": False})
    assert respuesta.status_code == 200, respuesta.text
    assert app_cliente.get(f"{API}/auth/me", headers=empresa_a["headers"]).status_code == 401
    respuesta = app_cliente.patch(ruta, headers=admin["headers"], json={"activo": True})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["activo"] is True
    assert respuesta.json()["company_id"] == empresa_a["company_id"]
    assert respuesta.json()["role"] == "company"
    assert app_cliente.get(f"{API}/auth/me", headers=empresa_a["headers"]).status_code == 401
    assert app_cliente.post(f"{API}/auth/refresh", json={
        "refresh_token": empresa_a["refresh_token"]}).status_code == 401
    login = app_cliente.post(f"{API}/auth/login", json={"email": empresa_a["email"], "password": CLAVE})
    assert login.status_code == 200, login.text
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert app_cliente.get(f"{API}/auth/me", headers=headers).status_code == 200
    assert app_cliente.post(f"{API}/auth/refresh", json={
        "refresh_token": login.json()["refresh_token"]}).status_code == 200


def test_empresa_no_puede_reactivarse(app_cliente, admin, empresa_a):
    ruta = f"{API}/admin/users/{empresa_a['user_id']}"
    respuesta = app_cliente.patch(ruta, headers=empresa_a["headers"], json={"activo": True})
    assert respuesta.status_code == 403
    assert app_cliente.patch(ruta, json={"activo": True}).status_code == 401
