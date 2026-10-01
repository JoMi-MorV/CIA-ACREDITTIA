"""Regresion de categorias y acceso del buscador global (RF-BUS-01)."""
import pytest

from tests.conftest import API, patente_valida, rut_valido


@pytest.mark.parametrize("consulta", [None, "", "a", "  ", " a ", "\t\n", "x" * 101])
def test_busqueda_rechaza_consulta_invalida(app_cliente, admin, consulta):
    params = {} if consulta is None else {"q": consulta}
    respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"],
                                 params=params)
    assert respuesta.status_code == 422, respuesta.text
    assert "items" not in respuesta.json()


@pytest.mark.parametrize("consulta", ["Al", "  Alfa  ", "x" * 100])
def test_busqueda_acepta_limites_y_normaliza(app_cliente, admin, empresa_a, consulta):
    respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"],
                                 params={"q": consulta})
    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["query"] == consulta.strip()
    assert respuesta.json()["hay_mas"] is False
    assert respuesta.json()["total"] == len(respuesta.json()["items"])
    empresas = [item for item in respuesta.json()["items"] if item["tipo"] == "empresa"]
    assert {item["id"] for item in empresas} == (
        set() if len(consulta) == 100 else {empresa_a["company_id"]})


@pytest.mark.parametrize("campo", ["nombre", "cargo"])
def test_busqueda_solo_trabajadores_por_nombre_o_cargo(
        app_cliente, admin, empresa_a, empresa_b, contrato_a, contrato_b, campo):
    termino = "CoincidenciaBusqueda"
    # El equipo coincide por nombre y se crea antes que los trabajadores.
    equipo = app_cliente.post(f"{API}/equipos", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "patente": patente_valida(81),
        "tipo_equipo": "Camión", "marca": termino, "modelo": "Equipo"})
    assert equipo.status_code == 201, equipo.text
    esperados = {}
    for n, empresa, contrato in [(81, empresa_a, contrato_a), (82, empresa_b, contrato_b)]:
        cuerpo = {"contrato_id": contrato["id"], "nombre": "Persona de prueba",
                  "rut": rut_valido(n), campo: termino}
        respuesta = app_cliente.post(f"{API}/personal", headers=empresa["headers"],
                                     json=cuerpo)
        assert respuesta.status_code == 201, respuesta.text
        esperados[respuesta.json()["id"]] = empresa

    for limite in (1, 2, 25):
        respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"],
                                     params={"q": termino.lower(), "limite": limite})
        assert respuesta.status_code == 200, respuesta.text
        items = respuesta.json()["items"]
        assert respuesta.json()["limite_por_categoria"] == limite
        assert respuesta.json()["hay_mas"] is (limite < len(esperados))
        assert len(items) == min(limite, len(esperados))
        assert equipo.json()["id"] not in {item["id"] for item in items}
        for item in items:
            empresa = esperados[item["id"]]
            assert item["tipo"] == "trabajador"
            assert item["company_id"] == empresa["company_id"]
            assert item["empresa"] == empresa["nombre"]
            assert item["detalle"] == f"/admin/companies/{empresa['company_id']}"
        if limite == 25:
            assert {item["id"] for item in items} == set(esperados)


def test_busqueda_rechaza_empresa_y_sin_sesion(app_cliente, empresa_a):
    for headers, estado in [({}, 401), (empresa_a["headers"], 403)]:
        respuesta = app_cliente.get(f"{API}/admin/search", headers=headers,
                                     params={"q": "Transportes"})
        assert respuesta.status_code == estado
        assert "items" not in respuesta.json()


@pytest.mark.parametrize("tabla,categoria", [
    ("companies", "empresa"), ("contratos", "contrato"), ("users", "usuario")])
def test_busqueda_informa_recorte_por_categoria(
        app_cliente, admin, empresa_a, empresa_b, contrato_a, contrato_b,
        motor_admin, tabla, categoria):
    from sqlalchemy import text
    ids = {
        "companies": [empresa_a["company_id"], empresa_b["company_id"]],
        "contratos": [contrato_a["id"], contrato_b["id"]],
        "users": [empresa_a["user_id"], empresa_b["user_id"]],
    }[tabla]
    # Tablas constantes del parametrizado; datos exclusivamente del fixture.
    with motor_admin.begin() as conexion:
        for numero, identificador in enumerate(ids):
            conexion.execute(text(f"UPDATE {tabla} SET nombre = :nombre WHERE id = :id"),
                             {"nombre": f"RecorteBusqueda {numero}", "id": identificador})
    for limite in (1, 2, 25):
        respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"],
                                     params={"q": "RecorteBusqueda", "limite": limite})
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["hay_mas"] is (limite == 1)
        assert datos["limite_por_categoria"] == limite
        assert datos["total"] == min(limite, 2)
        assert [item["id"] for item in datos["items"]] == ids[:limite]
        assert all(item["tipo"] == categoria for item in datos["items"])
