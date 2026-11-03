"""Sondas de infraestructura y servicios observables (§8.1, ops_heartbeat).

Cada sonda devuelve (estado, metricas):

    estado    'operativo' | 'degradado' | 'caido'
    metricas  dict libre por componente (documentado en §6.1 de la espec.)

Reglas de diseño:

* Una sonda NUNCA lanza: cualquier excepción es 'caido' con el error en las
  métricas. El heartbeat tiene que sobrevivir a lo que sea que esté roto.
* Los umbrales de degradación se aplican AQUÍ (la sonda conoce su métrica);
  el detector de incidentes solo mira estados.
* La API registra conteos y latencias sin rutas ni payloads en una ventana
  acotada; en Celery esas métricas se comparten por Redis entre réplicas.
* Los probes de IA e integraciones describen ejecuciones reales, no lanzan
  llamadas externas ni presentan una integración sin conector como saludable.
"""
from __future__ import annotations

import logging
import math
import threading
import time
import uuid
import urllib.error
import urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select, text

from ..config import settings
from ..config_ops import ops_settings

log = logging.getLogger("acredittia.ops.probes")

API_METRICS_WINDOW_S = 300
API_METRICS_BUCKET_S = 10
API_LATENCY_BUCKETS_MS = (5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000)
API_METRICS_TTL_S = 600
_api_samples: deque[tuple[float, float, int]] = deque(maxlen=10_000)
_api_samples_lock = threading.Lock()
_api_redis_lock = threading.Lock()
_api_redis = None


def _seguro(fn):
    """Envuelve la sonda: excepción => ('caido', {'error': ...})."""
    def dentro(db):
        try:
            return fn(db)
        except Exception as exc:            # noqa: BLE001 — es el contrato
            log.warning("Sonda %s falló: %s", fn.__name__, exc)
            return "caido", {"error": str(exc)[:300]}
    dentro.__name__ = fn.__name__
    return dentro


def _cliente_metricas_api():
    global _api_redis
    if _api_redis is None:
        with _api_redis_lock:
            if _api_redis is None:
                import redis
                _api_redis = redis.Redis.from_url(
                    settings.redis_url, decode_responses=True,
                    socket_connect_timeout=1, socket_timeout=1)
    return _api_redis


# ---------------------------------------------------------------- telemetría API
def registrar_solicitud_api(duracion_ms: float, status_code: int) -> None:
    """Registra una muestra acotada para la sonda, sin guardar rutas ni datos."""
    ahora = time.time()
    if settings.queue_backend != "celery":
        with _api_samples_lock:
            _api_samples.append((ahora, max(0.0, duracion_ms), status_code))
        return

    bucket = int(ahora // API_METRICS_BUCKET_S) * API_METRICS_BUCKET_S
    key = f"ops:api:requests:{bucket}"
    pipe = _cliente_metricas_api().pipeline(transaction=False)
    pipe.hincrby(key, "requests", 1)
    if status_code >= 500:
        pipe.hincrby(key, "errors_5xx", 1)
    duracion = max(0.0, duracion_ms)
    campo = next(
        (f"latency_le_{limite}_ms" for limite in API_LATENCY_BUCKETS_MS
         if duracion <= limite),
        "latency_gt_5000_ms",
    )
    pipe.hincrby(key, campo, 1)
    pipe.expire(key, API_METRICS_TTL_S)
    pipe.execute()


def reset_metricas_api() -> None:
    """Restablece los acumuladores; útil para pruebas y reinicios controlados."""
    global _api_redis
    with _api_samples_lock:
        _api_samples.clear()
    with _api_redis_lock:
        if _api_redis is not None:
            _api_redis.close()
            _api_redis = None


def _resumen_api(ahora: float | None = None) -> dict:
    ahora = time.time() if ahora is None else ahora
    desde = ahora - API_METRICS_WINDOW_S
    if settings.queue_backend != "celery":
        with _api_samples_lock:
            muestras = [x for x in _api_samples if x[0] >= desde]
        latencias = sorted(x[1] for x in muestras)
        objetivo = math.ceil(len(latencias) * 0.95)
        p95 = latencias[objetivo - 1] if objetivo else None
        return {
            "solicitudes_5m": len(muestras),
            "errores_5xx_5m": sum(x[2] >= 500 for x in muestras),
            "latencia_p95_ms": round(p95, 1) if p95 is not None else None,
            "ventana_segundos": API_METRICS_WINDOW_S,
            "metodo_percentil": "muestras en proceso",
        }

    cliente = _cliente_metricas_api()
    primera = int(desde // API_METRICS_BUCKET_S) * API_METRICS_BUCKET_S
    ultima = int(ahora // API_METRICS_BUCKET_S) * API_METRICS_BUCKET_S
    claves = [
        f"ops:api:requests:{ts}"
        for ts in range(primera, ultima + API_METRICS_BUCKET_S,
                       API_METRICS_BUCKET_S)
    ]
    pipe = cliente.pipeline(transaction=False)
    for key in claves:
        pipe.hgetall(key)
    filas = pipe.execute()
    bins = {limite: 0 for limite in API_LATENCY_BUCKETS_MS}
    over = solicitudes = errores = 0
    for fila in filas:
        solicitudes += int(fila.get("requests", 0))
        errores += int(fila.get("errors_5xx", 0))
        for limite in API_LATENCY_BUCKETS_MS:
            bins[limite] += int(fila.get(f"latency_le_{limite}_ms", 0))
        over += int(fila.get("latency_gt_5000_ms", 0))

    objetivo = math.ceil(solicitudes * 0.95)
    acumulado = 0
    p95 = None
    for limite, cantidad in bins.items():
        acumulado += cantidad
        if objetivo and acumulado >= objetivo:
            p95 = limite
            break
    if objetivo and p95 is None and over:
        p95 = 5001
    return {
        "solicitudes_5m": solicitudes,
        "errores_5xx_5m": errores,
        "latencia_p95_ms": p95,
        "ventana_segundos": API_METRICS_WINDOW_S,
        "metodo_percentil": "histograma de latencia; límite superior aproximado",
    }


def _ping_api() -> tuple[str, int | None]:
    url = ops_settings.ops_api_health_url.strip()
    if not url:
        return "no_configurado", None
    inicio = time.monotonic()
    try:
        with urllib.request.urlopen(url, timeout=2) as response:
            if response.status != 200:
                return "fallo", None
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        log.warning("Sonda HTTP de API falló (%s)", type(exc).__name__)
        return "fallo", None
    return "ok", int((time.monotonic() - inicio) * 1000)


# ------------------------------------------------------------------- sondas
@_seguro
def sonda_db(db):
    t0 = time.monotonic()
    db.execute(text("SELECT 1"))
    ping_ms = int((time.monotonic() - t0) * 1000)
    fila = db.execute(text(
        "SELECT count(*) AS activas,"
        "       current_setting('max_connections')::int AS maximo "
        "FROM pg_stat_activity WHERE datname = current_database()")).one()
    version = db.execute(text("SHOW server_version")).scalar_one()
    vector = db.execute(text(
        "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')"
    )).scalar_one()
    estado = "operativo"
    if fila.activas > fila.maximo * 0.85:
        estado = "degradado"
    return estado, {"ping_ms": ping_ms, "conexiones": fila.activas,
                    "conexiones_max": fila.maximo,
                    "version": version, "pgvector_disponible": vector,
                    "detalle": f"{fila.activas}/{fila.maximo} conexiones"}


@_seguro
def sonda_api(db):
    """HTTP liveness (si se configura) y latencia/error rate observados."""
    resumen = _resumen_api()
    salud_http, ping_ms = _ping_api()
    p95 = resumen["latencia_p95_ms"]
    solicitudes = resumen["solicitudes_5m"]
    errores = resumen["errores_5xx_5m"]
    tasa_error = round(100 * errores / solicitudes, 2) if solicitudes else None
    metricas = {
        "latencia_p95_ms": p95,
        "tasa_error_5xx_pct": tasa_error,
        "solicitudes_5m": solicitudes,
        "errores_5xx_5m": errores,
        "verificacion_http": salud_http,
        "healthcheck_ms": ping_ms,
        "ventana_segundos": resumen["ventana_segundos"],
        "metodo_percentil": resumen["metodo_percentil"],
        "estado_datos": "disponible" if solicitudes else "sin_trafico",
    }
    estado = "operativo"
    if salud_http == "fallo":
        estado = "caido"
        metricas["detalle"] = "La API no respondió al health check HTTP"
    elif p95 is not None and p95 > ops_settings.ops_umbral_p95_ms:
        estado = "degradado"
        metricas["detalle"] = f"p95 {p95} ms > umbral {ops_settings.ops_umbral_p95_ms} ms"
    elif solicitudes >= 20 and tasa_error is not None and tasa_error >= 5:
        estado = "degradado"
        metricas["detalle"] = (
            f"{errores}/{solicitudes} respuestas 5xx en los últimos 5 minutos")
    elif salud_http == "no_configurado" and not solicitudes:
        estado = "degradado"
        metricas["detalle"] = (
            "Sin tráfico medido ni OPS_API_HEALTH_URL; disponibilidad no verificada")
    return estado, metricas


@_seguro
def sonda_workers(db):
    """Comprueba Redis, workers Celery vivos, colas y tareas activas."""
    if settings.queue_backend != "celery":
        return "operativo", {
            "modo": "inproc", "workers_celery_activos": 0,
            "tareas_en_cola": None,
            "detalle": "La ejecución ocurre en proceso; Redis/Celery no aplica",
        }

    import redis
    from celery import Celery

    r = redis.Redis.from_url(
        settings.redis_url, socket_connect_timeout=1, socket_timeout=1)
    inicio = time.monotonic()
    r.ping()
    redis_ping_ms = int((time.monotonic() - inicio) * 1000)

    celery_app = Celery("acredittia-ops-health", broker=settings.redis_url)
    try:
        inspector = celery_app.control.inspect(timeout=1)
        pongs = inspector.ping() or {}
        colas_por_worker = inspector.active_queues()
        activas_por_worker = inspector.active()
        nombres_colas = sorted({
            cola["name"]
            for colas in (colas_por_worker or {}).values()
            for cola in colas
            if cola.get("name")
        })
        profundidad_colas = {
            nombre: int(r.llen(nombre) or 0) for nombre in nombres_colas
        }
    finally:
        celery_app.close()
        r.close()

    workers = sorted(pongs)
    metricas = {
        "modo": "celery",
        "redis_ping_ms": redis_ping_ms,
        "workers_activos": len(workers),
        "workers": workers,
        "tareas_ejecutandose": sum(
            len(tareas) for tareas in (activas_por_worker or {}).values()),
        "colas": profundidad_colas,
    }

    estado = "operativo"
    if not workers:
        estado = "caido"
        metricas["detalle"] = "Redis responde, pero no hay workers Celery activos"
    elif not nombres_colas:
        estado = "degradado"
        metricas["detalle"] = "Workers activos, pero no se pudieron consultar sus colas"
    elif sum(metricas["colas"].values()) > ops_settings.ops_umbral_cola:
        estado = "degradado"
        metricas["detalle"] = (
            f"{sum(metricas['colas'].values())} tareas en cola > "
            f"umbral {ops_settings.ops_umbral_cola}")
    return estado, metricas


@_seguro
def sonda_storage(db):
    """Verifica Storage sin generar operaciones sintéticas de pago en Azure."""
    if settings.storage_backend == "azure":
        return "degradado", {
            "backend": "azure",
            "estado_datos": "no_verificado",
            "detalle": (
                "No se realizan operaciones canario de Azure Blob para evitar "
                "transacciones facturables; disponibilidad no verificada"
            ),
        }

    from .storage import get_storage
    st = get_storage()
    ruta = f"ops/_canario_{uuid.uuid4().hex}.txt"
    contenido = uuid.uuid4().hex.encode()
    metricas = {"backend": settings.storage_backend}

    inicio = time.monotonic()
    try:
        st.save(ruta, contenido)
        metricas["escritura_ms"] = int((time.monotonic() - inicio) * 1000)
        inicio = time.monotonic()
        if st.read(ruta) != contenido:
            raise RuntimeError("Storage devolvió contenido distinto al escrito")
        metricas["lectura_ms"] = int((time.monotonic() - inicio) * 1000)
    finally:
        inicio = time.monotonic()
        st.delete(ruta)
        metricas["eliminacion_ms"] = int((time.monotonic() - inicio) * 1000)
        if st.exists(ruta):
            raise RuntimeError("El objeto canario de Storage no se pudo eliminar")
    return "operativo", metricas


@_seguro
def sonda_ia(db):
    """Volumen, errores y latencia p95 de ejecuciones IA de los últimos 7 días."""
    from ..models import IaReview

    corte = datetime.now(timezone.utc) - timedelta(days=7)
    total = db.scalar(select(func.count()).select_from(IaReview)
                      .where(IaReview.created_at >= corte)) or 0
    fallidos = db.scalar(select(func.count()).select_from(IaReview)
                         .where(IaReview.created_at >= corte,
                                IaReview.status == "failed")) or 0
    en_cola = db.scalar(select(func.count()).select_from(IaReview)
                           .where(IaReview.created_at >= corte,
                                  IaReview.status.in_(("queued", "processing")))) or 0
    duracion_ms = (
        func.extract("epoch", IaReview.finished_at - IaReview.started_at) * 1000)
    latencia_p95 = db.scalar(
        select(func.percentile_cont(0.95).within_group(duracion_ms))
        .where(IaReview.created_at >= corte, IaReview.status == "done",
               IaReview.started_at.is_not(None),
               IaReview.finished_at.is_not(None)))

    backend_real = settings.ia_backend == "claude" and bool(settings.anthropic_api_key)
    metricas = {
        "backend": "claude" if backend_real else "simulada",
        "revisiones_7d": total,
        "completadas_7d": total - fallidos - en_cola,
        "fallidas_7d": fallidos,
        "en_cola": en_cola,
        "tasa_fallo_pct": round(100 * fallidos / total, 2) if total else None,
        "latencia_p95_ms": round(float(latencia_p95), 1)
        if latencia_p95 is not None else None,
        "estado_datos": "disponible" if total else "sin_ejecuciones",
        "verificacion_externa": False,
    }
    if not backend_real:
        metricas["detalle"] = (
            "El backend IA está simulado; estas métricas no representan un proveedor SaaS")
        return "degradado", metricas
    if total >= 20 and fallidos / total > 0.10:
        metricas["detalle"] = f"{fallidos}/{total} revisiones fallidas en 7 días"
        return "degradado", metricas
    return "operativo", metricas


@_seguro
def sonda_integraciones(db):
    """Estado declarado e historial real de sincronizaciones por tipo."""
    from ..models import Integracion, SyncLog
    from .integraciones import CONECTORES

    filas = db.execute(select(Integracion.tipo, Integracion.estado)).all()
    estados = {"activa": 0, "con_error": 0, "desconectada": 0}
    for _, estado_integracion in filas:
        estados[str(estado_integracion)] = estados.get(str(estado_integracion), 0) + 1

    corte = datetime.now(timezone.utc) - timedelta(days=7)
    duracion_ms = (
        func.extract("epoch", SyncLog.finished_at - SyncLog.started_at) * 1000)
    resumen = db.execute(
        select(
            Integracion.tipo,
            func.count(SyncLog.id).label("total"),
            func.count(SyncLog.id).filter(SyncLog.status == "exito").label("exitos"),
            func.count(SyncLog.id).filter(SyncLog.status == "error").label("errores"),
            func.percentile_cont(0.95).within_group(duracion_ms).label("p95"),
            func.max(SyncLog.finished_at).label("ultima_ejecucion_at"),
        )
        .join(SyncLog, SyncLog.integracion_id == Integracion.id)
        .where(SyncLog.started_at >= corte)
        .group_by(Integracion.tipo)
    ).all()
    p95_global = db.scalar(
        select(func.percentile_cont(0.95).within_group(duracion_ms))
        .select_from(SyncLog)
        .where(SyncLog.started_at >= corte))
    conectores = {
        tipo: bool(getattr(clase, "IMPLEMENTADO", False))
        for tipo, clase in CONECTORES.items()
    }
    metricas_por_tipo = {
        str(tipo): {
            "ejecuciones_7d": total,
            "exitos_7d": exitos,
            "errores_7d": errores,
            "tasa_error_pct": round(100 * errores / total, 2) if total else None,
            "latencia_p95_ms": round(float(p95), 1) if p95 is not None else None,
            "ultima_ejecucion_at": ultima.isoformat() if ultima else None,
            "conector_implementado": conectores.get(str(tipo), False),
        }
        for tipo, total, exitos, errores, p95, ultima in resumen
    }
    tipos_activos = {
        str(tipo) for tipo, estado_integracion in filas
        if estado_integracion in ("activa", "con_error")
    }
    pendientes = sorted(tipo for tipo in tipos_activos
                       if not conectores.get(tipo, False))
    ejecuciones = sum(x["ejecuciones_7d"] for x in metricas_por_tipo.values())
    exitos = sum(x["exitos_7d"] for x in metricas_por_tipo.values())
    errores = sum(x["errores_7d"] for x in metricas_por_tipo.values())
    metricas = {
        "latencia_p95_ms": round(float(p95_global), 1)
        if p95_global is not None else None,
        "tasa_error_pct": round(100 * errores / ejecuciones, 2)
        if ejecuciones else None,
        "ejecuciones_7d": ejecuciones,
        "errores_7d": errores,
        "integraciones_activas": estados["activa"],
        "integraciones_con_error": estados["con_error"],
        "integraciones_desconectadas": estados["desconectada"],
        "conectores_implementados": sum(conectores.values()),
        "conectividad_externa_verificada": False,
        "exitos_7d": exitos,
        "por_tipo": metricas_por_tipo,
    }
    if pendientes:
        metricas["conectores_pendientes"] = pendientes
        metricas["detalle"] = (
            "Hay integraciones activas sin conector implementado: "
            + ", ".join(pendientes))
        return "degradado", metricas
    if estados["con_error"]:
        metricas["detalle"] = (
            f"{estados['con_error']} integraciones están marcadas con error")
        return "degradado", metricas
    return "operativo", metricas


SONDAS = {
    "api": sonda_api,
    "db": sonda_db,
    "workers": sonda_workers,
    "storage": sonda_storage,
    "ia": sonda_ia,
    "integraciones": sonda_integraciones,
}
