# Consola Interna de Administración — código backend

Implementación de la **Especificación de API — Consola Interna v1.0**
(`Acredittia_Especificacion_API_Consola_Interna.docx`): 20 endpoints bajo
`/api/v1/admin/ops`, 7 tablas nuevas, procedimientos almacenados PL/pgSQL,
índices y 4 jobs de fondo. Módulo **drop-in** para `app/backend`.

## Mapa de archivos

| Archivo | Destino en el repo | Contenido |
|---|---|---|
| `modelo_datos/07_consola_interna.sql` | `modelo_datos/` | ENUMs, `companies.industria`, tablas `ops_*` y `metricas_mensuales*`, índices, triggers, RLS solo-admin, seeds de componentes y jobs |
| `modelo_datos/08_funciones_consola.sql` | `modelo_datos/` | Procedimientos almacenados: `ops_estado_cuenta`, `ops_usuarios_por_empresa`, `ops_precio_a_mrr_clp`, `ops_mrr_actual`, `ops_calc_metricas`, `ops_calc_metricas_plan`, `ops_snapshot_metricas`, `ops_upsert_disponibilidad`, `ops_podar_telemetria` |
| `app/models_ops.py` | `app/backend/app/` | ORM de las tablas nuevas sobre el mismo `Base`; añade `Company.industria` sin tocar `models.py` |
| `app/config_ops.py` | `app/backend/app/` | Settings `OPS_*` (valor UF, CAC, margen, umbrales del detector) |
| `app/services/ops.py` | `app/backend/app/services/` | Heartbeats (Redis/in-proc), detector de incidentes, ciclo de vida de runs, decorador `@con_run`, auditoría |
| `app/services/ops_probes.py` | `app/backend/app/services/` | Las 6 sondas (db, api, workers, storage, ia, integraciones); p95 externo tras adaptador con stub |
| `app/routers/admin_ops.py` | `app/backend/app/routers/` | Los 20 endpoints (§5, §6, §7) |
| `worker/ops_tasks.py` | `app/backend/worker/` | Runners de los jobs, entrada `ops_ejecutar_run` para la cola y `registrar_ops(celery)` con el beat |
| `tests/test_ops.py` | `app/backend/tests/` | Suite pytest con el patrón del repo (pgserver + esquema real) |

## Instalación (6 ediciones pequeñas en archivos existentes)

1. **Copiar** los archivos según la tabla anterior.

2. **`app/main.py`** — montar el router:

   ```python
   from .routers import admin_ops                       # junto a los demás imports
   app.include_router(admin_ops.router, prefix=API)     # sección "Autenticación y administración"
   ```

3. **`app/database.py`** — registrar la migración y la nueva versión:

   ```python
   SCHEMA_SCRIPTS = [..., "06_migracion_v11.sql",
                     "07_consola_interna.sql", "08_funciones_consola.sql"]
   SCHEMA_VERSION = 7
   ```

   y en `schema_version()`, antes del `return 6`:

   ```python
   if _tabla_existe(c, "ops_jobs"):
       return 7
   ```

4. **`.env` / config** — `SCHEMA_VERSION_ESPERADA=7` y, cuando existan,
   los settings financieros: `OPS_VALOR_UF`, `OPS_CAC_CLP`,
   `OPS_MARGEN_BRUTO_PCT`, `OPS_OBJETIVO_CHURN_PCT` (defaults en
   `config_ops.py`; con `OPS_CAC_CLP=0` el endpoint devuelve `ltv_cac: null`
   en lugar de inventarlo).

5. **`worker/celery_app.py`** — al final:

   ```python
   from worker.ops_tasks import registrar_ops
   registrar_ops(celery)
   ```

   Con `QUEUE_BACKEND=inproc` no hace falta nada: la ejecución manual desde la
   consola ya funciona (la entrada `ops_ejecutar_run` se registra en `TAREAS`
   al importar `worker.ops_tasks`, cosa que hace el paso 2 vía el router →
   servicios; si se quiere el heartbeat periódico en desarrollo, añadir un job
   de APScheduler en `main.py` que llame `ops.disparar_por_cron("ops_heartbeat")`).

6. **`tests/conftest.py`** — para la suite:

   ```python
   SCRIPTS = [..., "06_migracion_v11.sql",
              "07_consola_interna.sql", "08_funciones_consola.sql"]
   CATALOGOS = {..., "ops_componentes", "ops_jobs"}   # seeds que sobreviven el TRUNCATE
   ```

7. **`requirements.txt`** (opcional, recomendado): `croniter>=2.0` — calcula
   `proxima_ejecucion_at` en `GET /procesos`. Sin la librería el campo llega
   `null`; nada más se degrada.

## Decisiones que conviene conocer

* **La agregación vive en PostgreSQL.** Usuarios activos por empresa, estado
  de cuenta, MRR y snapshots son funciones PL/pgSQL (08). La API las llama con
  `text()`, filtra y serializa. Cambiar una definición de negocio (p. ej. qué
  es "factura vencida") es tocar una función, no desplegar la API.
* **El estado en tiempo real no toca PostgreSQL.** Los latidos van a Redis
  (TTL 5 min, historia de 24 h) o a un diccionario en proceso en desarrollo;
  a la BD solo llega el consolidado diario. Monitor sin latido fresco =
  componente `caido` (peor caso, nunca "último feliz").
* **Ejecutar ≠ pausar.** La pausa (`PATCH /procesos/{clave}`) solo detiene el
  cron; la ejecución manual de un job pausado está permitida a propósito. El
  tick de cron (`disparar_por_cron`) se salta jobs pausados y corridas
  solapadas.
* **Expansión/contracción de MRR = 0 por ahora.** Exigen historial de cambios
  de plan (`suscripcion_eventos`, decisión de producto pendiente); el NRR
  degenera en `(prev + perdido) / prev` y así está comentado en la función.
* **Auditoría cross-tenant.** Las acciones de la consola escriben en
  `actividad` con `modulo='ops'` y `company_id NULL` (07 relaja el NOT NULL);
  las políticas RLS por tenant dejan esas filas invisibles para las empresas.
* **Meses cerrados son inmutables.** `ops_snapshot_metricas` rechaza recalcular
  un mes `cerrado=true` salvo `p_forzar` — que solo llega vía ejecución manual
  del job `metricas_snapshot` con `params={"mes": "YYYY-MM", "forzar": true}`,
  y por tanto queda auditada con actor.

## Ejecutar la suite

```bash
cd app/backend
pytest tests/test_ops.py -q
```

## Endpoints implementados (traza contra la especificación)

§5: `GET usuarios/resumen · usuarios/por-plan · usuarios/por-industria ·
usuarios/actividad-mensual · clientes · clientes/{id}` —
§6: `GET sistemas/estado · sistemas/{comp}/disponibilidad · procesos ·
procesos/{clave}/ejecuciones` · `POST procesos/{clave}/ejecutar` ·
`PATCH procesos/{clave}` · `GET/POST incidentes` · `PATCH incidentes/{id}` —
§7: `GET indicadores/resumen · indicadores/mrr · indicadores/clientes-flujo ·
indicadores/churn · indicadores/por-plan`.
