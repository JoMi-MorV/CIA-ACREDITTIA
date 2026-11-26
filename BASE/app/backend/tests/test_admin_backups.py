from __future__ import annotations

import base64
import io
import json
import re
from pathlib import Path
from zipfile import ZipFile

import pytest
import sqlalchemy as sa

from app.services import backups, console_exports
from tests.conftest import API


def concesion_usuarios(app_cliente, admin, empresa=None, recurso_id=None):
    cuerpo = {
        "admin_user_id": admin["user_id"],
        "recurso_tipo": "usuario",
        "motivo": "Validar exportación de usuarios",
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


def autoconcesion_exportacion(app_cliente, admin):
    cuerpo = {
        "motivo": "Validar exportación administrativa",
    }
    respuesta = app_cliente.post(
        f"{API}/admin/backups/export-grants",
        headers=admin["headers"], json=cuerpo)
    assert respuesta.status_code == 201, respuesta.text
    headers = dict(admin["headers"])
    headers["X-Access-Grant"] = respuesta.json()["id"]
    return headers


def test_backups_solo_admin(app_cliente, empresa_a):
    response = app_cliente.get(
        f"{API}/admin/backups/status", headers=empresa_a["headers"])
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "SOLO_ADMIN"


def test_import_respaldo_rechaza_archivo_superior_al_limite(
        app_cliente, admin, monkeypatch):
    from app.routers import admin_backups

    monkeypatch.setattr(admin_backups, "MAX_IMPORT_BYTES", 4)
    monkeypatch.setattr(admin_backups, "MAX_IMPORT_REQUEST_BYTES", 1024)
    response = app_cliente.post(
        f"{API}/admin/backups/import",
        headers=admin["headers"],
        files={"file": ("sobre-limite.acb", b"12345",
                        "application/octet-stream")},
    )
    assert response.status_code == 413, response.text
    assert response.json()["error"]["code"] == "RESPALDO_DEMASIADO_GRANDE"


def test_import_respaldo_rechaza_content_length_superior_al_limite(
        app_cliente, admin, monkeypatch):
    from app.routers import admin_backups

    monkeypatch.setattr(admin_backups, "MAX_IMPORT_REQUEST_BYTES", 1)
    response = app_cliente.post(
        f"{API}/admin/backups/import",
        headers=admin["headers"],
        files={"file": ("backup.acb", b"1234",
                        "application/octet-stream")},
    )
    assert response.status_code == 413, response.text
    assert response.json()["error"]["code"] == "RESPALDO_DEMASIADO_GRANDE"


def test_restauracion_exige_confirmacion_exacta(app_cliente, admin):
    backup_id = "0123456789abcdef0123456789abcdef"
    response = app_cliente.post(
        f"{API}/admin/backups/{backup_id}/restore",
        headers=admin["headers"],
        json={"confirmation": "RESTAURAR"},
    )
    assert response.status_code == 409
    assert "confirmación" in response.json()["error"]["message"]


def test_programacion_no_se_activa_sin_configuracion(app_cliente, admin):
    response = app_cliente.patch(
        f"{API}/admin/procesos/admin_backup",
        headers=admin["headers"],
        json={"activo": True},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESPALDO_NO_CONFIGURADO"


def test_respaldo_manual_no_se_ejecuta_sin_configuracion(app_cliente, admin):
    response = app_cliente.post(
        f"{API}/admin/procesos/admin_backup/ejecutar",
        headers=admin["headers"],
        json={"motivo": "prueba"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "RESPALDO_NO_CONFIGURADO"


def test_estado_backups_no_expone_configuracion(app_cliente, admin):
    response = app_cliente.get(
        f"{API}/admin/backups/status", headers=admin["headers"])
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["retention_count"] == 8
    assert body["schedule"] == "0 2 * * *"
    assert "backup_database_url" not in body
    assert "encryption_key" not in body


def test_restauracion_actualiza_backup_de_esquema_22(motor_admin, monkeypatch):
    schema_dir = Path(__file__).resolve().parents[3] / "modelo_datos"
    maintenance_url = motor_admin.url.set(
        drivername="postgresql").render_as_string(hide_password=False)
    monkeypatch.setattr(backups.settings, "backup_restore_database_url", maintenance_url)
    monkeypatch.setattr(backups.settings, "schema_dir", str(schema_dir))
    with motor_admin.begin() as conn:
        conn.execute(sa.text(
            "UPDATE ops_jobs SET cron_expr='0 2 * * 0' "
            "WHERE clave='admin_backup'"))
        conn.execute(sa.text(
            "DELETE FROM app_schema_migrations WHERE version >= 23"))
    try:
        backups._migrate_restored_schema(motor_admin.url.database)
        with motor_admin.connect() as conn:
            version = conn.execute(sa.text(
                "SELECT max(version) FROM app_schema_migrations")).scalar_one()
            schedule, active = conn.execute(sa.text(
                "SELECT cron_expr, activo FROM ops_jobs "
                "WHERE clave='admin_backup'")).one()
        assert version == 25
        assert schedule == "0 2 * * *"
        assert active is False
    finally:
        with motor_admin.begin() as conn:
            conn.execute(sa.text(
                "UPDATE ops_jobs SET cron_expr='0 2 * * *' "
                "WHERE clave='admin_backup'"))
            conn.execute(sa.text(
                "INSERT INTO app_schema_migrations (version) VALUES (23), (24), (25) "
                "ON CONFLICT DO NOTHING"))


def test_export_console_zip_solo_contiene_resumenes_agregados(
        app_cliente, admin, empresa_a):
    headers = autoconcesion_exportacion(app_cliente, admin)
    response = app_cliente.get(
        f"{API}/admin/backups/export?formato=zip"
        "&motivo=Revision%20operacional%20autorizada",
        headers=headers)
    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/zip"
    with ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
        assert {
            "manifest.json",
            "csv/indicadores.csv",
            "json/indicadores.json",
            "csv/metricas_mensuales.csv",
            "json/salud_servicios.json",
            "json/procesos.json",
            "json/incidentes.json",
            "json/actividad.json",
        } <= names
        assert not any(name.startswith(("csv/companies.", "json/companies.",
                                        "csv/users.", "json/users.",
                                        "csv/contratos.", "json/contratos.",
                                        "csv/actividad_detalle.", "json/actividad_detalle."))
                       for name in names)
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["alcance"] == "resumen general agregado de la consola ADMIN"
        assert manifest["incluye_registros_identificables"] is False
        exportado = b"".join(archive.read(name) for name in names)
        assert empresa_a["company_id"].encode() not in exportado
        assert empresa_a["user_id"].encode() not in exportado


def test_export_console_pdf_resumen(app_cliente, admin):
    response = app_cliente.get(
        f"{API}/admin/backups/export?formato=pdf"
        "&motivo=Revision%20operacional%20autorizada",
        headers=admin["headers"])
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF")
    assert len(re.findall(rb"/Type /Page\b", response.content)) >= 5
    assert re.search(rb"/Subject \(Generated at \d{4}-\d{2}-\d{2}T"
                     rb"\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}\)", response.content)


def test_export_console_requiere_motivo_y_lo_audita(
        app_cliente, admin, motor_admin):
    sin_motivo = app_cliente.get(
        f"{API}/admin/backups/export?formato=zip", headers=admin["headers"])
    assert sin_motivo.status_code == 400
    assert sin_motivo.json()["error"]["code"] == "MOTIVO_REQUERIDO"

    motivo_corto = app_cliente.get(
        f"{API}/admin/backups/export?formato=zip&motivo=   ",
        headers=admin["headers"])
    assert motivo_corto.status_code == 400
    assert motivo_corto.json()["error"]["code"] == "MOTIVO_REQUERIDO"

    motivo_largo = app_cliente.get(
        f"{API}/admin/backups/export?formato=zip&motivo={'x' * 241}",
        headers=admin["headers"])
    assert motivo_largo.status_code == 400
    assert motivo_largo.json()["error"]["code"] == "MOTIVO_INVALIDO"

    motivo = "Revision operacional autorizada"
    headers = autoconcesion_exportacion(app_cliente, admin)
    response = app_cliente.get(
        f"{API}/admin/backups/export?formato=zip&motivo={motivo.replace(' ', '%20')}",
        headers=headers)
    assert response.status_code == 200, response.text

    with motor_admin.connect() as conn:
        audit = conn.execute(sa.text(
            "SELECT descripcion FROM actividad "
            "WHERE entidad_tipo = 'admin_export' "
            "ORDER BY created_at DESC LIMIT 1")).scalar_one()
    assert motivo in audit


def test_export_zip_requires_global_summary_grant(app_cliente, admin):
    params = {"formato": "zip", "motivo": "Validación de alcance RF-BUS-02"}
    sin_concesion = app_cliente.get(
        f"{API}/admin/backups/export", headers=admin["headers"], params=params)
    assert sin_concesion.status_code == 403
    assert sin_concesion.json()["error"]["code"] == "PERMISO_INFORMACION_REQUERIDO"

    headers = autoconcesion_exportacion(app_cliente, admin)
    respuesta = app_cliente.get(
        f"{API}/admin/backups/export", headers=headers, params=params)
    assert respuesta.status_code == 200, respuesta.text
    with ZipFile(io.BytesIO(respuesta.content)) as archive:
        manifiesto = json.loads(archive.read("manifest.json"))
        nombres = set(archive.namelist())
    assert "json/indicadores.json" in nombres
    assert "csv/companies.csv" not in nombres
    assert "json/users.json" not in nombres
    assert manifiesto["incluye_registros_identificables"] is False


def test_export_zip_rechaza_concesion_de_usuarios_no_especifica(
        app_cliente, admin, empresa_a):
    headers = concesion_usuarios(app_cliente, admin, empresa_a)
    respuesta = app_cliente.get(
        f"{API}/admin/backups/export",
        headers=headers,
        params={"formato": "zip", "motivo": "Exportación global aprobada"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"


def test_export_zip_rechaza_concesion_revocada(
        app_cliente, admin, empresa_a):
    headers = autoconcesion_exportacion(app_cliente, admin)
    grant_id = headers["X-Access-Grant"]
    revocada = app_cliente.post(
        f"{API}/admin/access-grants/{grant_id}/revoke",
        headers=admin["headers"], json={})
    assert revocada.status_code == 200, revocada.text
    respuesta = app_cliente.get(
        f"{API}/admin/backups/export",
        headers=headers,
        params={"formato": "zip", "motivo": "Exportación ya revocada"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"


def test_export_zip_rechaza_concesion_expirada(
        app_cliente, admin, empresa_a, motor_admin):
    headers = autoconcesion_exportacion(app_cliente, admin)
    grant_id = headers["X-Access-Grant"]
    with motor_admin.begin() as conn:
        conn.execute(sa.text(
            "UPDATE admin_access_grants SET expires_at = now() - interval '1 minute' "
            "WHERE id = :grant_id"), {"grant_id": grant_id})

    respuesta = app_cliente.get(
        f"{API}/admin/backups/export",
        headers=headers,
        params={"formato": "zip", "motivo": "Exportación ya expirada"},
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "PERMISO_INFORMACION_INVALIDO"


def test_export_grant_rechaza_alcance_por_empresa(app_cliente, admin, empresa_a):
    grant_empresa = app_cliente.post(
        f"{API}/admin/backups/export-grants",
        headers=admin["headers"],
        json={
            "motivo": "Validación de exportación general",
            "alcance": "empresa",
            "company_id": empresa_a["company_id"],
        },
    )
    assert grant_empresa.status_code == 422


def test_export_pdf_summary_needs_no_user_grant(app_cliente, admin):
    response = app_cliente.get(
        f"{API}/admin/backups/export",
        headers=admin["headers"],
        params={"formato": "pdf", "motivo": "Reporte agregado de operaciones"},
    )
    assert response.status_code == 200, response.text
    assert response.content.startswith(b"%PDF")
    assert len(re.findall(rb"/Type /Page\b", response.content)) >= 5


def test_encryption_roundtrip_and_tamper_detection(tmp_path, monkeypatch):
    key = base64.urlsafe_b64encode(b"k" * 32).decode("ascii")
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY", key)
    source = tmp_path / "source.bin"
    encrypted = tmp_path / "backup.acb"
    decrypted = tmp_path / "decrypted.bin"
    source.write_bytes((b"operational-backup" * 90000) + b"tail")

    backups._encrypt(source, encrypted)
    backups._decrypt(encrypted, decrypted)
    assert decrypted.read_bytes() == source.read_bytes()

    damaged = bytearray(encrypted.read_bytes())
    damaged[-1] ^= 0x40
    encrypted.write_bytes(damaged)
    with pytest.raises(backups.BackupError, match="autenticar"):
        backups._decrypt(encrypted, tmp_path / "damaged.bin")


def test_delete_backup_removes_package_and_sidecar(tmp_path, monkeypatch):
    monkeypatch.setattr(backups.settings, "backups_dir", str(tmp_path))
    backup_id = "0123456789abcdef0123456789abcdef"
    package = tmp_path / "acredittia-test.acb"
    package.write_bytes(b"encrypted backup")
    (tmp_path / f"{backup_id}.json").write_text(
        backups.json.dumps({"id": backup_id, "file": package.name}),
        encoding="utf-8",
    )

    result = backups.delete_backup(backup_id)

    assert result == {"id": backup_id, "deleted": True}
    assert not package.exists()
    assert not (tmp_path / f"{backup_id}.json").exists()


def test_recuperacion_calcula_rpo_desde_fecha_del_respaldo(tmp_path, monkeypatch):
    monkeypatch.setattr(backups.settings, "backups_dir", str(tmp_path))
    created = backups.datetime(2026, 11, 4, 3, 0, tzinfo=backups.timezone.utc)
    (tmp_path / "0123456789abcdef0123456789abcdef.json").write_text(
        backups.json.dumps({"created_at": created.isoformat()}), encoding="utf-8")

    restored = backups.datetime(2026, 11, 4, 4, 0, tzinfo=backups.timezone.utc)
    assert backups.backup_recovery_point(
        "0123456789abcdef0123456789abcdef", restored_at=restored) == 3600.0


def test_produccion_no_reutiliza_url_de_lectura_para_restaurar(monkeypatch):
    monkeypatch.setattr(backups.settings, "app_env", "production")
    monkeypatch.setattr(backups.settings, "backup_database_url",
                        "postgresql+psycopg://backup@db/acredittia")
    monkeypatch.setattr(backups.settings, "backup_restore_database_url", "")
    with pytest.raises(backups.BackupError, match="BACKUP_RESTORE_DATABASE_URL"):
        backups._maintenance_url()


def test_export_csv_protects_spreadsheet_formulas():
    assert console_exports._csv_value("=1+1") == "'=1+1"
    assert console_exports._csv_value("  =1+1") == "'  =1+1"
    assert console_exports._csv_value("normal") == "normal"
