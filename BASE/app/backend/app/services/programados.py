"""Disparo de los reportes programados.

`celery beat` invoca `disparar_pendientes()` cada minuto. Aquí se decide
qué expresiones cron corresponden a este momento y se encolan como reportes
normales, para que el camino de generación sea exactamente el mismo que el de un
reporte pedido a mano.

La evaluación del cron es propia y deliberadamente conservadora: soporta `*`,
números, listas (`1,15`), rangos (`1-5`) y pasos (`*/2`) en los cinco campos
estándar. No soporta nombres (`MON`, `JAN`) ni extensiones de Quartz (`L`, `W`,
`#`, `?`). `POST /reportes/programados` valida con la misma gramática, así que
no se puede guardar una expresión que luego no sepamos evaluar.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Reporte, ReporteProgramado
from .jobs import enqueue

log = logging.getLogger("acredittia.programados")
ZONA_HORARIA = ZoneInfo("America/Santiago")


def _campo_coincide(expr: str, valor: int, minimo: int, maximo: int) -> bool:
    expr = expr.strip()
    if expr in ("*", "?"):
        return True
    for parte in expr.split(","):
        paso = 1
        if "/" in parte:
            parte, _, p = parte.partition("/")
            if not p.isdigit() or int(p) == 0:
                return False
            paso = int(p)
        if parte in ("*", ""):
            desde, hasta = minimo, maximo
        elif "-" in parte:
            a, _, b = parte.partition("-")
            if not (a.isdigit() and b.isdigit()):
                return False
            desde, hasta = int(a), int(b)
        elif parte.isdigit():
            desde = hasta = int(parte)
        else:
            return False
        if desde > hasta or desde < minimo or hasta > maximo:
            return False
        if desde <= valor <= hasta and (valor - desde) % paso == 0:
            return True
    return False


def cron_coincide(expr: str, momento: datetime) -> bool:
    """True si los cinco campos cron corresponden a `momento` en hora de Chile."""
    campos = expr.split()
    if len(campos) != 5:
        return False
    minuto, hora, dia, mes, dow = campos
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=ZONA_HORARIA)
    else:
        momento = momento.astimezone(ZONA_HORARIA)

    # crontab: domingo es 0 y también 7; datetime usa lunes=0
    dow_cron = (momento.weekday() + 1) % 7
    coincide_dia = _campo_coincide(dia, momento.day, 1, 31)
    coincide_dow = (_campo_coincide(dow, dow_cron, 0, 6)
                    or (dow_cron == 0 and _campo_coincide(dow, 7, 0, 7)))
    if dia not in ("*", "?") and dow not in ("*", "?"):
        coincide_dia = coincide_dia or coincide_dow
    else:
        coincide_dia = coincide_dia and coincide_dow
    return (
        _campo_coincide(minuto, momento.minute, 0, 59)
        and _campo_coincide(hora, momento.hour, 0, 23)
        and coincide_dia
        and _campo_coincide(mes, momento.month, 1, 12)
    )


def _mismo_minuto(a: datetime, b: datetime) -> bool:
    if a.tzinfo is None:
        a = a.replace(tzinfo=ZONA_HORARIA)
    if b.tzinfo is None:
        b = b.replace(tzinfo=ZONA_HORARIA)
    return (
        a.astimezone(timezone.utc).replace(second=0, microsecond=0)
        == b.astimezone(timezone.utc).replace(second=0, microsecond=0)
    )


def disparar_pendientes(db: Session, momento: datetime | None = None) -> int:
    """Encola los reportes programados cuyo cron coincide con el minuto actual.

    El beat consulta cada minuto. El antirrebote evita duplicados de ese mismo
    minuto sin impedir expresiones más frecuentes que una vez por hora.
    """
    ahora = momento or datetime.now(ZONA_HORARIA)
    if ahora.tzinfo is None:
        ahora = ahora.replace(tzinfo=ZONA_HORARIA)
    else:
        ahora = ahora.astimezone(ZONA_HORARIA)
    disparados = 0

    for p in db.scalars(
            select(ReporteProgramado).where(ReporteProgramado.activo)
            .with_for_update()):
        if p.ultimo_run_at and _mismo_minuto(p.ultimo_run_at, ahora):
            continue
        if not cron_coincide(p.cron_expr, ahora):
            continue

        reporte = Reporte(
            company_id=p.company_id, nombre=f"{p.nombre} ({ahora:%Y-%m-%d %H:%M})",
            tipo=p.tipo, formato=p.formato, status="queued",
            params={**(p.params or {}), "_programado_id": str(p.id)},
            generado_por=None,        # NULL = "Sistema (Programado)"
        )
        db.add(reporte)
        db.flush()
        p.ultimo_run_at = ahora
        db.commit()

        enqueue("generar_reporte", reporte_id=str(reporte.id),
                company_id=str(p.company_id))
        disparados += 1
        log.info("Reporte programado %s encolado como %s", p.id, reporte.id)

    return disparados
