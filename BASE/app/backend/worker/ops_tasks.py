"""Tareas de fondo de la consola interna (§8) y registro de runners.

Importar este módulo (lo hacen `main.py` y `worker/celery_app.py`):

1. registra en `TAREAS` la entrada 'ops_ejecutar_run' que usa el endpoint
   POST /api/v1/admin/procesos/{clave}/ejecutar, con lo que funciona igual con
   Celery y con QUEUE_BACKEND=inproc;
2. puebla `OPS_RUNNERS` con la función de cada clave de ops_jobs, de modo que
   una ejecución manual y una por cron corren exactamente el mismo código.

Para Celery, `registrar_ops(celery)` añade las tareas y su beat schedule; en
`worker/celery_app.py` basta con:

    from worker.ops_tasks import registrar_ops
    registrar_ops(celery)
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text

from app.config_ops import COMPONENTES
from app.services import ops
from app.services.jobs import tarea
from app.services.ops_probes import SONDAS

log = logging.getLogger("acredittia.ops.tasks")

OPS_CRON_SCHEDULES = {
    "vencimientos": "30 0 * * *",
    "reportes_programados": "* * * * *",
    "purga_temporales": "0 4 * * *",
    "ops_disponibilidad": "5 0 * * *",
    "metricas_snapshot": "10 2 * * *",
    "ops_retencion": "30 3 * * 0",
    "admin_backup": "0 2 * * 0",
}


# ============================================================================
# Entrada de la cola para ejecuciones manuales (§6.5)
# ============================================================================
@tarea("ops_ejecutar_run")
def ops_ejecutar_run(run_id: int) -> None:
    ops.ejecutar_run(int(run_id))


# ============================================================================
# Runners de los jobs de ops_jobs (§8). Cada uno recibe la sesión is_admin
# del ciclo de vida del run y devuelve (items_procesados, mensaje).
# ============================================================================
@ops.runner("ops_heartbeat")
def run_heartbeat(db, _progress=None, **_):
    """Sondea los componentes, guarda los latidos y evalúa incidentes."""
    total = len(COMPONENTES)
    for indice, componente in enumerate(COMPONENTES, start=1):
        estado, metricas = SONDAS[componente](db)
        ops.guardar_latido(componente, estado, metricas)
        ops.evaluar_incidentes(db, componente)
        if _progress:
            _progress(round(indice * 100 / total),
                      f"Componente {indice} de {total}: {componente}")
    db.commit()
    return len(COMPONENTES), f"{len(COMPONENTES)} componentes sondeados"


@ops.runner("ops_disponibilidad")
def run_disponibilidad(db, fecha: str | None = None, _progress=None, **_):
    """Consolida los latidos del día ANTERIOR en ops_disponibilidad_diaria.

    Con params {"fecha": "YYYY-MM-DD"} consolida ese día (re-cálculo manual).
    Los latidos viven 24 h en la historia del store, así que el job debe
    correr a primera hora (beat: 00:05).
    """
    objetivo = (date.fromisoformat(fecha) if fecha
                else date.today() - timedelta(days=1))
    n = 0
    total = len(COMPONENTES)
    for indice, componente in enumerate(COMPONENTES, start=1):
        latidos = [h for h in ops.historia_latidos(componente, 1440)
                   if datetime.fromisoformat(h["ts"]).date() == objetivo]
        if latidos:
            checks = len(latidos)
            caidos = sum(1 for x in latidos if x["estado"] == "caido")
            peor = max(latidos, key=lambda x: ops.PESO_ESTADO[x["estado"]])["estado"]
            p95s = sorted(x["metricas"].get("latencia_p95_ms") for x in latidos
                          if x["metricas"].get("latencia_p95_ms") is not None)
            db.execute(text(
                "SELECT ops_upsert_disponibilidad("
                "CAST(:c AS text), CAST(:f AS date), "
                "CAST(:e AS ops_comp_estado), CAST(:u AS numeric), "
                "CAST(:p AS integer), CAST(:t AS integer), CAST(:x AS integer))"), {
                "c": componente, "f": objetivo, "e": peor,
                "u": round(100.0 * (checks - caidos) / checks, 2),
                "p": p95s[int(len(p95s) * 0.95) - 1] if p95s else None,
                "t": checks, "x": caidos,
            })
            n += 1
        if _progress:
            _progress(round(indice * 100 / total),
                      f"Componente {indice} de {total}: {componente}")
    db.commit()
    return n, f"Disponibilidad de {objetivo.isoformat()} consolidada ({n} componentes)"


@ops.runner("metricas_snapshot")
def run_metricas_snapshot(db, mes: str | None = None, forzar: bool = False,
                          _progress=None, **_):
    """Snapshot del mes en curso; el día 1 consolida además el mes anterior.

    Con params {"mes": "YYYY-MM"} recalcula ese mes (forzar=true si estaba
    cerrado; queda auditado porque la ejecución manual registra actor).
    """
    uf = db.execute(text(
        "SELECT valor_uf FROM ops_ajustes_negocio WHERE id = true"
    )).scalar_one()
    if mes:
        objetivo = date(int(mes[:4]), int(mes[5:7]), 1)
        if _progress:
            _progress(10, f"Preparando snapshot de {mes}")
        db.execute(text(
            # ops_valor_uf llega desde Python como float; la función SQL exige numeric.
            "SELECT ops_snapshot_metricas(:m, CAST(:uf AS NUMERIC), true, :fz)"),
            {"m": objetivo, "uf": uf, "fz": forzar})
        db.commit()
        if _progress:
            _progress(90, f"Snapshot de {mes} calculado")
        return 1, f"Snapshot de {mes} recalculado"

    hoy = date.today()
    n = 0
    if hoy.day == 1:
        if _progress:
            _progress(10, "Consolidando el mes anterior")
        anterior = (hoy - timedelta(days=1)).replace(day=1)
        db.execute(text(
            # El casteo evita que psycopg envíe la UF como double precision.
            "SELECT ops_snapshot_metricas(:m, CAST(:uf AS NUMERIC), true, false)"),
                   {"m": anterior, "uf": uf})
        n += 1
    if _progress:
        _progress(50 if hoy.day == 1 else 10, "Calculando snapshot del mes actual")
    db.execute(text(
        # Mantener el mismo tipo numeric en el snapshot del mes en curso.
        "SELECT ops_snapshot_metricas(:m, CAST(:uf AS NUMERIC), false, false)"),
               {"m": hoy.replace(day=1), "uf": uf})
    db.commit()
    if _progress:
        _progress(90, "Snapshot mensual guardado")
    return n + 1, f"Snapshot del mes en curso actualizado (UF {uf})"


@ops.runner("ops_retencion")
def run_retencion(db, _progress=None, **_):
    if _progress:
        _progress(10, "Aplicando política de retención")
    fila = db.execute(text("SELECT * FROM ops_podar_privacidad()")).one()
    actividad = db.execute(
        text("SELECT * FROM ops_podar_telemetria_actividad()")).one()
    db.commit()
    if _progress:
        _progress(90, "Consolidando resultados de retención")
    total = sum((fila.actividad_podada, fila.bitacora_podada,
                 fila.runs_podados, fila.incidentes_podados,
                 fila.disponibilidad_podada, fila.metricas_podadas,
                 actividad.sesiones_podadas,
                 actividad.agregados_usuario_podados,
                 actividad.agregados_empresa_podados))
    return int(total), (
        f"actividad={fila.actividad_podada}, bitácora={fila.bitacora_podada}, "
        f"runs={fila.runs_podados}, incidentes={fila.incidentes_podados}, "
        f"disponibilidad={fila.disponibilidad_podada}, métricas={fila.metricas_podadas}; "
        f"telemetría_sesiones={actividad.sesiones_podadas}, "
        f"telemetría_usuarios={actividad.agregados_usuario_podados}, "
        f"telemetría_empresas={actividad.agregados_empresa_podados}; "
        f"{fila.runs_timeout} runs marcados timeout")


# --- Jobs de negocio existentes, expuestos en la consola --------------------
@ops.runner("vencimientos")
def run_vencimientos(db, _progress=None, **_):
    """Mismo trabajo que acredittia.cron_diario, expuesto y reintetable."""
    from app.services.vencimientos import (escribir_snapshots,
                                           expirar_credenciales,
                                           recalcular_documentos)
    docs = recalcular_documentos(db)
    if _progress:
        _progress(33, "Documentos recalculados")
    snaps = escribir_snapshots(db)
    if _progress:
        _progress(66, "Snapshots de cumplimiento guardados")
    creds = expirar_credenciales(db)
    db.commit()
    if _progress:
        _progress(90, "Credenciales expiradas y cambios guardados")
    return docs, (f"{docs} documentos recalculados, {snaps} snapshots, "
                  f"{creds} credenciales expiradas")


@ops.runner("reportes_programados")
def run_reportes_programados(db, _progress=None, **_):
    from app.services.programados import disparar_pendientes
    n = disparar_pendientes(db, progreso=_progress)
    db.commit()
    return n, f"{n} reportes programados disparados"


@ops.runner("purga_temporales")
def run_purga_temporales(db, _progress=None, **_):
    from app.services.tasks import purgar_temporales
    if _progress:
        _progress(10, "Buscando archivos temporales vencidos")
    n = purgar_temporales()
    if _progress:
        _progress(90, f"Purga completada: {n} archivos eliminados")
    return n, f"{n} blobs temporales purgados"


@ops.runner("admin_backup")
def run_admin_backup(db, _progress=None, **_):
    """Genera y cifra el respaldo PostgreSQL + Storage local."""
    from app.services.backups import create_backup

    backup = create_backup(reason="programado", progreso=_progress)
    return 1, (f"Respaldo {backup['id']} creado; "
               f"{backup['files']} archivos incluidos")


# ============================================================================
# Celery: tareas + beat (§8). Los ticks pasan por disparar_por_cron(), que
# respeta la pausa (ops_jobs.activo) y evita corridas solapadas.
# ============================================================================
def registrar_ops(celery) -> None:
    from celery.schedules import crontab

    @celery.task(name="acredittia.ops_tick")
    def ops_tick(clave: str):
        rid = ops.disparar_por_cron(clave)
        return {"job": clave, "run_id": rid}

    schedules = {
        "ops-heartbeat": {
            "task": "acredittia.ops_tick",
            "schedule": 60.0,                       # cada minuto
            "args": ("ops_heartbeat",),
        }
    }
    for clave, expresion in OPS_CRON_SCHEDULES.items():
        minuto, hora, dia, mes, dia_semana = expresion.split()
        schedules[f"ops-{clave}"] = {
            "task": "acredittia.ops_tick",
            "schedule": crontab(
                minute=minuto, hour=hora, day_of_month=dia,
                month_of_year=mes, day_of_week=dia_semana),
            "args": (clave,),
        }
    celery.conf.beat_schedule.update(schedules)
    log.info("Tareas de la consola interna registradas en Celery")


def registrar_scheduler_local(scheduler) -> None:
    """Registra los mismos procesos en APScheduler para el modo inproc local."""
    from apscheduler.triggers.cron import CronTrigger

    scheduler.add_job(
        ops.disparar_por_cron, "interval", seconds=60,
        args=("ops_heartbeat",), id="ops-ops_heartbeat",
        replace_existing=True)
    for clave, expresion in OPS_CRON_SCHEDULES.items():
        trigger = CronTrigger.from_crontab(
            expresion, timezone=scheduler.timezone)
        scheduler.add_job(
            ops.disparar_por_cron, trigger=trigger, args=(clave,),
            id=f"ops-{clave}", replace_existing=True)
