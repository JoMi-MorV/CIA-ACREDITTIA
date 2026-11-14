"""Consola interna /admin/ops (Especificación Consola Interna v1.0).

Requiere que 07_consola_interna.sql y 08_funciones_consola.sql estén en la
lista SCRIPTS de tests/conftest.py (ver README de codigo_administracion).

Con QUEUE_BACKEND=inproc las ejecuciones manuales corren en el acto, así que
el run ya está cerrado ('ok'/'error') en la aserción siguiente al 202 — el
mismo patrón que usa test_reportes.py.
"""
from __future__ import annotations

import json
import uuid
from datetime import date, datetime, timedelta, timezone
from threading import Event, Thread

import pytest

from app.database import worker_session
from app.models import Company, Documento
from tests.conftest import API

ENVOLTURA = {"items", "page", "page_size", "total", "total_pages"}
COMPONENTES = {"api", "db", "workers", "storage", "ia", "integraciones"}


# ============================================================================
# Fixtures propias
# ============================================================================
@pytest.fixture
def plan_pro(motor_admin):
    """Plan comercial + retorno del id. Directo a BD: el CRUD de planes
    (spec v1.1 §6) no es prerrequisito de esta suite."""
    from sqlalchemy import text
    with motor_admin.connect() as c:
        pid = c.execute(text(
            "INSERT INTO planes (nombre, precio, moneda, periodo) "
            "VALUES ('Pro', 12.5, 'UF', 'mensual') "
            "ON CONFLICT (nombre) DO UPDATE SET precio = EXCLUDED.precio "
            "RETURNING id")).scalar()
        c.commit()
    return str(pid)


@pytest.fixture
def suscripcion_a(motor_admin, empresa_a, plan_pro):
    """empresa_a con suscripción activa al plan Pro y su industria fijada."""
    from sqlalchemy import text
    with motor_admin.connect() as c:
        c.execute(text(
            "UPDATE companies SET industria = 'mineria' WHERE id = :cid"),
            {"cid": empresa_a["company_id"]})
        sid = c.execute(text(
            "INSERT INTO suscripciones (company_id, plan_id, estado) "
            "VALUES (:cid, :pid, 'activa') RETURNING id"),
            {"cid": empresa_a["company_id"], "pid": plan_pro}).scalar()
        c.commit()
    return str(sid)


def _run_ok(cliente, admin, clave: str, params: dict | None = None) -> dict:
    """Ejecuta un proceso por la API y asevera que terminó ok (inproc)."""
    r = cliente.post(f"{API}/admin/ops/procesos/{clave}/ejecutar",
                     headers=admin["headers"],
                     json={"params": params or {}})
    assert r.status_code == 202, r.text
    rid = r.json()["run_id"]
    r = cliente.get(f"{API}/admin/ops/procesos/{clave}/ejecuciones",
                    headers=admin["headers"])
    run = next(x for x in r.json()["items"] if x["run_id"] == rid)
    assert run["status"] == "ok", run
    return run


# ============================================================================
# Autorización
# ============================================================================
def test_todo_el_router_exige_admin(app_cliente, empresa_a):
    for ruta in ("usuarios/resumen", "sistemas/estado", "procesos",
                 "indicadores/resumen"):
        r = app_cliente.get(f"{API}/admin/ops/{ruta}",
                            headers=empresa_a["headers"])
        assert r.status_code == 403, ruta
        assert r.json()["error"]["code"] == "SOLO_ADMIN"


def test_sin_token(app_cliente):
    r = app_cliente.get(f"{API}/admin/ops/usuarios/resumen")
    assert r.status_code == 401


def test_stats_incluye_empresa_aprobada_sin_usuarios(app_cliente, admin):
    with worker_session(is_admin=True) as db:
        company = Company(nombre="Empresa sin usuarios", rut="71.234.567-8",
                          email="sin-usuarios@empresa.cl", status="approved")
        db.add(company)
        db.commit()
        company_id = str(company.id)

    respuesta = app_cliente.get(f"{API}/admin/stats", headers=admin["headers"])
    assert respuesta.status_code == 200, respuesta.text
    item = next(x for x in respuesta.json()["actividad_global"]["clientes_baja_actividad"]
                if x["company_id"] == company_id)
    assert item["usuarios"] == 0
    assert item["usuarios_activos"] == 0
    assert item["actividad_pct"] == 0


def test_stats_documentos_usan_mismo_universo_aprobado(
        app_cliente, admin, empresa_a, contrato_a):
    def obtener_stats():
        respuesta = app_cliente.get(f"{API}/admin/stats",
                                    headers=admin["headers"])
        assert respuesta.status_code == 200, respuesta.text
        return respuesta.json()

    inicial = obtener_stats()
    estados = ("ok", "falta", "porvenc", "venc")
    with worker_session(is_admin=True) as db:
        db.add_all([
            Documento(
                company_id=empresa_a["company_id"],
                contrato_id=contrato_a["id"],
                titulo=f"Documento de prueba {estado}",
                estado="ok" if estado == "ok" else "falta",
                estado_calc=estado,
            )
            for estado in estados
        ])
        db.add_all([
            Documento(
                company_id=empresa_a["company_id"],
                contrato_id=contrato_a["id"],
                titulo="Documento opcional",
                obligatorio=False,
            ),
            Documento(
                company_id=empresa_a["company_id"],
                contrato_id=contrato_a["id"],
                titulo="Documento EMSIPOR",
                es_emsipor=True,
            ),
        ])
        db.commit()

    aprobado = obtener_stats()
    assert aprobado["documentos_total"] == inicial["documentos_total"] + 4
    assert aprobado["documentos_ok"] == inicial["documentos_ok"] + 1
    assert aprobado["documentos"] == {
        "total": inicial["documentos"]["total"] + 4,
        "ok": inicial["documentos"]["ok"] + 1,
        "pendientes": inicial["documentos"]["pendientes"] + 1,
        "por_vencer": inicial["documentos"]["por_vencer"] + 1,
        "vencidos": inicial["documentos"]["vencidos"] + 1,
    }
    assert aprobado["cumplimiento_global_pct"] == round(
        100 * aprobado["documentos_ok"] / aprobado["documentos_total"])

    with worker_session(is_admin=True) as db:
        company = db.get(Company, empresa_a["company_id"])
        assert company is not None
        company.status = "pending"
        db.commit()

    sin_empresas_aprobadas = obtener_stats()
    assert sin_empresas_aprobadas["empresas_total"] == aprobado["empresas_total"]
    assert sin_empresas_aprobadas["aprobadas"] == 0
    assert sin_empresas_aprobadas["contratos_total"] == aprobado["contratos_total"]
    assert sin_empresas_aprobadas["documentos_total"] == 0
    assert sin_empresas_aprobadas["documentos_ok"] == 0
    assert sin_empresas_aprobadas["documentos"] == {
        "total": 0,
        "ok": 0,
        "pendientes": 0,
        "por_vencer": 0,
        "vencidos": 0,
    }
    assert sin_empresas_aprobadas["cumplimiento_promedio"] is None
    assert sin_empresas_aprobadas["cumplimiento_global_pct"] is None


# ============================================================================
# §5 — Usuarios
# ============================================================================
def test_usuarios_resumen(app_cliente, admin, empresa_a, empresa_b):
    r = app_cliente.get(f"{API}/admin/ops/usuarios/resumen",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    u = d["usuarios"]
    # Los fixtures crean un usuario por empresa y ambos hicieron login.
    assert u["totales"] >= 2
    assert u["activos"]["n"] + u["inactivos"]["n"] == u["totales"]
    # El admin de plataforma no cuenta como usuario.
    assert d["ventana_dias"] == 30
    assert d["serie_12m"][-1]["usuarios_totales"] == u["totales"]


def test_usuarios_resumen_ventana_invalida(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/ops/usuarios/resumen?ventana_dias=5",
                        headers=admin["headers"])
    assert r.status_code == 422        # validación FastAPI (ge=7)


def test_por_plan_y_sin_plan(app_cliente, admin, empresa_a, empresa_b,
                             suscripcion_a):
    r = app_cliente.get(f"{API}/admin/ops/usuarios/por-plan",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    pro = next(x for x in d["items"] if x["plan"] == "Pro")
    assert pro["clientes"] == 1
    assert pro["usuarios"] >= 1
    assert pro["activos"] + pro["inactivos"] == pro["usuarios"]
    # empresa_b no tiene suscripción: cae en sin_plan.
    assert d["sin_plan"]["clientes"] >= 1


def test_por_industria_categorias_estables(app_cliente, admin, empresa_a,
                                           suscripcion_a):
    r = app_cliente.get(f"{API}/admin/ops/usuarios/por-industria",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert {x["industria"] for x in d["items"]} == {
        "mineria", "construccion", "energia", "industrial", "otras"}
    mineria = next(x for x in d["items"] if x["industria"] == "mineria")
    assert mineria["usuarios"] >= 1
    if d["total"]:
        assert round(sum(x["pct"] for x in d["items"]), 1) == 100.0


def test_clientes_tabla_y_filtros(app_cliente, admin, empresa_a, empresa_b,
                                  suscripcion_a):
    r = app_cliente.get(f"{API}/admin/ops/clientes", headers=admin["headers"])
    assert r.status_code == 200 and set(r.json()) == ENVOLTURA
    assert r.json()["total"] >= 2

    r = app_cliente.get(f"{API}/admin/ops/clientes?industria=mineria",
                        headers=admin["headers"])
    assert {x["industria"] for x in r.json()["items"]} == {"mineria"}

    r = app_cliente.get(f"{API}/admin/ops/clientes?plan_id=sin_plan",
                        headers=admin["headers"])
    assert all(x["plan"] is None for x in r.json()["items"])

    nombre = None
    r = app_cliente.get(f"{API}/admin/ops/clientes", headers=admin["headers"])
    nombre = r.json()["items"][0]["nombre"]
    r = app_cliente.get(f"{API}/admin/ops/clientes?search={nombre[:8]}",
                        headers=admin["headers"])
    assert any(x["nombre"] == nombre for x in r.json()["items"])

    # Sin facturas vencidas: todos al día.
    assert all(x["estado_cuenta"] == "al_dia" for x in r.json()["items"])

    r = app_cliente.get(f"{API}/admin/ops/clientes?industria=agro",
                        headers=admin["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "RANGO_INVALIDO"


def test_cliente_detalle_y_404(app_cliente, admin, empresa_a, suscripcion_a):
    r = app_cliente.get(f"{API}/admin/ops/clientes/{empresa_a['company_id']}",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["suscripcion"]["plan"] == "Pro"
    assert d["suscripcion"]["mrr_clp"] > 0          # 12,5 UF convertidas a CLP
    assert d["facturacion"]["estado_cuenta"] == "al_dia"

    r = app_cliente.get(f"{API}/admin/ops/clientes/{uuid.uuid4()}",
                        headers=admin["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NO_ENCONTRADO"


# ============================================================================
# §6 — Sistemas y procesos
# ============================================================================
def test_estado_ciego_luego_operativo(app_cliente, admin):
    from app.services import ops as svc_ops
    svc_ops.reset_store()          # monitor sin latidos: peor caso

    r = app_cliente.get(f"{API}/admin/ops/sistemas/estado",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert {c["clave"] for c in d["componentes"]} == COMPONENTES
    assert d["estado_global"] == "caido"           # ciego = caído
    assert all(c["impacto"]["alcance"] == "indeterminado"
               and c["impacto"]["empresas_afectadas"] == []
               for c in d["componentes"])

    _run_ok(app_cliente, admin, "ops_heartbeat")
    r = app_cliente.get(f"{API}/admin/ops/sistemas/estado",
                        headers=admin["headers"])
    d = r.json()
    assert d["estado_global"] == "degradado", d
    componentes = {c["clave"]: c for c in d["componentes"]}
    assert componentes["db"]["metricas"]["conexiones"] >= 1
    assert componentes["db"]["metricas"]["version"]
    assert componentes["api"]["metricas"]["solicitudes_5m"] > 0
    assert componentes["workers"]["metricas"]["modo"] == "inproc"
    assert componentes["ia"]["estado"] == "degradado"
    assert componentes["ia"]["metricas"]["backend"] == "simulada"
    assert all(c["impacto"]["empresas_afectadas"] == []
               for c in componentes.values())


def test_heartbeat_expirado_se_clasifica_como_caido(monkeypatch):
    from app.services import ops

    store = ops._MemStore()
    monkeypatch.setattr(ops, "_store", store)
    ts = datetime.now(timezone.utc) - timedelta(
        seconds=ops.ops_settings.ops_heartbeat_ttl_s + 1)
    store.set(ops._k("api"), json.dumps({
        "estado": "operativo", "metricas": {"ping_ms": 1},
        "ts": ts.isoformat(),
    }))

    assert ops.estado_componente("api") == ("caido", None, None)

    ops.guardar_latido("api", "operativo", {"ping_ms": 2})
    estado, metricas, desde = ops.estado_componente("api")
    assert estado == "operativo"
    assert metricas == {"ping_ms": 2}
    assert desde is not None


def test_sonda_api_mide_latencia_y_respuestas_5xx(monkeypatch):
    from app.services import ops_probes

    ops_probes.reset_metricas_api()
    monkeypatch.setattr(ops_probes.settings, "queue_backend", "inproc")
    monkeypatch.setattr(ops_probes.ops_settings, "ops_api_health_url", "")
    for duracion in range(1, 21):
        ops_probes.registrar_solicitud_api(
            duracion, 500 if duracion == 20 else 200)

    estado, metricas = ops_probes.sonda_api(None)
    assert estado == "degradado"
    assert metricas["solicitudes_5m"] == 20
    assert metricas["errores_5xx_5m"] == 1
    assert metricas["tasa_error_5xx_pct"] == 5
    assert metricas["latencia_p95_ms"] == 19
    ops_probes.reset_metricas_api()


def test_sonda_api_inaccesible_se_clasifica_como_caida(monkeypatch):
    from app.services import ops_probes

    monkeypatch.setattr(
        ops_probes.ops_settings, "ops_api_health_url",
        "http://api.test/health")
    monkeypatch.setattr(ops_probes, "_resumen_api", lambda: {
        "solicitudes_5m": 0, "errores_5xx_5m": 0,
        "latencia_p95_ms": None, "ventana_segundos": 300,
        "metodo_percentil": "sin muestras",
    })

    def api_inaccesible(*args, **kwargs):
        raise ops_probes.urllib.error.URLError("sin conexión")

    monkeypatch.setattr(
        ops_probes.urllib.request, "urlopen", api_inaccesible)
    estado, metricas = ops_probes.sonda_api(None)

    assert estado == "caido"
    assert metricas["verificacion_http"] == "fallo"
    assert metricas["detalle"] == "La API no respondió al health check HTTP"


def test_sonda_api_aplica_umbral_p95(monkeypatch):
    from app.services import ops_probes

    monkeypatch.setattr(ops_probes.settings, "queue_backend", "inproc")
    monkeypatch.setattr(ops_probes.ops_settings, "ops_api_health_url", "")
    monkeypatch.setattr(
        ops_probes.ops_settings, "ops_umbral_p95_ms", 800)
    ops_probes.reset_metricas_api()
    ops_probes.registrar_solicitud_api(800, 200)
    assert ops_probes.sonda_api(None)[0] == "operativo"

    ops_probes.reset_metricas_api()
    ops_probes.registrar_solicitud_api(801, 200)
    estado, metricas = ops_probes.sonda_api(None)
    assert estado == "degradado"
    assert metricas["latencia_p95_ms"] == 801
    ops_probes.reset_metricas_api()


def test_sonda_workers_detecta_redis_caido(monkeypatch):
    import redis

    from app.services import ops_probes

    class RedisCaido:
        def ping(self):
            raise redis.ConnectionError("Redis no disponible")

    monkeypatch.setattr(ops_probes.settings, "queue_backend", "celery")
    monkeypatch.setattr(
        redis.Redis, "from_url", lambda *args, **kwargs: RedisCaido())

    estado, metricas = ops_probes.sonda_workers(None)
    assert estado == "caido"
    assert "Redis no disponible" in metricas["error"]


def test_sonda_workers_distingue_worker_y_umbral_de_cola(monkeypatch):
    import celery
    import redis

    from app.services import ops_probes

    class RedisTemporal:
        def __init__(self):
            self.profundidad = 500

        def ping(self):
            return True

        def llen(self, nombre):
            return self.profundidad

        def close(self):
            pass

    class Inspector:
        workers = {}

        def ping(self):
            return self.workers

        def active_queues(self):
            return {"worker-1": [{"name": "celery"}]} if self.workers else {}

        def active(self):
            return {"worker-1": []} if self.workers else {}

    class CeleryTemporal:
        control = type("Control", (), {
            "inspect": lambda self, timeout: Inspector(),
        })()

        def __init__(self, *args, **kwargs):
            pass

        def close(self):
            pass

    redis_temporal = RedisTemporal()
    monkeypatch.setattr(ops_probes.settings, "queue_backend", "celery")
    monkeypatch.setattr(redis.Redis, "from_url",
                        lambda *args, **kwargs: redis_temporal)
    monkeypatch.setattr(celery, "Celery", CeleryTemporal)
    monkeypatch.setattr(ops_probes.ops_settings, "ops_umbral_cola", 500)
    monkeypatch.setattr(
        ops_probes.ops_settings, "ops_api_health_url",
        "http://api.test/health")
    monkeypatch.setattr(ops_probes, "_resumen_api", lambda: {
        "solicitudes_5m": 0, "errores_5xx_5m": 0,
        "latencia_p95_ms": None, "ventana_segundos": 300,
        "metodo_percentil": "sin muestras",
    })

    def api_inaccesible(*args, **kwargs):
        raise ops_probes.urllib.error.URLError("API no disponible")

    monkeypatch.setattr(
        ops_probes.urllib.request, "urlopen", api_inaccesible)

    Inspector.workers = {}
    estado, metricas = ops_probes.sonda_workers(None)
    assert estado == "caido"
    assert metricas["workers_activos"] == 0

    Inspector.workers = {"worker-1": {"ok": "pong"}}
    estado, metricas = ops_probes.sonda_workers(None)
    assert estado == "operativo"
    assert metricas["colas"] == {"celery": 500}
    estado_api, _ = ops_probes.sonda_api(None)
    assert estado_api == "caido"

    redis_temporal.profundidad = 501
    estado, metricas = ops_probes.sonda_workers(None)
    assert estado == "degradado"
    assert metricas["colas"] == {"celery": 501}


def test_sonda_api_comparte_histograma_redis(monkeypatch):
    from app.services import ops_probes

    class FakePipeline:
        def __init__(self, client):
            self.client = client
            self.comandos = []

        def hincrby(self, key, campo, valor):
            self.comandos.append(("hincrby", key, campo, valor))

        def expire(self, key, segundos):
            self.comandos.append(("expire", key, segundos))

        def hgetall(self, key):
            self.comandos.append(("hgetall", key))

        def execute(self):
            salida = []
            for comando in self.comandos:
                if comando[0] == "hincrby":
                    _, key, campo, valor = comando
                    fila = self.client.datos.setdefault(key, {})
                    fila[campo] = int(fila.get(campo, 0)) + valor
                    salida.append(fila[campo])
                elif comando[0] == "hgetall":
                    salida.append(self.client.datos.get(comando[1], {}))
                else:
                    salida.append(True)
            return salida

    class FakeRedis:
        def __init__(self):
            self.datos = {}

        def pipeline(self, transaction=False):
            return FakePipeline(self)

    monkeypatch.setattr(ops_probes.settings, "queue_backend", "celery")
    monkeypatch.setattr(ops_probes.ops_settings, "ops_api_health_url", "")
    monkeypatch.setattr(ops_probes, "_api_redis", FakeRedis())
    for duracion in range(1, 21):
        ops_probes.registrar_solicitud_api(
            duracion, 500 if duracion == 20 else 200)

    estado, metricas = ops_probes.sonda_api(None)
    assert estado == "degradado"
    assert metricas["solicitudes_5m"] == 20
    assert metricas["errores_5xx_5m"] == 1
    assert metricas["latencia_p95_ms"] == 25
    assert "histograma" in metricas["metodo_percentil"]


def test_sonda_storage_verifica_ciclo_completo(monkeypatch):
    from app.services import ops_probes

    class StorageTemporal:
        def __init__(self):
            self.objetos = {}

        def save(self, ruta, contenido):
            self.objetos[ruta] = contenido

        def read(self, ruta):
            return self.objetos[ruta]

        def delete(self, ruta):
            self.objetos.pop(ruta, None)

        def exists(self, ruta):
            return ruta in self.objetos

    storage = StorageTemporal()
    monkeypatch.setattr("app.services.storage.get_storage", lambda: storage)
    estado, metricas = ops_probes.sonda_storage(None)

    assert estado == "operativo"
    assert {"escritura_ms", "lectura_ms", "eliminacion_ms"} <= metricas.keys()
    assert storage.objetos == {}


def test_sonda_storage_no_ejecuta_canario_azure(monkeypatch):
    from app.services import ops_probes

    monkeypatch.setattr(ops_probes.settings, "storage_backend", "azure")
    monkeypatch.setattr(
        "app.services.storage.get_storage",
        lambda: pytest.fail("No debe inicializar ni consultar Azure Blob"),
    )

    estado, metricas = ops_probes.sonda_storage(None)

    assert estado == "degradado"
    assert metricas["backend"] == "azure"
    assert metricas["estado_datos"] == "no_verificado"
    assert "transacciones facturables" in metricas["detalle"]


def test_sonda_integraciones_mide_corridas_y_marca_conector_pendiente(
    empresa_a, monkeypatch,
):
    from datetime import timedelta

    from app.database import worker_session
    from app.models import Integracion, SyncLog
    from app.services.ops_probes import sonda_integraciones

    ahora = datetime.now(timezone.utc)
    with worker_session(is_admin=True) as db:
        integracion = Integracion(
            company_id=uuid.UUID(empresa_a["company_id"]),
            tipo="whatsapp", estado="activa")
        db.add(integracion)
        db.flush()
        db.add(SyncLog(
            integracion_id=integracion.id,
            company_id=integracion.company_id,
            status="error",
            started_at=ahora - timedelta(seconds=2),
            finished_at=ahora,
        ))
        db.flush()
        estado, metricas = sonda_integraciones(db)

    assert estado == "degradado"
    assert metricas["ejecuciones_7d"] == 1
    assert metricas["errores_7d"] == 1
    assert metricas["conectividad_externa_verificada"] is False
    assert metricas["conectores_pendientes"] == ["whatsapp"]


def test_disponibilidad_404_y_parcial(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/ops/sistemas/nube/disponibilidad",
                        headers=admin["headers"])
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "COMPONENTE_DESCONOCIDO"

    _run_ok(app_cliente, admin, "ops_heartbeat")
    r = app_cliente.get(f"{API}/admin/ops/sistemas/db/disponibilidad?dias=7",
                        headers=admin["headers"])
    assert r.status_code == 200
    d = r.json()
    assert d["dias"][-1]["parcial"] is True
    assert d["dias"][-1]["estado"] == "operativo"


def test_procesos_listado(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/ops/procesos", headers=admin["headers"])
    assert r.status_code == 200
    claves = {x["clave"] for x in r.json()["items"]}
    assert {"vencimientos", "ops_heartbeat", "metricas_snapshot",
            "ia_revision"} <= claves
    continuo = next(x for x in r.json()["items"] if x["clave"] == "ia_revision")
    assert continuo["tipo"] == "continuo" and continuo["cron_expr"] is None


def test_schedules_celery_y_local_cubren_todos_los_jobs():
    from types import SimpleNamespace
    from zoneinfo import ZoneInfo

    from worker.ops_tasks import (OPS_CRON_SCHEDULES, registrar_ops,
                                  registrar_scheduler_local)

    class FakeCelery:
        def __init__(self):
            self.conf = SimpleNamespace(beat_schedule={})

        def task(self, name):
            return lambda fn: fn

    class FakeScheduler:
        timezone = ZoneInfo("America/Santiago")

        def __init__(self):
            self.jobs = {}

        def add_job(self, fn, trigger, **kwargs):
            self.jobs[kwargs["id"]] = (fn, trigger, kwargs)

    celery = FakeCelery()
    registrar_ops(celery)
    schedules = celery.conf.beat_schedule
    assert set(schedules) == {
        "ops-heartbeat", *(f"ops-{clave}" for clave in OPS_CRON_SCHEDULES)}
    assert schedules["ops-reportes_programados"]["args"] == (
        "reportes_programados",)

    local = FakeScheduler()
    registrar_scheduler_local(local)
    assert set(local.jobs) == {
        "ops-ops_heartbeat", *(f"ops-{clave}" for clave in OPS_CRON_SCHEDULES)}
    assert all(fn is not None for fn, _, _ in local.jobs.values())
    assert local.jobs["ops-reportes_programados"][1].timezone == local.timezone


def test_corrida_cron_pasa_por_historial_operativo(monkeypatch, motor_admin):
    from sqlalchemy import text

    from app.services import ops

    monkeypatch.setitem(
        ops.OPS_RUNNERS, "metricas_snapshot",
        lambda db, **_: (1, "runner de prueba ejecutado"))
    run_id = ops.disparar_por_cron("metricas_snapshot")
    assert run_id is not None
    with motor_admin.connect() as conn:
        fila = conn.execute(text(
            "SELECT status::text, disparo::text, mensaje "
            "FROM ops_job_runs WHERE id=:id"), {"id": run_id}).one()
    assert fila == ("ok", "cron", "runner de prueba ejecutado")


def test_historial_identifica_corridas_demo_y_no_las_mide_como_reales(
        app_cliente, admin, motor_admin):
    from sqlalchemy import text

    with motor_admin.begin() as conn:
        run_id = conn.execute(text(
            "INSERT INTO ops_job_runs "
            "(job_clave, status, disparo, params, started_at, finished_at, "
            "items_procesados, mensaje) "
            "VALUES ('purga_temporales', 'ok', 'cron', "
            "'{\"origen\":\"seed_demo\"}'::jsonb, now(), now(), 59, "
            "'Ejecución de ejemplo') RETURNING id")).scalar_one()

    ruta = f"{API}/admin/ops/procesos"
    respuesta = app_cliente.get(ruta, headers=admin["headers"])
    purga = next(item for item in respuesta.json()["items"]
                 if item["clave"] == "purga_temporales")
    assert purga["ultima_ejecucion"]["run_id"] == run_id
    assert purga["ultima_ejecucion"]["es_demo"] is True
    assert purga["tasa_exito_7d_pct"] is None

    historial = app_cliente.get(
        f"{API}/admin/ops/procesos/purga_temporales/ejecuciones",
        headers=admin["headers"]).json()["items"]
    assert historial[0]["es_demo"] is True


def test_purga_temporales_expone_fallo_de_storage(monkeypatch):
    from app.services import tasks

    class Contenedor:
        def list_blobs(self, name_starts_with):
            raise RuntimeError("Storage no disponible")

    class StorageTemporal:
        client = type("Cliente", (), {
            "get_container_client": lambda self, nombre: Contenedor(),
        })()

    monkeypatch.setattr(
        "app.services.storage.get_storage", lambda: StorageTemporal())
    with pytest.raises(RuntimeError, match="Storage no disponible"):
        tasks.purgar_temporales()


def test_storage_azure_no_oculta_errores_de_borrado(monkeypatch):
    from app.services.storage import AzureBlobStorage

    class Blob:
        def delete_blob(self):
            raise PermissionError("Borrado no autorizado")

    storage = AzureBlobStorage.__new__(AzureBlobStorage)
    monkeypatch.setattr(storage, "_blob", lambda ruta: Blob())
    with pytest.raises(PermissionError, match="Borrado no autorizado"):
        storage.delete("tmp/prueba")


def test_ejecutar_manual_y_409_en_ejecucion(app_cliente, admin, motor_admin):
    run = _run_ok(app_cliente, admin, "ops_heartbeat")
    assert run["disparo"] == "manual"
    assert run["actor"]["email"] == admin["email"]

    # Con un run 'running' colgado, el siguiente POST debe chocar.
    from sqlalchemy import text
    with motor_admin.connect() as c:
        c.execute(text(
            "INSERT INTO ops_job_runs (job_clave, status, disparo, started_at) "
            "VALUES ('ops_heartbeat', 'running', 'cron', now())"))
        c.commit()
    r = app_cliente.post(f"{API}/admin/ops/procesos/ops_heartbeat/ejecutar",
                         headers=admin["headers"], json={})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOB_EN_EJECUCION"
    with motor_admin.connect() as c:
        c.execute(text("UPDATE ops_job_runs SET status='ok' "
                       "WHERE status='running'"))
        c.commit()


def test_historial_muestra_run_encolado_y_progreso_en_vivo(
        app_cliente, admin, monkeypatch):
    from app.models_ops import OpsJob
    from app.services import ops

    iniciado = Event()
    continuar = Event()

    def runner_con_progreso(_db, _progress=None, **_):
        _progress(42, "Sondeo 2 de 5")
        iniciado.set()
        if not continuar.wait(timeout=10):
            raise TimeoutError("La prueba no liberó el runner")
        return 5, "5 componentes sondeados"

    monkeypatch.setitem(ops.OPS_RUNNERS, "ops_heartbeat", runner_con_progreso)
    with worker_session(is_admin=True) as db:
        job = db.get(OpsJob, "ops_heartbeat")
        run = ops.crear_run(db, job, disparo="manual")
        db.commit()
        run_id = run.id

    ruta_historial = f"{API}/admin/ops/procesos/ops_heartbeat/ejecuciones"
    encolado = app_cliente.get(ruta_historial, headers=admin["headers"])
    assert encolado.headers["cache-control"] == "private, no-store"
    run_encolado = next(r for r in encolado.json()["items"]
                        if r["run_id"] == run_id)
    assert run_encolado["status"] == "queued"
    assert run_encolado["created_at"]

    hilo = Thread(target=ops.ejecutar_run, args=(run_id,), daemon=True)
    hilo.start()
    try:
        assert iniciado.wait(timeout=5), "El runner no reportó progreso"
        actualizado = app_cliente.get(ruta_historial, headers=admin["headers"])
        run_activo = next(r for r in actualizado.json()["items"]
                          if r["run_id"] == run_id)
        assert run_activo["status"] == "running"
        assert run_activo["progress_pct"] == 42
        assert run_activo["progress_mensaje"] == "Sondeo 2 de 5"

        procesos = app_cliente.get(
            f"{API}/admin/ops/procesos", headers=admin["headers"])
        assert procesos.headers["cache-control"] == "private, no-store"
        ultima = next(p for p in procesos.json()["items"]
                      if p["clave"] == "ops_heartbeat")["ultima_ejecucion"]
        assert ultima["run_id"] == run_id
        assert ultima["progress_pct"] == 42
    finally:
        continuar.set()
        hilo.join(timeout=10)
    assert not hilo.is_alive()

    terminada = app_cliente.get(ruta_historial, headers=admin["headers"])
    run_final = next(r for r in terminada.json()["items"]
                     if r["run_id"] == run_id)
    assert run_final["status"] == "ok"
    assert run_final["progress_pct"] == 100


def test_ejecutar_job_desconocido(app_cliente, admin):
    r = app_cliente.post(f"{API}/admin/ops/procesos/nada/ejecutar",
                         headers=admin["headers"], json={})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "JOB_DESCONOCIDO"


def test_pausar_reanudar_y_reglas(app_cliente, admin):
    base = f"{API}/admin/ops/procesos/purga_temporales"

    r = app_cliente.patch(base, headers=admin["headers"],
                          json={"activo": False})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "MOTIVO_REQUERIDO"

    r = app_cliente.patch(base, headers=admin["headers"],
                          json={"activo": False, "motivo": "Mantención"})
    assert r.status_code == 200
    assert r.json()["activo"] is False
    assert r.json()["proxima_ejecucion_at"] is None

    # Pausado sigue aceptando ejecución manual (la pausa es solo del cron).
    _run_ok(app_cliente, admin, "purga_temporales")

    r = app_cliente.patch(base, headers=admin["headers"], json={"activo": True})
    assert r.status_code == 200 and r.json()["activo"] is True

    r = app_cliente.patch(f"{API}/admin/ops/procesos/ia_revision",
                          headers=admin["headers"],
                          json={"activo": False, "motivo": "x"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "JOB_NO_PAUSABLE"


def test_incidentes_ciclo_completo(app_cliente, admin):
    # Crear manual.
    r = app_cliente.post(f"{API}/admin/ops/incidentes", headers=admin["headers"],
                         json={"componente": "storage", "severidad": "degradado",
                               "titulo": "Subida lenta reportada por cliente"})
    assert r.status_code == 201, r.text
    inc = r.json()
    assert inc["origen"] == "manual" and inc["estado"] == "abierto"
    iid = inc["id"]

    # Componente inexistente y severidad inválida.
    r = app_cliente.post(f"{API}/admin/ops/incidentes", headers=admin["headers"],
                         json={"componente": "nube", "severidad": "caido",
                               "titulo": "x"})
    assert r.status_code == 404
    r = app_cliente.post(f"{API}/admin/ops/incidentes", headers=admin["headers"],
                         json={"componente": "api", "severidad": "operativo",
                               "titulo": "x"})
    assert r.status_code == 422

    # Cerrar sin resolución -> 422; con resolución -> resuelto.
    r = app_cliente.patch(f"{API}/admin/ops/incidentes/{iid}",
                          headers=admin["headers"], json={"estado": "resuelto"})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "RESOLUCION_REQUERIDA"

    r = app_cliente.patch(f"{API}/admin/ops/incidentes/{iid}",
                          headers=admin["headers"],
                          json={"estado": "resuelto",
                                "resolucion": "Reinicio del pool"})
    assert r.status_code == 200 and r.json()["estado"] == "resuelto"

    # Resuelto: editar -> 409; reabrir -> ok; transición inválida -> 400.
    r = app_cliente.patch(f"{API}/admin/ops/incidentes/{iid}",
                          headers=admin["headers"], json={"titulo": "otro"})
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "INCIDENTE_RESUELTO"

    r = app_cliente.patch(f"{API}/admin/ops/incidentes/{iid}",
                          headers=admin["headers"], json={"estado": "abierto"})
    assert r.status_code == 200 and r.json()["resuelto_at"] is None

    r = app_cliente.patch(f"{API}/admin/ops/incidentes/{iid}",
                          headers=admin["headers"],
                          json={"estado": "abierto"})   # abierto -> abierto
    # sin cambio de estado no es transición: se acepta como edición vacía
    assert r.status_code == 200

    r = app_cliente.get(f"{API}/admin/ops/incidentes?estado=abierto",
                        headers=admin["headers"])
    assert any(x["id"] == iid for x in r.json()["items"])


# ============================================================================
# §7 — Indicadores
# ============================================================================
def test_indicadores_resumen_en_vivo(app_cliente, admin, suscripcion_a):
    r = app_cliente.get(f"{API}/admin/ops/indicadores/resumen",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["parcial"] is True and d["moneda"] == "CLP"
    assert d["mrr"]["valor"] > 0                    # 12,5 UF activas
    assert d["arr"] == round(d["mrr"]["valor"] * 12, 2)
    assert d["clientes_activos"] >= 1
    assert d["objetivo_churn_pct"] == 2.0
    # Sin CAC configurado no se inventa un LTV/CAC.
    assert d["ltv_cac"] is None

    ajustes = app_cliente.patch(
        f"{API}/admin/ajustes-negocio", headers=admin["headers"],
        json={
            "valor_uf": 39000,
            "uf_vigente_desde": date.today().isoformat(),
            "uf_fuente": "Prueba",
            "cac_clp": 500000,
            "margen_bruto_pct": 80,
            "objetivo_churn_pct": 2,
            "motivo": "Prueba de actualización CAC",
        })
    assert ajustes.status_code == 200, ajustes.text
    r = app_cliente.get(f"{API}/admin/ops/indicadores/resumen",
                        headers=admin["headers"])
    assert r.status_code == 200, r.text
    assert r.headers["cache-control"] == "private, no-store"
    assert r.json()["ltv_cac"]["payback_meses"] > 0


def test_indicadores_mes_futuro(app_cliente, admin):
    r = app_cliente.get(f"{API}/admin/ops/indicadores/resumen?mes=2999-01",
                        headers=admin["headers"])
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "RANGO_INVALIDO"


def test_snapshot_y_series(app_cliente, admin, suscripcion_a):
    _run_ok(app_cliente, admin, "metricas_snapshot")

    r = app_cliente.get(f"{API}/admin/ops/indicadores/mrr?meses=3",
                        headers=admin["headers"])
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[-1]["parcial"] is True
    assert items[-1]["mrr"] > 0

    r = app_cliente.get(f"{API}/admin/ops/indicadores/clientes-flujo",
                        headers=admin["headers"])
    fin = r.json()["items"][-1]
    assert fin["neto"] == fin["altas"] - fin["bajas"]

    r = app_cliente.get(f"{API}/admin/ops/indicadores/churn",
                        headers=admin["headers"])
    assert r.json()["objetivo_pct"] == 2.0

    r = app_cliente.get(f"{API}/admin/ops/indicadores/por-plan",
                        headers=admin["headers"])
    d = r.json()
    pro = next(x for x in d["items"] if x["plan"] == "Pro")
    assert pro["mrr"] > 0
    if len(d["items"]) == 1:
        assert pro["pct_mrr"] == 100.0


# ============================================================================
# Auditoría
# ============================================================================
def test_acciones_auditadas_sin_tenant(app_cliente, admin, motor_admin):
    app_cliente.patch(f"{API}/admin/ops/procesos/purga_temporales",
                      headers=admin["headers"],
                      json={"activo": False, "motivo": "Prueba de auditoría"})
    from sqlalchemy import text
    with motor_admin.connect() as c:
        filas = c.execute(text(
            "SELECT descripcion FROM actividad "
            "WHERE modulo = 'ops' AND company_id IS NULL")).all()
    assert any("Prueba de auditoría" in f.descripcion for f in filas)
    app_cliente.patch(f"{API}/admin/ops/procesos/purga_temporales",
                      headers=admin["headers"], json={"activo": True})


def test_catalogo_auditado_y_visible_en_auditoria_global(app_cliente, admin):
    creada = app_cliente.post(f"{API}/admin/faenas", headers=admin["headers"],
                              json={"nombre": "Faena auditada", "mandante": "Mandante"})
    assert creada.status_code == 201, creada.text

    auditoria = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"modulo": "admin_catalogo", "page_size": 10})
    assert auditoria.status_code == 200, auditoria.text
    evento = next(item for item in auditoria.json()["items"]
                  if item["entidad_id"] == creada.json()["id"])
    assert evento["empresa"] == "Plataforma"
    assert evento["actor"] == "Admin Plataforma"
    assert evento["tipo"] == "creacion"


def test_mutaciones_catalogo_registran_cambios_antes_y_despues(
        app_cliente, admin):
    creada = app_cliente.post(
        f"{API}/admin/faenas", headers=admin["headers"],
        json={"nombre": "Faena cambios auditados", "mandante": "Mandante"},
    )
    assert creada.status_code == 201, creada.text
    faena_id = creada.json()["id"]

    editada = app_cliente.patch(
        f"{API}/admin/faenas/{faena_id}", headers=admin["headers"],
        json={"nombre": "Faena renombrada"},
    )
    assert editada.status_code == 200, editada.text
    plataforma = app_cliente.post(
        f"{API}/admin/faenas/{faena_id}/plataformas",
        headers=admin["headers"], json={"nombre": "Portal auditado"},
    )
    assert plataforma.status_code == 201, plataforma.text

    codigo = f"AUD-{faena_id[:8]}"
    plantilla = app_cliente.post(
        f"{API}/admin/requisitos/templates", headers=admin["headers"],
        json={"ambito": "empresa", "titulo": "Requisito auditado",
              "codigo": codigo, "tipo": "legal"},
    )
    assert plantilla.status_code == 201, plantilla.text
    plantilla_id = plantilla.json()["id"]
    desactivada = app_cliente.delete(
        f"{API}/admin/requisitos/templates/{plantilla_id}",
        headers=admin["headers"],
    )
    assert desactivada.status_code == 200, desactivada.text

    auditoria = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"modulo": "admin_catalogo", "page_size": 100},
    )
    assert auditoria.status_code == 200, auditoria.text
    eventos = auditoria.json()["items"]

    evento_faena = next(item for item in eventos
                        if item["entidad_id"] == faena_id
                        and item["descripcion"] == "Faena actualizada")
    assert evento_faena["cambios"]["nombre"] == {
        "antes": "Faena cambios auditados",
        "despues": "Faena renombrada",
    }
    assert any(item["entidad_id"] == plataforma.json()["id"]
               and item["tipo"] == "creacion" for item in eventos)
    evento_template = next(item for item in eventos
                           if item["entidad_id"] == plantilla_id
                           and item["descripcion"] ==
                           "Plantilla de requisito desactivada")
    assert evento_template["cambios"]["activo"] == {
        "antes": True, "despues": False,
    }


def test_cambio_estado_empresa_audita_empresa_y_usuarios(
        app_cliente, admin, empresa_a):
    respuesta = app_cliente.post(
        f"{API}/admin/companies/{empresa_a['company_id']}/reject",
        headers=admin["headers"], json={"reason": "Revisión administrativa"},
    )
    assert respuesta.status_code == 200, respuesta.text

    auditoria = app_cliente.get(
        f"{API}/admin/users/audit", headers=admin["headers"],
        params={"page_size": 100},
    )
    assert auditoria.status_code == 200, auditoria.text
    evento_usuario = next(item for item in auditoria.json()["items"]
                          if item["usuario_id"] == empresa_a["user_id"]
                          and item["descripcion"] ==
                          "Estado de acceso de usuario cambiado por administración")
    assert evento_usuario["cambios"]["status"] == {
        "antes": "approved", "despues": "rejected",
    }

    eventos_globales = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"modulo": "empresa", "page_size": 100},
    )
    assert eventos_globales.status_code == 200, eventos_globales.text
    evento_empresa = next(
        item for item in eventos_globales.json()["items"]
        if item["entidad_id"] == empresa_a["company_id"]
        and item["descripcion"] == "Estado de cuenta cambiado por administración"
    )
    assert evento_empresa["cambios"]["status"] == {
        "antes": "approved", "despues": "rejected",
    }


def test_revocacion_admin_sin_empresa_audita_cambios(
        app_cliente, admin, motor_admin):
    from app.models import User

    user_id = uuid.uuid4()
    with worker_session(is_admin=True) as db:
        db.add(User(
            id=user_id, email=f"admin-{user_id}@acredittia.cl",
            nombre="Admin sin empresa", password_hash="no-se-usa",
            role="admin", company_id=None, status="approved",
        ))
        db.commit()

    respuesta = app_cliente.post(
        f"{API}/admin/users/{user_id}/revoke",
        headers=admin["headers"], json={"motivo": "Cambio de responsabilidad"},
    )
    assert respuesta.status_code == 200, respuesta.text

    auditoria = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"user_id": admin["user_id"], "page_size": 100},
    )
    assert auditoria.status_code == 200, auditoria.text
    evento = next(
        item for item in auditoria.json()["items"]
        if item["entidad_id"] == str(user_id)
        and item["descripcion"] == "Acceso de usuario revocado por administración"
    )
    assert evento["empresa"] == "Plataforma"
    assert evento["cambios"]["activo"] == {
        "antes": True, "despues": False,
    }

    repetida = app_cliente.post(
        f"{API}/admin/users/{user_id}/revoke",
        headers=admin["headers"], json={},
    )
    assert repetida.status_code == 200, repetida.text
    auditoria_final = app_cliente.get(
        f"{API}/admin/audit", headers=admin["headers"],
        params={"user_id": admin["user_id"], "page_size": 100},
    )
    eventos_revocacion = [
        item for item in auditoria_final.json()["items"]
        if item["entidad_id"] == str(user_id)
        and item["descripcion"] == "Acceso de usuario revocado por administración"
    ]
    assert len(eventos_revocacion) == 1
