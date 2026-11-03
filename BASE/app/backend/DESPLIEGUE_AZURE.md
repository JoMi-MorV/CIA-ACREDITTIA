# Despliegue en Azure

Guía operativa para la versión actual del backend. La API requiere el esquema
**v13** (`SCHEMA_VERSION_ESPERADA=13`); aplica y verifica las migraciones antes
de desplegar API, worker y beat con la misma imagen.

Cuatro procesos, **una sola imagen**, diferenciados por el `command`. Así un
despliegue no puede dejar la API y el worker en versiones distintas del código.

| Proceso | Recurso Azure | Command |
|---|---|---|
| API | Container App | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |
| Worker | Container App | `celery -A worker.celery_app worker --concurrency=4` |
| Beat (cron) | Container App, 1 réplica fija | `celery -A worker.celery_app beat` |
| Migración | Container Apps Job, `--parallelism 1` | `python -m migrate.run` |

Todos los procesos programados pasan por el mismo registro operativo que usa la
consola; el horario aplica en `America/Santiago` y cada corrida deja un resultado
consultable. El despachador de reportes revisa las programaciones cada minuto
para respetar el minuto definido en su expresión cron.

## Recursos necesarios

- **Azure Database for PostgreSQL Flexible Server** 16. Habilitar previamente
  `azure.extensions = CITEXT,PG_TRGM`, que el esquema exige.
- **Azure Cache for Redis** — broker y backend de Celery.
- **Storage Account** con un contenedor privado (`docs`).
- **Key Vault** (HSM recomendado) con una clave RSA llamada `plataforma-cred`.

## Tres roles de base de datos, no uno

Los crea `04_rls.sql` y `06_migracion_v11.sql`. La separación no es cosmética:
es lo que hace que el vault JWE (§8.2) sea real.

| Rol | Lo usa | Puede leer `credencial_jwe` |
|---|---|---|
| `acredittia_owner` | job de migración | sí (es el dueño) |
| `acredittia_app` | API | **no** — SELECT revocado |
| `acredittia_worker` | worker y beat | sí |

Cambia las contraseñas placeholder `CAMBIAR_EN_KEY_VAULT` en el primer
despliegue y guárdalas en Key Vault. Si la API se ejecutara con el rol del
worker, la separación de privilegios desaparece sin que nada falle: es el error
de configuración más fácil de cometer y el más difícil de notar.

## Variables de entorno

### API
```
DATABASE_URL      postgresql+psycopg://acredittia_app:<pwd>@<host>:5432/acredittia?sslmode=require
DB_RLS_ENABLED    true
DB_APPLY_SCHEMA_ON_START  false      # lo hace el job de migración
SCHEMA_VERSION_ESPERADA   13
JWT_SECRET        <secreto de Key Vault>
CORS_ORIGINS      https://app.acredittia.cl
PUBLIC_BASE_URL   https://api.acredittia.cl
STORAGE_BACKEND   azure
AZURE_STORAGE_ACCOUNT  acredittiast
AZURE_BLOB_CONTAINER   docs
QUEUE_BACKEND     celery
REDIS_URL         rediss://:<clave>@<cache>.redis.cache.windows.net:6380/0
JWE_BACKEND       keyvault
AZURE_KEYVAULT_URL     https://acredittia-kv.vault.azure.net
KEYVAULT_KEY_NAME      plataforma-cred
IA_BACKEND        claude
ANTHROPIC_API_KEY <secreto de Key Vault>
```

### Respaldos y exportaciones ADMIN

La exportación de conjuntos administrativos no depende del backend de archivos.
El respaldo/restauración implementado actualmente **solo admite
`STORAGE_BACKEND=local`**. Esta guía de Azure configura `STORAGE_BACKEND=azure`,
por lo que los respaldos no están habilitados para el despliegue Azure: no se
debe tratar el volumen local como copia de Blob ni activar el proceso semanal
hasta aprobar e implementar un adaptador de respaldo de Azure Blob. La interfaz
marca la función como no configurada y la migración deja el job pausado. La API
rechaza reanudarlo o ejecutarlo si falta configuración.

Para instalaciones compatibles con almacenamiento local:

```
BACKUPS_DIR                 /data/backups
BACKUP_DATABASE_URL         postgresql+psycopg://<rol_lectura_backup>:<pwd>@<host>:5432/acredittia?sslmode=require
BACKUP_RESTORE_DATABASE_URL postgresql+psycopg://<rol_mantenimiento>:<pwd>@<host>:5432/acredittia?sslmode=require
BACKUP_ENCRYPTION_KEY       <base64-url-safe de 32 bytes aleatorios, desde Key Vault>
BACKUP_RESTORE_ROLE         <rol propietario de la base temporal/restaurada>
BACKUP_RETENTION_COUNT      8
```

Ambas URLs deben apuntar al mismo servidor/base que `DATABASE_URL`. Mantenga
credenciales separadas: `BACKUP_DATABASE_URL` solo requiere lectura completa
para `pg_dump` (incluido `BYPASSRLS` para respaldar todas las empresas) y se
usa en API/worker; `BACKUP_RESTORE_DATABASE_URL` queda solo en API y necesita
privilegios de mantenimiento para crear/restaurar/verificar bases, cerrar
conexiones y reemplazar la activa. `BACKUP_RESTORE_ROLE` es el dueño de la base
restaurada y debe poder crear los objetos/extensiones requeridos por el esquema.
No entregue la credencial de mantenimiento al worker. El contenedor instala
herramientas PostgreSQL 16. Configure la misma clave externa en API y worker,
mantenga una copia recuperable por un canal independiente y no la guarde en
repositorio, imagen ni paquete. Perder esa clave vuelve irrecuperables las
copias. En `development`, si `BACKUP_RESTORE_DATABASE_URL` no se fija, el
servicio usa `BACKUP_DATABASE_URL` como compatibilidad local; en producción no
hay fallback. `BACKUPS_DIR` debe ser privado y persistente, compartido por API
y worker. No se incluyen claves JWE/vault, secretos ni archivos remotos de
Azure. La retención de ocho no constituye una copia fuera del entorno ni
define RPO o RTO; no desplegar ni ejecutar la restauración contra producción
sin una ventana aprobada y prueba de recuperación.

### Worker y beat
Lo mismo, salvo:
```
WORKER_DATABASE_URL  postgresql+psycopg://acredittia_worker:<pwd>@<host>:5432/acredittia?sslmode=require
OPS_API_HEALTH_URL   URL interna del endpoint /health de la API, accesible desde el worker
```
`worker/celery_app.py` la copia sobre `DATABASE_URL` antes de importar la
aplicación, para que el engine se construya con el rol correcto.

El worker ejecuta las sondas de salud: verifica Redis y workers Celery, y
consulta esta URL para medir la disponibilidad HTTP de la API. Configúrala con
el nombre DNS interno de la Container App; no uses una URL pública si existe
una ruta interna. Las latencias y errores de requests se agregan en Redis en
ventanas de cinco minutos, sin conservar rutas, usuarios ni payloads.

### Job de migración
```
MIGRATE_DATABASE_URL  postgresql+psycopg://acredittia_owner:<pwd>@<host>:5432/acredittia?sslmode=require
SCHEMA_DIR            /schema      # monta modelo_datos/
```

## Identidad administrada

Asigna a la identidad de los Container Apps:

- **Storage Blob Data Contributor** sobre la cuenta de almacenamiento. Hace falta
  el rol de *Contributor*, no solo *Reader*, porque emitir SAS de usuario
  delegado exige pedir la clave de delegación.
- **Key Vault Crypto User** sobre la clave `plataforma-cred` (operaciones
  `wrapKey` y `unwrapKey`).
- **Key Vault Secrets User** si se usa `KeyVaultSecretWriter` para las
  credenciales de integración.

`DefaultAzureCredential` las resuelve sin secretos en configuración. En
desarrollo la misma credencial usa `az login`.

## Salud de Azure Blob

La sonda operativa no ejecuta escrituras, lecturas ni borrados canario sobre
Azure Blob: esas solicitudes generarían transacciones facturables. Cuando
`STORAGE_BACKEND=azure`, Storage aparece como **degradado / no verificado** en
vez de afirmar disponibilidad sin evidencia. Para habilitar una señal positiva
sin sondeos sintéticos, hace falta instrumentar y agregar las operaciones reales
del negocio.

## Parámetro del servidor obligatorio

```
log_error_verbosity = terse
```

Sin él, una violación de NOT NULL o UNIQUE sobre `plataforma_credenciales` emite
`DETAIL: Failing row contains (...)` con el JWE incluido, y ese texto va al log
del servidor. El JWE no es descifrable sin Key Vault, pero el log pasaría a
tener la misma clasificación que la base de datos. Ver §4.8 y §10 del modelo de
datos.

## Orden de despliegue

```bash
# 1. Esquema (falla el deploy si no termina bien)
az containerapp job start -n acredittia-migrate -g <rg>

# 2. Verificación
az containerapp job start -n acredittia-migrate -g <rg> --command "python -m migrate.run --verificar"

# 3. API, worker y beat
az containerapp update -n acredittia-api    -g <rg> --image <acr>/acredittia:<tag>
az containerapp update -n acredittia-worker -g <rg> --image <acr>/acredittia:<tag>
az containerapp update -n acredittia-beat   -g <rg> --image <acr>/acredittia:<tag>
```

La API comprueba la versión del esquema al arrancar y **falla rápido** si no
coincide, así que un despliegue con el orden invertido se detecta en el probe y
no a mitad de un request.

## Probes

- Liveness: `GET /health`
- Readiness: `GET /health/esquema` — devuelve 503 si la base no está en la
  versión esperada.

## Escalado

- **API**: sin estado, escala por peticiones. El contexto de tenant vive en un
  `ContextVar` por request, no en el proceso.
- **Worker**: escala por longitud de cola con KEDA sobre Redis.
- **Beat**: exactamente **1 réplica**. Dos instancias dispararían el cron dos
  veces; los snapshots de cumplimiento lo absorben (son idempotentes por día),
  pero los reportes programados se duplicarían.

## Procesos programados

`celery beat` debe ejecutarse en una sola réplica y programa todos los runners
operativos a través del dispatcher de `ops_jobs`. Cada disparo queda registrado
en el historial operativo, respeta la pausa del proceso y evita ejecuciones
solapadas. Los horarios usan `America/Santiago`:

| Proceso | Frecuencia |
|---|---|
| Sondeo de componentes (heartbeat) | Cada minuto |
| Reportes programados | Cada minuto; el dispatcher evalúa los cinco campos del cron |
| Vencimientos y snapshots de documentos | Todos los días a las 00:30 |
| Consolidación de disponibilidad | Todos los días a las 00:05 |
| Snapshot de métricas de negocio | Todos los días a las 02:10 |
| Retención de telemetría | Domingos a las 03:30 |
| Respaldo ADMIN (solo con storage local configurado) | Domingos a las 02:00 |
| Purga de blobs temporales de IA | Todos los días a las 04:00 |

Con `QUEUE_BACKEND=inproc` el cron corre dentro del proceso de la API vía
APScheduler; sirve para desarrollo y **no** para producción con más de una
réplica.
