from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from zipfile import ZipFile

import sqlalchemy as sa

from app.services import business_exports
from tests.conftest import API, patente_valida, rut_valido, subir_archivo


def _export_body(company_id, *, scope="empresa", resource_id=None,
                 categories=None):
    return {
        "alcance": scope,
        "company_id": company_id,
        "recurso_id": resource_id,
        "categorias": categories or [
            "empresa", "contratos", "personas_equipos", "documentos",
            "alertas", "actividad", "requisitos", "plataformas",
            "cumplimiento", "calendario",
        ],
        "motivo": "Exportación solicitada para validación",
    }


def _csv_rows(archive, path):
    content = archive.read(path).decode("utf-8-sig")
    return list(csv.DictReader(io.StringIO(content)))


def _documento_de_contrato(app_cliente, empresa, contrato):
    response = app_cliente.get(
        f"{API}/contratos/{contrato['id']}/documentos",
        headers=empresa["headers"])
    assert response.status_code == 200, response.text
    return response.json()["items"][0]


def _crear_persona_y_equipo(app_cliente, empresa, contrato):
    response = app_cliente.post(
        f"{API}/personal", headers=empresa["headers"],
        json={"contrato_id": contrato["id"], "nombre": "Persona Exportación",
              "rut": rut_valido(11), "cargo": "Conductor", "es_conductor": True})
    assert response.status_code == 201, response.text
    person_id = response.json()["id"]
    response = app_cliente.post(
        f"{API}/equipos", headers=empresa["headers"],
        json={"contrato_id": contrato["id"], "patente": patente_valida(3),
              "tipo_equipo": "Camión", "marca": "Volvo"})
    assert response.status_code == 201, response.text
    return {"trabajador": person_id, "equipo": response.json()["id"]}


def test_exporta_empresa_con_archivos_saneados_y_auditoria(
        app_cliente, admin, empresa_a, contrato_a, monkeypatch, motor_admin):
    documento = _documento_de_contrato(app_cliente, empresa_a, contrato_a)
    subir_archivo(
        app_cliente, empresa_a, documento["id"],
        filename="../../acta de prueba.pdf",
        contenido=b"%PDF-1.4 contenido exportable")
    temporales = []
    original_temporary_directory = business_exports.tempfile.TemporaryDirectory

    def create_temporary_directory(*args, **kwargs):
        temporary = original_temporary_directory(*args, **kwargs)
        temporales.append(Path(temporary.name))
        return temporary

    monkeypatch.setattr(
        business_exports.tempfile, "TemporaryDirectory",
        create_temporary_directory)
    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(empresa_a["company_id"]),
    )

    if response.status_code != 200:
        with motor_admin.connect() as connection:
            failure = connection.execute(sa.text(
                'SELECT "metadata" FROM actividad '
                "WHERE entidad_tipo = 'exportacion_datos' "
                "ORDER BY id DESC LIMIT 1")).scalar_one()
        raise AssertionError(f"{response.text}; audit={failure}")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-content-type-options"] == "nosniff"
    with ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        manifest = json.loads(archive.read("manifest.json"))
        documents = _csv_rows(archive, "datos/documento_archivos.csv")
        users = _csv_rows(archive, "datos/users.csv")
        archive_path = documents[0]["ruta_archivo"]
        assert archive_path.startswith("archivos/contrato/")
        assert "../" not in archive_path
        assert archive_path.endswith("acta de prueba.pdf")
        assert archive.read(archive_path) == b"%PDF-1.4 contenido exportable"
        assert "blob_path" not in documents[0]
        assert "password_hash" not in users[0]
        assert "auth_version" not in users[0]
        assert "datos/contratos.csv" in names
        assert "plataforma_credenciales" not in " ".join(names)
        assert manifest["alcance"] == "empresa"
        assert manifest["archivos_incluidos"] == 1

    with motor_admin.connect() as connection:
        grant = connection.execute(sa.text(
            "SELECT id, revoked_at FROM admin_access_grants "
            "WHERE recurso_tipo = 'exportacion_datos_empresa' "
            "ORDER BY created_at DESC LIMIT 1")).one()
        events = connection.execute(sa.text(
            'SELECT "metadata" FROM actividad '
            "WHERE entidad_tipo = 'exportacion_datos' AND entidad_id = :id "
            "ORDER BY id"), {"id": grant.id}).scalars().all()
    assert grant.revoked_at is not None
    assert len(temporales) == 1
    assert not temporales[0].exists()
    results = [event["resultado"] for event in events]
    assert results == [
        "solicitada", "generacion_completada", "respuesta_http_completada",
    ]
    assert all(event["motivo"] == "Exportación solicitada para validación"
               for event in events)


def test_exporta_contrato_sin_incluir_otro_contrato(
        app_cliente, admin, empresa_a, contrato_a, motor_admin):
    from tests.conftest import crear_contrato

    otro = crear_contrato(
        app_cliente, empresa_a, contrato_a["faena_id"], nombre="Contrato ajeno al alcance")
    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(
            empresa_a["company_id"], scope="contrato",
            resource_id=contrato_a["id"], categories=["contratos"]),
    )
    assert response.status_code == 200, response.text
    with ZipFile(io.BytesIO(response.content)) as archive:
        contracts = _csv_rows(archive, "datos/contratos.csv")
    assert {row["id"] for row in contracts} == {contrato_a["id"]}
    assert otro["id"] not in {row["id"] for row in contracts}


def test_exporta_actividad_de_entidades_relacionadas_al_contrato(
        app_cliente, admin, empresa_a, contrato_a, motor_admin):
    from tests.conftest import crear_contrato

    with motor_admin.begin() as connection:
        plataforma_id = connection.execute(sa.text(
            "SELECT id FROM faena_plataformas "
            "WHERE faena_id = :faena_id ORDER BY id LIMIT 1"),
            {"faena_id": contrato_a["faena_id"]},
        ).scalar_one()
        connection.execute(sa.text(
            'INSERT INTO actividad '
            '(company_id, user_id, tipo, modulo, descripcion, entidad_tipo, '
            'entidad_id, "metadata") '
            "VALUES (NULL, NULL, 'actualizacion', 'plataformas', "
            "'Catálogo de plataforma actualizado', 'faena_plataforma', "
            ":entidad_id, '{}'::jsonb)"),
            {"entidad_id": plataforma_id},
        )

    requisito_url = f"{API}/contratos/{{}}/requisitos"
    requisito_a = app_cliente.post(
        requisito_url.format(contrato_a["id"]),
        headers=empresa_a["headers"],
        json={"titulo": "Requisito de auditoría A", "ambito": "empresa"},
    )
    assert requisito_a.status_code == 201, requisito_a.text
    update_a = app_cliente.patch(
        f"{requisito_url.format(contrato_a['id'])}/{requisito_a.json()['id']}",
        headers=empresa_a["headers"],
        json={"titulo": "Requisito de auditoría A actualizado"},
    )
    assert update_a.status_code == 200, update_a.text

    otro = crear_contrato(
        app_cliente, empresa_a, contrato_a["faena_id"],
        nombre="Contrato para actividad excluida")
    requisito_b = app_cliente.post(
        requisito_url.format(otro["id"]),
        headers=empresa_a["headers"],
        json={"titulo": "Requisito de auditoría B", "ambito": "empresa"},
    )
    assert requisito_b.status_code == 201, requisito_b.text
    update_b = app_cliente.patch(
        f"{requisito_url.format(otro['id'])}/{requisito_b.json()['id']}",
        headers=empresa_a["headers"],
        json={"titulo": "Requisito de auditoría B actualizado"},
    )
    assert update_b.status_code == 200, update_b.text

    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(
            empresa_a["company_id"], scope="contrato",
            resource_id=contrato_a["id"], categories=["actividad"]),
    )
    assert response.status_code == 200, response.text
    with ZipFile(io.BytesIO(response.content)) as archive:
        activities = _csv_rows(archive, "datos/actividad.csv")
    entity_ids = {row["entidad_id"] for row in activities}
    assert requisito_a.json()["id"] in entity_ids
    assert requisito_b.json()["id"] not in entity_ids
    assert str(plataforma_id) in entity_ids


def test_exporta_solo_persona_o_equipo_seleccionado(
        app_cliente, admin, empresa_a, contrato_a):
    poblado = _crear_persona_y_equipo(app_cliente, empresa_a, contrato_a)
    for scope, key in (("persona", "trabajador"), ("equipo", "equipo")):
        response = app_cliente.post(
            f"{API}/admin/exports/data",
            headers=admin["headers"],
            json=_export_body(
                empresa_a["company_id"], scope=scope,
                resource_id=poblado[key],
                categories=["personas_equipos", "documentos"]),
        )
        assert response.status_code == 200, response.text
        with ZipFile(io.BytesIO(response.content)) as archive:
            subjects = _csv_rows(archive, "datos/sujetos.csv")
            documents = _csv_rows(archive, "datos/documentos.csv")
        assert {row["id"] for row in subjects} == {poblado[key]}
        assert all(row["sujeto_id"] == poblado[key] for row in documents)


def test_exportacion_deniega_recurso_de_otra_empresa(
        app_cliente, admin, empresa_a, contrato_b, motor_admin):
    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(
            empresa_a["company_id"], scope="contrato",
            resource_id=contrato_b["id"], categories=["contratos"]),
    )
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "RECURSO_NO_ENCONTRADO"
    with motor_admin.connect() as connection:
        result = connection.execute(sa.text(
            'SELECT "metadata" FROM actividad '
            "WHERE entidad_tipo = 'exportacion_datos' "
            "ORDER BY created_at DESC LIMIT 1")).scalar_one()
    assert result["resultado"] == "denegada"


def test_exportacion_requiere_admin_categoria_y_motivo(
        app_cliente, admin, empresa_a):
    body = _export_body(empresa_a["company_id"], categories=["documentos"])
    non_admin = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=empresa_a["headers"], json=body)
    assert non_admin.status_code == 403

    invalid_category = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json={**body, "categorias": ["credenciales"]},
    )
    assert invalid_category.status_code == 422
    assert invalid_category.json()["error"]["code"] == "CATEGORIA_INVALIDA"

    invalid_reason = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json={**body, "motivo": "             "},
    )
    assert invalid_reason.status_code == 400
    assert invalid_reason.json()["error"]["code"] == "MOTIVO_REQUERIDO"


def test_exportacion_streaming_no_lee_archivo_completo(
        app_cliente, admin, empresa_a, contrato_a, monkeypatch):
    documento = _documento_de_contrato(app_cliente, empresa_a, contrato_a)
    subir_archivo(app_cliente, empresa_a, documento["id"])
    content = b"xyz012" * (10 * 1024 * 1024)

    class StorageEnChunks:
        def read(self, _blob_path):
            raise AssertionError("El export no debe materializar el archivo completo")

        def iter_chunks(self, _blob_path):
            for offset in range(0, len(content), 64 * 1024):
                yield content[offset:offset + 64 * 1024]

    monkeypatch.setattr(
        business_exports, "get_storage", lambda: StorageEnChunks())
    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(empresa_a["company_id"], categories=["documentos"]),
    )
    assert response.status_code == 200, response.text
    with ZipFile(io.BytesIO(response.content)) as archive:
        metadata = _csv_rows(archive, "datos/documento_archivos.csv")
        assert archive.read(metadata[0]["ruta_archivo"]) == content


def test_exporta_muchas_filas_de_actividad(
        app_cliente, admin, empresa_a, motor_admin):
    with motor_admin.begin() as connection:
        connection.execute(sa.text(
            'INSERT INTO actividad '
            '(company_id, tipo, modulo, descripcion, entidad_tipo, "metadata") '
            "SELECT :company_id, 'visualizacion', 'export_prueba', "
            "'evento sintetico', 'evento_prueba', '{}'::jsonb "
            "FROM generate_series(1, 10000)"),
            {"company_id": empresa_a["company_id"]},
        )

    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(
            empresa_a["company_id"], categories=["actividad"]),
    )
    assert response.status_code == 200, response.text
    with ZipFile(io.BytesIO(response.content)) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        activities = _csv_rows(archive, "datos/actividad.csv")
    assert manifest["filas_por_tipo"]["actividad"] >= 10000
    assert len(activities) >= 10000


def test_fallo_de_storage_cancela_exportacion_y_limpia_temporal(
        app_cliente, admin, empresa_a, contrato_a, monkeypatch, motor_admin):
    documento = _documento_de_contrato(app_cliente, empresa_a, contrato_a)
    subir_archivo(app_cliente, empresa_a, documento["id"])
    temporales = []
    original_temporary_directory = business_exports.tempfile.TemporaryDirectory

    def create_temporary_directory(*args, **kwargs):
        temporary = original_temporary_directory(*args, **kwargs)
        temporales.append(Path(temporary.name))
        return temporary

    class StorageFallido:
        def iter_chunks(self, _blob_path):
            raise OSError("storage failure")

    monkeypatch.setattr(
        business_exports.tempfile, "TemporaryDirectory",
        create_temporary_directory)
    monkeypatch.setattr(business_exports, "get_storage", lambda: StorageFallido())
    response = app_cliente.post(
        f"{API}/admin/exports/data",
        headers=admin["headers"],
        json=_export_body(
            empresa_a["company_id"], categories=["documentos"]),
    )
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "EXPORTACION_FALLIDA"
    assert len(temporales) == 1
    assert not temporales[0].exists()
    with motor_admin.connect() as connection:
        result = connection.execute(sa.text(
            'SELECT "metadata" FROM actividad '
            "WHERE entidad_tipo = 'exportacion_datos' "
            "ORDER BY created_at DESC LIMIT 1")).scalar_one()
    assert result["resultado"] == "generacion_fallida"
