"""Registro acotado de actividad de sesiones de usuarios de clientes."""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from ..models import User
from ..models_ops import (
    OpsActivitySession, OpsCompanyActivityDaily, OpsUserActivityDaily,
)

TIME_ZONE = ZoneInfo("America/Santiago")
HEARTBEAT_MIN_SECONDS = 60
HEARTBEAT_MAX_SECONDS = 120


def _activity_dates(start: datetime, end: datetime) -> list[tuple[date, int]]:
    """Divide segundos entre días locales para no cruzar el límite de Santiago."""
    portions: list[tuple[date, int]] = []
    cursor = start
    while cursor < end:
        local_date = cursor.astimezone(TIME_ZONE).date()
        next_day = datetime.combine(
            local_date + timedelta(days=1), time.min, tzinfo=TIME_ZONE)
        boundary = min(end, next_day.astimezone(timezone.utc))
        seconds = int((boundary - cursor).total_seconds())
        if seconds:
            portions.append((local_date, seconds))
        cursor = boundary
    return portions


def _ensure_daily_rows(db: Session, user: User, activity_date: date) -> None:
    db.execute(insert(OpsUserActivityDaily).values(
        fecha=activity_date, user_id=user.id, company_id=user.company_id,
        segundos_activos=0,
    ).on_conflict_do_nothing(
        index_elements=[OpsUserActivityDaily.fecha, OpsUserActivityDaily.user_id]))
    db.execute(insert(OpsCompanyActivityDaily).values(
        fecha=activity_date, company_id=user.company_id, segundos_activos=0,
    ).on_conflict_do_nothing(
        index_elements=[OpsCompanyActivityDaily.fecha,
                        OpsCompanyActivityDaily.company_id]))


def _add_seconds(db: Session, user: User, activity_date: date, seconds: int) -> None:
    if seconds <= 0:
        return
    user_insert = insert(OpsUserActivityDaily).values(
        fecha=activity_date, user_id=user.id, company_id=user.company_id,
        segundos_activos=seconds,
    )
    db.execute(user_insert.on_conflict_do_update(
        index_elements=[OpsUserActivityDaily.fecha, OpsUserActivityDaily.user_id],
        set_={"segundos_activos": (
            OpsUserActivityDaily.segundos_activos + user_insert.excluded.segundos_activos
        )},
    ))
    company_insert = insert(OpsCompanyActivityDaily).values(
        fecha=activity_date, company_id=user.company_id, segundos_activos=seconds,
    )
    db.execute(company_insert.on_conflict_do_update(
        index_elements=[OpsCompanyActivityDaily.fecha,
                        OpsCompanyActivityDaily.company_id],
        set_={"segundos_activos": (
            OpsCompanyActivityDaily.segundos_activos
            + company_insert.excluded.segundos_activos
        )},
    ))


def registrar_heartbeat(
    db: Session, user: User, session_id: uuid.UUID, now: datetime,
) -> int:
    """Acredita hasta dos minutos por señal y deduplica pestañas de una sesión."""
    if user.company_id is None:
        raise ValueError("La sesión de actividad requiere una empresa asociada")

    insert_session = insert(OpsActivitySession).values(
        session_id=session_id,
        user_id=user.id,
        company_id=user.company_id,
        started_at=now,
        last_heartbeat_at=now,
    ).on_conflict_do_nothing(index_elements=[OpsActivitySession.session_id])
    created = db.execute(insert_session.returning(
        OpsActivitySession.session_id)).scalar_one_or_none() is not None
    if created:
        _ensure_daily_rows(db, user, now.astimezone(TIME_ZONE).date())
        db.commit()
        return 0

    session = db.scalar(select(OpsActivitySession).where(
        OpsActivitySession.session_id == session_id).with_for_update())
    if (session is None or session.user_id != user.id
            or session.company_id != user.company_id or session.ended_at is not None):
        db.rollback()
        raise ValueError("La sesión no está disponible para registrar actividad")

    previous = session.last_heartbeat_at
    if previous.tzinfo is None:
        previous = previous.replace(tzinfo=timezone.utc)
    elapsed = (now - previous).total_seconds()
    _ensure_daily_rows(db, user, now.astimezone(TIME_ZONE).date())

    if elapsed < HEARTBEAT_MIN_SECONDS:
        db.commit()
        return 0

    if elapsed > HEARTBEAT_MAX_SECONDS:
        session.last_heartbeat_at = now
        db.commit()
        return 0

    seconds = int(elapsed)
    session.last_heartbeat_at = now
    for activity_date, portion in _activity_dates(
            now - timedelta(seconds=seconds), now):
        _add_seconds(db, user, activity_date, portion)
    db.commit()
    return seconds
