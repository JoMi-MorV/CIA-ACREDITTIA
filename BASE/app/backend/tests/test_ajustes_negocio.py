from datetime import date, timedelta

import sqlalchemy as sa

from tests.conftest import API


def _ajustes(cambio=None):
    valores = {
        "valor_uf": 39500.5,
        "uf_vigente_desde": date.today().isoformat(),
        "uf_fuente": "Fuente de prueba",
        "cac_clp": 125000,
        "margen_bruto_pct": 75,
        "objetivo_churn_pct": 3.5,
        "motivo": "Actualización de valores de prueba",
    }
    if cambio:
        valores.update(cambio)
    return valores


def test_ajustes_negocio_solo_admin_y_persistencia(
        app_cliente, admin, empresa_a, motor_admin):
    ruta = f"{API}/admin/ajustes-negocio"
    inicial = app_cliente.get(ruta, headers=admin["headers"])
    assert inicial.status_code == 200, inicial.text
    assert inicial.json()["valor_uf"] == 39000

    denegado = app_cliente.patch(
        ruta, headers=empresa_a["headers"], json=_ajustes())
    assert denegado.status_code == 403

    guardado = app_cliente.patch(
        ruta, headers=admin["headers"], json=_ajustes())
    assert guardado.status_code == 200, guardado.text
    assert guardado.json()["valor_uf"] == 39500.5
    assert guardado.json()["cac_clp"] == 125000
    assert guardado.json()["updated_by"] == admin["user_id"]

    lectura = app_cliente.get(ruta, headers=admin["headers"])
    assert lectura.status_code == 200, lectura.text
    assert lectura.json()["margen_bruto_pct"] == 75
    assert lectura.json()["objetivo_churn_pct"] == 3.5
    churn = app_cliente.get(
        f"{API}/admin/indicadores/churn", headers=admin["headers"])
    assert churn.status_code == 200, churn.text
    assert churn.json()["objetivo_pct"] == 3.5
    with motor_admin.connect() as conn:
        evento = conn.execute(
            sa.text(
                "SELECT descripcion FROM actividad "
                "WHERE entidad_tipo = 'ops_ajustes_negocio' "
                "ORDER BY created_at DESC LIMIT 1")).scalar_one()
    assert "antes=" in evento and "despues=" in evento
    assert "Actualización de valores de prueba" in evento


def test_ajustes_negocio_valida_motivo_fuente_y_vigencia(
        app_cliente, admin):
    ruta = f"{API}/admin/ajustes-negocio"
    for cambio in (
        {"motivo": "corto"},
        {"uf_fuente": "   "},
        {"uf_vigente_desde": (date.today() + timedelta(days=1)).isoformat()},
        {"valor_uf": 0},
        {"margen_bruto_pct": 101},
        {"objetivo_churn_pct": -1},
    ):
        respuesta = app_cliente.patch(
            ruta, headers=admin["headers"], json=_ajustes(cambio))
        assert respuesta.status_code == 422, respuesta.text
