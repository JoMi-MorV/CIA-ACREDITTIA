from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import text

from app import security
from app.models_ops import OpsUserActivityDaily
from app.routers import auth as auth_router
from app.database import worker_session
from tests.conftest import API, CLAVE


class _Clock:
    current = datetime.now(timezone.utc).replace(microsecond=0)

    @classmethod
    def now(cls, tz=None):
        return cls.current.astimezone(tz) if tz else cls.current.replace(tzinfo=None)


def _set_clock(monkeypatch, instant):
    _Clock.current = instant
    monkeypatch.setattr(auth_router, "datetime", _Clock)


def _heartbeat(cliente, headers):
    return cliente.post(f"{API}/auth/activity/heartbeat", headers=headers)


def test_heartbeat_autenticado_deduplica_pestanas_y_conserva_sesion(
        app_cliente, empresa_a, monkeypatch, motor_admin):
    token_original = security.decode_access_token(empresa_a["token"])
    refresh = app_cliente.post(f"{API}/auth/refresh",
                              json={"refresh_token": empresa_a["refresh_token"]})
    assert refresh.status_code == 200, refresh.text
    token_nuevo = security.decode_access_token(refresh.json()["access_token"])
    assert token_nuevo["sid"] == token_original["sid"]

    headers = {"Authorization": f"Bearer {refresh.json()['access_token']}"}
    _set_clock(monkeypatch, datetime.now(timezone.utc).replace(microsecond=0))
    primera = _heartbeat(app_cliente, headers)
    assert primera.status_code == 200, primera.text
    assert primera.json()["segundos_registrados"] == 0

    _Clock.current += timedelta(seconds=60)
    segunda = _heartbeat(app_cliente, headers)
    assert segunda.status_code == 200
    assert segunda.json()["segundos_registrados"] == 60

    _Clock.current += timedelta(seconds=1)
    duplicada = _heartbeat(app_cliente, headers)
    assert duplicada.status_code == 200
    assert duplicada.json()["segundos_registrados"] == 0

    activity_date = _Clock.current.astimezone(
        ZoneInfo("America/Santiago")).date()
    with motor_admin.connect() as conn:
        daily = conn.execute(text(
            "SELECT segundos_activos FROM ops_actividad_usuario_diaria "
            "WHERE fecha=:fecha AND user_id=:user_id"
        ), {"fecha": activity_date,
            "user_id": uuid.UUID(empresa_a["user_id"])}).scalar_one()
        session_user = conn.execute(text(
            "SELECT user_id FROM ops_sesiones_actividad WHERE session_id=:session_id"
        ), {"session_id": uuid.UUID(token_original["sid"])}).scalar_one()
    assert daily == 60
    assert session_user == uuid.UUID(empresa_a["user_id"])

    logout = app_cliente.post(f"{API}/auth/logout", headers=headers,
                              json={"refresh_token": refresh.json()["refresh_token"]})
    assert logout.status_code == 200
    assert _heartbeat(app_cliente, headers).status_code == 401


def test_heartbeats_suman_sesiones_concurrentes_y_descartan_brechas_largas(
        app_cliente, empresa_a, monkeypatch, motor_admin):
    segunda_login = app_cliente.post(f"{API}/auth/login", json={
        "email": empresa_a["email"], "password": CLAVE})
    assert segunda_login.status_code == 200
    headers_a = empresa_a["headers"]
    headers_b = {"Authorization": f"Bearer {segunda_login.json()['access_token']}"}
    _set_clock(monkeypatch, datetime.now(timezone.utc).replace(microsecond=0))

    assert _heartbeat(app_cliente, headers_a).json()["segundos_registrados"] == 0
    _Clock.current += timedelta(seconds=60)
    assert _heartbeat(app_cliente, headers_b).json()["segundos_registrados"] == 0
    _Clock.current += timedelta(seconds=60)
    assert _heartbeat(app_cliente, headers_a).json()["segundos_registrados"] == 120
    _Clock.current += timedelta(seconds=60)
    assert _heartbeat(app_cliente, headers_b).json()["segundos_registrados"] == 120

    activity_date = _Clock.current.astimezone(
        ZoneInfo("America/Santiago")).date()
    with motor_admin.connect() as conn:
        daily = conn.execute(text(
            "SELECT segundos_activos FROM ops_actividad_usuario_diaria "
            "WHERE fecha=:fecha AND user_id=:user_id"
        ), {"fecha": activity_date,
            "user_id": uuid.UUID(empresa_a["user_id"])}).scalar_one()
    assert daily == 240

    _Clock.current += timedelta(seconds=121)
    brecha = _heartbeat(app_cliente, headers_a)
    assert brecha.status_code == 200
    assert brecha.json()["segundos_registrados"] == 0
    _Clock.current += timedelta(seconds=60)
    recuperado = _heartbeat(app_cliente, headers_a)
    assert recuperado.json()["segundos_registrados"] == 60


def test_admin_no_se_mide_y_salud_distingue_na_de_cero(
        app_cliente, admin, empresa_a, motor_admin):
    admin_heartbeat = _heartbeat(app_cliente, admin["headers"])
    assert admin_heartbeat.status_code == 403

    sin_datos = app_cliente.get(
        f"{API}/admin/stats/active-usage?period=today",
        headers=admin["headers"])
    assert sin_datos.status_code == 200, sin_datos.text
    assert sin_datos.json()["measured_users"] == 0
    assert sin_datos.json()["active_minutes_total"] == 0
    assert sin_datos.json()["active_minutes_per_user"] is None

    today = datetime.now(ZoneInfo("America/Santiago")).date()
    with motor_admin.begin() as conn:
        conn.execute(text("""
            INSERT INTO ops_actividad_usuario_diaria
              (fecha, user_id, company_id, segundos_activos)
            SELECT :fecha, id, company_id, 0 FROM users WHERE id=:user_id
        """), {"fecha": today, "user_id": uuid.UUID(empresa_a["user_id"])})
    with worker_session(is_admin=True) as db:
        assert db.query(OpsUserActivityDaily).filter(
            OpsUserActivityDaily.fecha == today,
            OpsUserActivityDaily.user_id == uuid.UUID(empresa_a["user_id"]),
        ).all() == []

    medido_cero = app_cliente.get(
        f"{API}/admin/stats/active-usage?period=today",
        headers=admin["headers"])
    assert medido_cero.status_code == 200, medido_cero.text
    assert medido_cero.json()["measured_users"] == 1
    assert medido_cero.json()["active_minutes_total"] == 0
    assert medido_cero.json()["active_minutes_per_user"] == 0


def test_ventanas_de_actividad_usan_dias_calendario_locales(
        app_cliente, admin, empresa_a, motor_admin):
    today = datetime.now(ZoneInfo("America/Santiago")).date()
    month_start = today.replace(day=1)
    user_id = uuid.UUID(empresa_a["user_id"])
    seconds_by_date = {
        today: 60,
        today - timedelta(days=6): 120,
        today - timedelta(days=7): 3600,
        today - timedelta(days=29): 180,
        today - timedelta(days=30): 1800,
        month_start: 300,
        month_start - timedelta(days=1): 2400,
    }
    with motor_admin.begin() as conn:
        company_id = conn.execute(text(
            "SELECT company_id FROM users WHERE id=:user_id"
        ), {"user_id": user_id}).scalar_one()
        conn.execute(OpsUserActivityDaily.__table__.insert(), [
            {"fecha": activity_date, "user_id": user_id,
             "company_id": company_id, "segundos_activos": seconds}
            for activity_date, seconds in seconds_by_date.items()
        ])

    periods = {
        "today": (today, today + timedelta(days=1)),
        "last_7_days": (today - timedelta(days=6), today + timedelta(days=1)),
        "last_30_days": (today - timedelta(days=29), today + timedelta(days=1)),
        "month": (month_start, today + timedelta(days=1)),
    }
    for period, (start, end) in periods.items():
        response = app_cliente.get(
            f"{API}/admin/stats/active-usage?period={period}",
            headers=admin["headers"])
        assert response.status_code == 200, response.text
        data = response.json()
        expected_seconds = sum(
            seconds for activity_date, seconds in seconds_by_date.items()
            if start <= activity_date < end)
        assert data["start_date"] == start.isoformat()
        assert data["end_date_exclusive"] == end.isoformat()
        assert data["measured_users"] == 1
        assert data["active_minutes_total"] == round(expected_seconds / 60, 2)


def test_retencion_de_telemetria_aplica_plazos_dec08(
        app_cliente, empresa_a, motor_admin):
    now = datetime.now(timezone.utc)
    today = now.astimezone(ZoneInfo("America/Santiago")).date()
    old_effective_at = now - timedelta(days=500)
    session_id = uuid.uuid4()
    user_id = uuid.UUID(empresa_a["user_id"])
    with motor_admin.begin() as conn:
        original_policy = conn.execute(text(
            "SELECT effective_at FROM privacy_retention_policy WHERE id = true"
        )).scalar_one()
        conn.execute(text(
            "UPDATE privacy_retention_policy SET effective_at=:inicio WHERE id=true"
        ), {"inicio": old_effective_at})
        conn.execute(text("""
            INSERT INTO ops_sesiones_actividad
              (session_id, user_id, company_id, started_at, last_heartbeat_at)
            SELECT :session_id, id, company_id, :anterior, :anterior
              FROM users WHERE id=:user_id
        """), {"session_id": session_id, "user_id": user_id,
               "anterior": now - timedelta(days=91)})
        conn.execute(text("""
            INSERT INTO ops_actividad_usuario_diaria
              (fecha, user_id, company_id, segundos_activos)
            SELECT :fecha, id, company_id, 60 FROM users WHERE id=:user_id
        """), {"fecha": today - timedelta(days=91), "user_id": user_id})
        conn.execute(text("""
            INSERT INTO ops_actividad_empresa_diaria
              (fecha, company_id, segundos_activos)
            SELECT :fecha, company_id, 60 FROM users WHERE id=:user_id
        """), {"fecha": today - timedelta(days=91), "user_id": user_id})
        conn.execute(text("""
            INSERT INTO ops_actividad_empresa_diaria
              (fecha, company_id, segundos_activos)
            SELECT :fecha, company_id, 60 FROM users WHERE id=:user_id
        """), {"fecha": today - timedelta(days=400), "user_id": user_id})

    try:
        with worker_session(is_admin=True) as db:
            result = db.execute(text(
                "SELECT * FROM ops_podar_telemetria_actividad()")).one()
            db.commit()
        assert tuple(result) == (1, 1, 1)
        with motor_admin.connect() as conn:
            remaining_company_days = conn.execute(text(
                "SELECT fecha FROM ops_actividad_empresa_diaria "
                "WHERE company_id=(SELECT company_id FROM users WHERE id=:user_id)"
            ), {"user_id": user_id}).scalars().all()
        assert remaining_company_days == [today - timedelta(days=91)]
    finally:
        with motor_admin.begin() as conn:
            conn.execute(text(
                "UPDATE privacy_retention_policy SET effective_at=:inicio WHERE id=true"
            ), {"inicio": original_policy})


def test_job_retencion_incluye_el_resultado_de_telemetria(app_cliente):
    from worker.ops_tasks import run_retencion

    with worker_session(is_admin=True) as db:
        total, message = run_retencion(db)

    assert total >= 0
    assert "telemetría_sesiones=" in message
    assert "telemetría_usuarios=" in message
    assert "telemetría_empresas=" in message
