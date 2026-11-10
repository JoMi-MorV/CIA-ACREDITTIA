"""Regresion de categorias y acceso del buscador global (RF-BUS-01)."""
import pytest

from tests.conftest import API, CLAVE, patente_valida, rut_valido


def concesion_sensible(app_cliente, admin, categoria, empresa=None, recurso_id=None):
    cuerpo = {
        "admin_user_id": admin["user_id"],
        "recurso_tipo": categoria,
        "motivo": f"Validar permisos de {categoria} en pruebas",
        "horas": 1,
    }
    if empresa:
        cuerpo["company_id"] = empresa["company_id"]
    if recurso_id:
        cuerpo["recurso_id"] = recurso_id
    respuesta = app_cliente.post(
        f"{API}/admin/access-grants", headers=admin["headers"], json=cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    headers = dict(admin["headers"])
    headers["X-Access-Grant"] = respuesta.json()["id"]
    return headers


def segundo_admin(app_cliente):
    from app.database import worker_session
    from app.models import User
    from app.security import hash_password

    email = "segundo-admin@acredittia.cl"
    with worker_session(is_admin=True) as db:
        db.add(User(email=email, nombre="Segundo Admin",
                    password_hash=hash_password(CLAVE), role="admin",
                    company_id=None, status="approved"))
        db.commit()
    respuesta = app_cliente.post(
        f"{API}/auth/login", json={"email": email, "password": CLAVE})
    assert respuesta.status_code == 200, respuesta.text
    return {"user_id": respuesta.json()["user"]["id"],
            "headers": {"Authorization":
                        f"Bearer {respuesta.json()['access_token']}"}}


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
    assert "query" not in respuesta.json()
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
        trabajadores = [item for item in items if item["tipo"] == "trabajador"]
        equipos = [item for item in items if item["tipo"] == "equipo"]
        assert len(trabajadores) == min(limite, len(esperados))
        assert equipo.json()["id"] in {item["id"] for item in equipos}
        for item in trabajadores:
            empresa = esperados[item["id"]]
            assert item["tipo"] == "trabajador"
            assert item["company_id"] == empresa["company_id"]
            assert item["empresa"] == empresa["nombre"]
            assert item["detalle"] == f"/admin/companies/{empresa['company_id']}"
        if limite == 25:
            assert {item["id"] for item in trabajadores} == set(esperados)


def test_busqueda_equipos_por_patente_y_atributos(
        app_cliente, admin, empresa_a, contrato_a):
    respuesta_equipo = app_cliente.post(
        f"{API}/equipos", headers=empresa_a["headers"], json={
            "contrato_id": contrato_a["id"], "patente": patente_valida(83),
            "tipo_equipo": "Camión", "marca": "MarcaBusqueda",
            "modelo": "ModeloBusqueda",
        })
    assert respuesta_equipo.status_code == 201, respuesta_equipo.text
    equipo_id = respuesta_equipo.json()["id"]

    for termino in (respuesta_equipo.json()["patente"], "Camión",
                    "MarcaBusqueda", "ModeloBusqueda",
                    respuesta_equipo.json()["nombre"]):
        respuesta = app_cliente.get(
            f"{API}/admin/search", headers=admin["headers"],
            params={"q": termino})
        assert respuesta.status_code == 200, respuesta.text
        equipo = next(item for item in respuesta.json()["items"]
                      if item["id"] == equipo_id)
        assert equipo["tipo"] == "equipo"
        assert equipo["company_id"] == empresa_a["company_id"]
        assert equipo["empresa"] == empresa_a["nombre"]
        assert respuesta_equipo.json()["patente"] in equipo["subtitulo"]
        assert "rut" not in equipo


def test_busqueda_equipos_combina_terminos_entre_marca_y_patente(
        app_cliente, admin, empresa_a, contrato_a, motor_admin):
    from sqlalchemy import text

    alta = app_cliente.post(f"{API}/equipos", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "patente": patente_valida(89),
        "tipo_equipo": "Camión", "marca": "Toyota", "modelo": "Hilux",
    })
    assert alta.status_code == 201, alta.text
    prefijo_patente = alta.json()["patente"][:4]
    with motor_admin.begin() as conexion:
        conexion.execute(
            text("UPDATE companies SET nombre = 'Aseo Transporte' WHERE id = :id"),
            {"id": empresa_a["company_id"]})

    respuesta = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": f"toy {prefijo_patente.lower()} cam aseo",
                "tipo": "equipo"})

    assert respuesta.status_code == 200, respuesta.text
    assert [item["id"] for item in respuesta.json()["items"]] == [alta.json()["id"]]


def test_busqueda_filtra_categoria_y_encuentra_persona_por_rut(
        app_cliente, admin, empresa_a, contrato_a):
    rut = rut_valido(84)
    alta = app_cliente.post(f"{API}/personal", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "nombre": "Persona por RUT",
        "rut": rut,
    })
    assert alta.status_code == 201, alta.text

    respuesta = app_cliente.get(
        f"{API}/admin/search",
        headers=concesion_sensible(app_cliente, admin, "personal", empresa_a),
        params={"q": rut, "tipo": "trabajador"})
    assert respuesta.status_code == 200, respuesta.text
    assert [item["tipo"] for item in respuesta.json()["items"]] == ["trabajador"]
    assert respuesta.json()["items"][0]["id"] == alta.json()["id"]
    salida = str(respuesta.json()).lower()
    assert "query" not in respuesta.json()
    assert rut not in salida
    assert "password" not in salida
    assert "token" not in salida

    invalida = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": rut, "tipo": "desconocido"})
    assert invalida.status_code == 400
    assert invalida.json()["error"]["code"] == "TIPO_INVALIDO"


def test_busqueda_usuario_por_rut_sin_exponerlo_en_resultado(
        app_cliente, admin, empresa_a):
    respuesta = app_cliente.get(
        f"{API}/admin/search",
        headers=concesion_sensible(app_cliente, admin, "usuario", empresa_a),
        params={"q": empresa_a["email"], "tipo": "usuario"})
    assert respuesta.status_code == 200, respuesta.text
    usuario = next(item for item in respuesta.json()["items"]
                   if item["id"] == empresa_a["user_id"])
    assert usuario["tipo"] == "usuario"
    salida = str(respuesta.json()).lower()
    assert "query" not in respuesta.json()
    assert "rut" not in usuario
    assert empresa_a["rut"] not in salida
    assert "password" not in salida
    assert "token" not in salida


def test_busqueda_aplica_filtros_especificos_en_servidor(
        app_cliente, admin, empresa_a, contrato_a):
    rut = rut_valido(86)
    persona = app_cliente.post(f"{API}/personal", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "nombre": "Conductora Filtro",
        "rut": rut, "cargo": "OperadoraFiltro", "es_conductor": True,
    })
    assert persona.status_code == 201, persona.text

    respuesta = app_cliente.get(f"{API}/admin/search",
                                headers=concesion_sensible(
                                    app_cliente, admin, "personal", empresa_a),
                                params={"q": "Conductora", "tipo": "trabajador",
                                        "cargo": "OperadoraFiltro",
                                        "empresa": empresa_a["nombre"],
                                        "conductor": "true"})
    assert respuesta.status_code == 200, respuesta.text
    assert [item["id"] for item in respuesta.json()["items"]] == [persona.json()["id"]]

    con_busqueda_vacia = app_cliente.get(
        f"{API}/admin/search",
        headers=concesion_sensible(app_cliente, admin, "personal", empresa_a),
        params={"tipo": "trabajador", "cargo": "OperadoraFiltro"})
    assert con_busqueda_vacia.status_code == 200, con_busqueda_vacia.text
    assert [item["id"] for item in con_busqueda_vacia.json()["items"]] == [persona.json()["id"]]

    sin_conductor = app_cliente.get(
        f"{API}/admin/search",
        headers=concesion_sensible(app_cliente, admin, "personal", empresa_a),
        params={"q": "Conductora", "tipo": "trabajador", "conductor": "false"})
    assert all(item["id"] != persona.json()["id"]
               for item in sin_conductor.json()["items"])


def test_busqueda_filtra_equipos_por_detalle(
        app_cliente, admin, empresa_a, contrato_a):
    alta = app_cliente.post(f"{API}/equipos", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "patente": patente_valida(87),
        "tipo_equipo": "Camión", "marca": "FiltroMarca",
        "modelo": "FiltroModelo", "anio": 2020,
    })
    assert alta.status_code == 201, alta.text

    respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"],
                                params={"q": "Camión", "tipo": "equipo",
                                        "empresa": empresa_a["nombre"],
                                        "patente": alta.json()["patente"],
                                        "marca": "FiltroMarca",
                                        "modelo": "FiltroModelo", "anio": 2020})
    assert respuesta.status_code == 200, respuesta.text
    assert [item["id"] for item in respuesta.json()["items"]] == [alta.json()["id"]]

    filtrada_sin_texto = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"tipo": "equipo", "tipo_equipo": "Camión",
                "marca": "FiltroMarca", "anio": 2020})
    assert filtrada_sin_texto.status_code == 200, filtrada_sin_texto.text
    assert [item["id"] for item in filtrada_sin_texto.json()["items"]] == [alta.json()["id"]]


def test_busqueda_vacia_sin_filtros_se_rechaza(app_cliente, admin):
    respuesta = app_cliente.get(f"{API}/admin/search", headers=admin["headers"])
    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "BUSQUEDA_INVALIDA"


def test_catalogos_de_filtros_globales(app_cliente, admin, empresa_a,
                                      contrato_a):
    personal = app_cliente.post(f"{API}/personal", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "nombre": "Persona catálogo",
        "rut": rut_valido(88), "cargo": "CargoCatalogoFiltro",
    })
    assert personal.status_code == 201, personal.text
    equipo = app_cliente.post(f"{API}/equipos", headers=empresa_a["headers"], json={
        "contrato_id": contrato_a["id"], "patente": patente_valida(88),
        "tipo_equipo": "Camión", "marca": "MarcaCatalogoFiltro",
        "modelo": "Modelo catálogo",
    })
    assert equipo.status_code == 201, equipo.text
    respuesta = app_cliente.get(f"{API}/admin/search/catalogos",
                                headers=admin["headers"])
    assert respuesta.status_code == 200, respuesta.text
    catalogos = respuesta.json()
    assert set(catalogos) == {
        "empresas", "contratos", "cargos", "tipos_equipo", "marcas", "hay_mas"}
    assert empresa_a["nombre"] in catalogos["empresas"]
    assert contrato_a["nombre"] in catalogos["contratos"]
    assert "CargoCatalogoFiltro" in catalogos["cargos"]
    assert "Camión" in catalogos["tipos_equipo"]
    assert "MarcaCatalogoFiltro" in catalogos["marcas"]
    assert catalogos["hay_mas"] == {
        "empresas": False, "contratos": False, "cargos": False, "marcas": False}
    assert all(isinstance(valores, list) for clave, valores in catalogos.items()
               if clave != "hay_mas")
    assert "alfa@empresa.cl" not in str(catalogos)
    assert empresa_a["rut"] not in str(catalogos)


def test_busqueda_filtra_empresas_contratos_y_usuarios(
        app_cliente, admin, empresa_a, contrato_a, motor_admin):
    from sqlalchemy import text
    with motor_admin.begin() as conexion:
        conexion.execute(text(
            "UPDATE companies SET nombre = 'EmpresaFiltroGlobal', "
            "status = 'approved', es_demo = false WHERE id = :id"),
            {"id": empresa_a["company_id"]})
        conexion.execute(text(
            "UPDATE contratos SET nombre = 'ContratoFiltroGlobal', estado = 'vigente' "
            "WHERE id = :id"), {"id": contrato_a["id"]})
        conexion.execute(text(
            "UPDATE users SET nombre = 'UsuarioFiltroGlobal', status = 'approved' "
            "WHERE id = :id"), {"id": empresa_a["user_id"]})

    empresa = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": "EmpresaFiltroGlobal", "tipo": "empresa",
                "estado": "approved", "es_demo": "false"})
    assert [item["id"] for item in empresa.json()["items"]] == [empresa_a["company_id"]]

    empresa_por_rut = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": empresa_a["rut"], "tipo": "empresa"})
    assert empresa_por_rut.status_code == 200, empresa_por_rut.text
    assert [item["id"] for item in empresa_por_rut.json()["items"]] == [
        empresa_a["company_id"]]
    assert empresa_a["rut"] not in str(empresa_por_rut.json())

    contrato = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": "ContratoFiltroGlobal", "tipo": "contrato",
                "empresa": "EmpresaFiltroGlobal", "estado": "vigente"})
    assert [item["id"] for item in contrato.json()["items"]] == [contrato_a["id"]]

    usuario = app_cliente.get(
        f"{API}/admin/search",
        headers=concesion_sensible(app_cliente, admin, "usuario", empresa_a),
        params={"q": "UsuarioFiltroGlobal", "tipo": "usuario",
                "empresa": "EmpresaFiltroGlobal", "rol": "company",
                "estado": "approved"})
    assert [item["id"] for item in usuario.json()["items"]] == [empresa_a["user_id"]]


def test_busqueda_rechaza_empresa_y_sin_sesion(app_cliente, empresa_a):
    for headers, estado in [({}, 401), (empresa_a["headers"], 403)]:
        respuesta = app_cliente.get(f"{API}/admin/search", headers=headers,
                                     params={"q": "Transportes"})
        assert respuesta.status_code == estado
        assert "items" not in respuesta.json()


@pytest.mark.parametrize("categoria", ["trabajador", "usuario"])
def test_busqueda_sensible_exige_concesion(app_cliente, admin, categoria):
    respuesta = app_cliente.get(
        f"{API}/admin/search", headers=admin["headers"],
        params={"q": "Persona", "tipo": categoria})

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "PERMISO_INFORMACION_REQUERIDO"


def test_busqueda_concesion_limited_to_company_and_resource(
        app_cliente, admin, empresa_a, empresa_b, contrato_a, contrato_b):
    personas = []
    for empresa, contrato, rut_num in (
            (empresa_a, contrato_a, 91), (empresa_b, contrato_b, 92)):
        respuesta = app_cliente.post(
            f"{API}/personal", headers=empresa["headers"], json={
                "contrato_id": contrato["id"],
                "nombre": "AlcanceBuscadorPrueba",
                "rut": rut_valido(rut_num),
            })
        assert respuesta.status_code == 201, respuesta.text
        personas.append((empresa, respuesta.json()["id"]))

    headers = concesion_sensible(
        app_cliente, admin, "personal", empresa_a, personas[0][1])
    respuesta = app_cliente.get(
        f"{API}/admin/search", headers=headers,
        params={"q": "AlcanceBuscadorPrueba", "tipo": "trabajador"})

    assert respuesta.status_code == 200, respuesta.text
    assert [item["id"] for item in respuesta.json()["items"]] == [personas[0][1]]
    assert personas[1][1] not in {
        item["id"] for item in respuesta.json()["items"]}


def test_busqueda_rechaza_concesion_ajena_expirada_revocada_y_de_otra_categoria(
        app_cliente, admin, empresa_a, motor_admin):
    from sqlalchemy import text

    otro = segundo_admin(app_cliente)
    headers = concesion_sensible(app_cliente, admin, "personal", empresa_a)
    grant_id = headers["X-Access-Grant"]
    consulta = {"q": "persona", "tipo": "trabajador"}

    ajena = app_cliente.get(
        f"{API}/admin/search",
        headers={**otro["headers"], "X-Access-Grant": grant_id},
        params=consulta)
    assert ajena.status_code == 403
    assert ajena.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"
    assert "items" not in ajena.json()

    with motor_admin.begin() as conexion:
        conexion.execute(text(
            "UPDATE admin_access_grants "
            "SET expires_at = now() - interval '1 minute' WHERE id = :id"),
            {"id": grant_id})
    expirada = app_cliente.get(
        f"{API}/admin/search", headers=headers, params=consulta)
    assert expirada.status_code == 403
    assert expirada.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"

    revocable = concesion_sensible(app_cliente, admin, "personal", empresa_a)
    grant_revocable = revocable["X-Access-Grant"]
    revocada = app_cliente.post(
        f"{API}/admin/access-grants/{grant_revocable}/revoke",
        headers=admin["headers"])
    assert revocada.status_code == 200, revocada.text
    respuesta_revocada = app_cliente.get(
        f"{API}/admin/search", headers=revocable, params=consulta)
    assert respuesta_revocada.status_code == 403
    assert respuesta_revocada.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"

    categoria_incorrecta = concesion_sensible(
        app_cliente, admin, "personal", empresa_a)
    usuario = app_cliente.get(
        f"{API}/admin/search",
        headers=categoria_incorrecta,
        params={"q": "alfa", "tipo": "usuario"})
    assert usuario.status_code == 403
    assert usuario.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"


def test_detalle_empresa_redacta_usuarios_y_aplica_alcance_de_concesion(
        app_cliente, admin, empresa_a, empresa_b):
    ruta = f"{API}/admin/companies/{empresa_a['company_id']}"
    sin_concesion = app_cliente.get(ruta, headers=admin["headers"])
    assert sin_concesion.status_code == 200, sin_concesion.text
    detalle = sin_concesion.json()
    serializado = str(detalle)
    assert detalle["datos_usuarios_restringidos"] is True
    assert detalle["cuentas"] == []
    assert all(not contrato["responsables"]
               for contrato in detalle["contratos"])
    assert empresa_a["email"] not in serializado

    grant_usuario = concesion_sensible(
        app_cliente, admin, "usuario", empresa_a)
    con_concesion = app_cliente.get(ruta, headers=grant_usuario)
    assert con_concesion.status_code == 200, con_concesion.text
    detalle_autorizado = con_concesion.json()
    assert detalle_autorizado["datos_usuarios_restringidos"] is False
    assert any(cuenta["id"] == empresa_a["user_id"]
               for cuenta in detalle_autorizado["cuentas"])
    salida = str(detalle_autorizado)
    assert "password" not in salida.lower()
    assert "token" not in salida.lower()
    assert empresa_a["rut"] not in salida

    grant_otra_empresa = concesion_sensible(
        app_cliente, admin, "usuario", empresa_b)
    fuera_de_alcance = app_cliente.get(ruta, headers=grant_otra_empresa)
    assert fuera_de_alcance.status_code == 200, fuera_de_alcance.text
    detalle_fuera_de_alcance = fuera_de_alcance.json()
    assert detalle_fuera_de_alcance["datos_usuarios_restringidos"] is True
    assert detalle_fuera_de_alcance["cuentas"] == []
    assert empresa_a["email"] not in str(detalle_fuera_de_alcance)


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
        headers = (concesion_sensible(app_cliente, admin, "usuario")
                   if categoria == "usuario" else admin["headers"])
        respuesta = app_cliente.get(f"{API}/admin/search", headers=headers,
                                     params={"q": "RecorteBusqueda", "limite": limite,
                                             "tipo": categoria})
        assert respuesta.status_code == 200, respuesta.text
        datos = respuesta.json()
        assert datos["hay_mas"] is (limite == 1)
        assert datos["limite_por_categoria"] == limite
        assert datos["total"] == min(limite, 2)
        assert [item["id"] for item in datos["items"]] == ids[:limite]
        assert all(item["tipo"] == categoria for item in datos["items"])
