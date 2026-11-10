import io
import json
from zipfile import ZipFile

from app.services.actividad import minimizar_texto
from tests.conftest import API


def test_minimizar_texto_redacta_email_rut_y_secretos():
    texto = (
        "Usuario persona@empresa.cl RUT 12.345.678-5 "
        "token=secreto password:clave credential=archivo"
    )

    resultado = minimizar_texto(texto)

    assert "persona@empresa.cl" not in resultado
    assert "12.345.678-5" not in resultado
    assert "secreto" not in resultado
    assert "clave" not in resultado
    assert "archivo" not in resultado


def test_minimizar_texto_redacta_urls_firmadas():
    resultado = minimizar_texto(
        "Descarga https://storage.example/file.pdf?sv=1&sig=secreto."
    )

    assert "secreto" not in resultado
    assert "sig=" not in resultado
    assert "[URL firmada redactada]." in resultado


def test_minimizar_metadata_redacta_campos_de_secreto():
    from app.services.actividad import minimizar_metadata

    resultado = minimizar_metadata({
        "password": "no almacenar",
        "detalles": [{"api_key": "no almacenar", "email": "persona@empresa.cl"}],
    })

    assert resultado["password"] == "[dato sensible redactado]"
    assert resultado["detalles"][0]["api_key"] == "[dato sensible redactado]"
    assert "persona@empresa.cl" not in str(resultado)


def test_consulta_de_auditoria_se_redacta_y_deja_traza(
        app_cliente, admin, motor_admin):
    import json
    from sqlalchemy import text

    with motor_admin.begin() as conn:
        conn.execute(text("""
            INSERT INTO actividad
                (company_id, user_id, tipo, modulo, descripcion, metadata)
            VALUES
                (NULL, NULL, 'visualizacion', 'test_privacidad',
                 :descripcion, CAST(:metadata AS jsonb))
        """), {
            "descripcion": "URL https://storage.example/doc?sig=secreto.",
            "metadata": json.dumps({"password": "secreto"}),
        })

    respuesta = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"modulo": "test_privacidad"},
    )

    assert respuesta.status_code == 200, respuesta.text
    fila = respuesta.json()["items"][0]
    assert "secreto" not in fila["descripcion"]
    assert "[URL firmada redactada]" in fila["descripcion"]

    with motor_admin.connect() as conn:
        traza = conn.execute(text("""
            SELECT metadata
              FROM actividad
             WHERE modulo = 'auditoria'
               AND user_id = CAST(:user_id AS uuid)
             ORDER BY id DESC
             LIMIT 1
        """), {"user_id": admin["user_id"]}).scalar_one()

    assert traza["recurso"] == "global"
    assert traza["resultados"] == 1


def test_consulta_de_auditoria_usuarios_deja_traza(
        app_cliente, admin, motor_admin):
    from sqlalchemy import text

    respuesta = app_cliente.get(
        f"{API}/admin/users/audit", headers=admin["headers"])

    assert respuesta.status_code == 200, respuesta.text
    with motor_admin.connect() as conn:
        traza = conn.execute(text("""
            SELECT metadata
              FROM actividad
             WHERE modulo = 'auditoria'
               AND user_id = CAST(:user_id AS uuid)
             ORDER BY id DESC
             LIMIT 1
        """), {"user_id": admin["user_id"]}).scalar_one()

    assert traza["recurso"] == "usuarios"
    assert traza["resultados"] == len(respuesta.json()["items"])


def test_exportacion_redacta_actividad_historica(app_cliente, admin, motor_admin):
    from sqlalchemy import text

    marcador = "test_export_privacidad"
    with motor_admin.begin() as conn:
        conn.execute(text("""
            INSERT INTO actividad
                (company_id, user_id, tipo, modulo, descripcion, metadata)
            VALUES
                (NULL, NULL, 'visualizacion', :modulo,
                 'Correo persona@example.cl RUT 12.345.678-5 token=secreto123',
                 CAST(:metadata AS jsonb))
        """), {
            "modulo": marcador,
            "metadata": json.dumps({"password": "no-exportar"}),
        })

    grant = app_cliente.post(
        f"{API}/admin/access-grants",
        headers=admin["headers"],
        json={
            "admin_user_id": admin["user_id"],
            "recurso_tipo": "usuario",
            "motivo": "Validar exportación de actividad",
            "horas": 1,
        },
    )
    assert grant.status_code == 201, grant.text
    headers = dict(admin["headers"])
    headers["X-Access-Grant"] = grant.json()["id"]
    respuesta = app_cliente.get(
        f"{API}/admin/backups/export",
        headers=headers,
        params={
            "formato": "zip",
            "motivo": "Revision operacional autorizada",
        },
    )
    assert respuesta.status_code == 200, respuesta.text

    with ZipFile(io.BytesIO(respuesta.content)) as archive:
        filas = json.loads(archive.read("json/actividad.json"))
    fila = next(fila for fila in filas if fila["modulo"] == marcador)
    assert "persona@example.cl" not in fila["descripcion"]
    assert "12.345.678-5" not in fila["descripcion"]
    assert "secreto123" not in fila["descripcion"]
    assert fila["metadata"]["password"] == "[dato sensible redactado]"


def test_poda_aplica_plazos_y_preserva_historicos_previos(
        app_cliente, motor_admin):
    import uuid
    from sqlalchemy import text
    from app.database import worker_session

    marcador = str(uuid.uuid4())
    with motor_admin.begin() as conn:
        fecha_original = conn.execute(text(
            "SELECT effective_at FROM privacy_retention_policy WHERE id = true"
        )).scalar_one()
        conn.execute(text("""
            UPDATE privacy_retention_policy
               SET effective_at = TIMESTAMPTZ '2000-01-01 00:00:00+00'
             WHERE id = true
        """))
        conn.execute(text("""
            INSERT INTO actividad
                (company_id, user_id, tipo, modulo, descripcion, metadata, created_at)
            VALUES
                (NULL, NULL, 'visualizacion', :marcador, 'purgar',
                 '{}'::jsonb, TIMESTAMPTZ '2024-01-01 00:00:00+00'),
                (NULL, NULL, 'visualizacion', :historico, 'preservar',
                 '{}'::jsonb, TIMESTAMPTZ '1999-01-01 00:00:00+00')
        """), {"marcador": marcador, "historico": f"{marcador}_historico"})
        conn.execute(text("""
            INSERT INTO bitacora_cambios
                (tabla, registro_id, operacion, campos, created_at)
            VALUES
                ('test_privacidad', CAST(:id AS uuid), 'UPDATE', '{}'::jsonb,
                 TIMESTAMPTZ '2024-01-01 00:00:00+00')
        """), {"id": str(uuid.uuid4())})
        conn.execute(text("""
            INSERT INTO ops_job_runs (job_clave, status, disparo, created_at)
            VALUES ('ops_retencion', 'ok', 'cron', TIMESTAMPTZ '2024-01-01 00:00:00+00')
        """))
        conn.execute(text("""
            INSERT INTO ops_incidentes
                (componente, severidad, estado, origen, titulo, resolucion,
                 resuelto_at, abierto_at, updated_at)
            VALUES ('api', 'degradado', 'resuelto', 'manual', :marcador,
                    'validado', TIMESTAMPTZ '2024-01-01 00:00:00+00',
                    TIMESTAMPTZ '2024-01-01 00:00:00+00',
                    TIMESTAMPTZ '2024-01-01 00:00:00+00')
        """), {"marcador": marcador})
        conn.execute(text("""
            INSERT INTO ops_disponibilidad_diaria
                (componente, fecha, estado, uptime_pct, checks_total, checks_fallidos)
            VALUES ('api', DATE '2024-01-01', 'operativo', 100, 1, 0)
        """))

    try:
        with worker_session(is_admin=True) as db:
            podados = db.execute(text(
                "SELECT * FROM ops_podar_privacidad()"
            )).one()
            db.commit()

        assert podados.actividad_podada >= 1
        assert podados.bitacora_podada >= 1
        assert podados.runs_podados >= 1
        assert podados.incidentes_podados >= 1
        assert podados.disponibilidad_podada >= 1
        with motor_admin.connect() as conn:
            registros = conn.execute(text("""
                SELECT modulo FROM actividad
                 WHERE modulo IN (:marcador, :historico)
            """), {"marcador": marcador,
                   "historico": f"{marcador}_historico"}).scalars().all()
        assert registros == [f"{marcador}_historico"]
    finally:
        with motor_admin.begin() as conn:
            conn.execute(text("""
                UPDATE privacy_retention_policy
                   SET effective_at = :fecha
                 WHERE id = true
            """), {"fecha": fecha_original})
