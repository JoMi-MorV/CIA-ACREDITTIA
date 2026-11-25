# Acredittia — Aplicación web

Plataforma multiempresa de acreditación de contratistas para faenas mineras y
energéticas. El proyecto incluye un portal para empresas y una consola
administrativa interna, con autenticación JWT, aislamiento por empresa/contrato,
gestión de usuarios, contratos, personal y equipos, checklists, documentos,
revisión IA, alertas, calendario, reportes e integraciones.

## Estructura

```
app/
├── docker-compose.yml     # Postgres, Redis, migración, API, worker, beat y web
├── backend/               # FastAPI + SQLAlchemy 2 (Python 3.12)
│   └── app/
│       ├── main.py        # arranque, CORS, salud y cron local
│       ├── models.py      # modelos SQLAlchemy
│       ├── routers/       # API de portal, administración y operaciones
│       └── services/      # colas, checklist, storage, IA e integraciones
├── frontend/              # Next.js 15.5.29 + React 18
└── ../modelo_datos/       # esquema, RLS, índices, funciones y migraciones
```

PostgreSQL no ejecuta el esquema desde su inicialización. El servicio `migrate`
aplica las migraciones versionadas de `../modelo_datos/` antes de iniciar la
api y los workers. La versión actual del esquema es **23**, y la API comprueba
la versión requerida al arrancar.

## Ejecutar en local

Requisitos: Docker Desktop.

```powershell
Set-Location .\BASE\app
docker compose up --build
```

Ejecuta desde la raíz del proyecto. El comando se ejecuta en primer plano para
mostrar los mensajes de inicio y salud de los servicios; usa `Ctrl+C` para
detenerlo.
- Web: http://localhost:3000
- API: http://localhost:8000
- Documentación interactiva de la API (OpenAPI): http://localhost:8000/docs
- Salud de la API: http://localhost:8000/health

Para dejar la pila en segundo plano, ejecuta `docker compose up --build -d`;
revisa la salida con `docker compose logs -f` y el estado con `docker compose ps`.
Para detener todos los servicios sin borrar contenedores ni datos, ejecuta
`docker compose stop`.

## Procesos programados

Celery Beat es el scheduler del modo Compose y debe ejecutarse en una sola
réplica. Los disparos pasan por el ciclo de vida de procesos operativos, que
registra cada ejecución, respeta las pausas y evita solapamientos. En desarrollo
con `QUEUE_BACKEND=inproc`, APScheduler registra los mismos procesos en la API;
no uses ese modo con varias réplicas.

Todos los horarios usan `America/Santiago`:

| Proceso | Frecuencia |
|---|---|
| Sondeo de componentes (heartbeat) | Cada minuto |
| Reportes programados | Cada minuto; solo dispara los reportes cuyo cron coincide |
| Vencimientos y snapshots de documentos | Todos los días a las 00:30 |
| Consolidación de disponibilidad | Todos los días a las 00:05 |
| Snapshot de métricas de negocio | Todos los días a las 02:10 |
| Retención de telemetría | Domingos a las 03:30 |
| Purga de blobs temporales de IA | Todos los días a las 04:00 |

En `APP_ENV=test` no se inicia el scheduler local; las pruebas cubren el
registro de horarios sin lanzar procesos periódicos contra la base de pruebas.

## Demo temporal por ngrok

El perfil `docker-compose.ngrok.yml` publica únicamente el frontend por ngrok,
con el login de Acredittia activo. PostgreSQL, Redis, API y el inspector de
ngrok quedan ligados a `127.0.0.1`.
Es exclusivamente para una demostración temporal con
datos sintéticos. El Compose base usa roles de desarrollo y semillas/cuentas
demo conocidas: no cargar información real ni tratarlo como despliegue de
producción. La URL queda accesible públicamente a quien la conozca.

Desde PowerShell, en `BASE/app`:

```powershell
Copy-Item .env.example .env
```

Completa `.env` localmente con un token ngrok nuevo, el dominio reservado en tu
cuenta ngrok y un `JWT_SECRET` aleatorio único de al menos 32 bytes. No
reutilices credenciales expuestas ni compartas
los secretos por chat. El `.env` está excluido de Git.

Valida la configuración y levanta el perfil:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml up --build -d
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs -f ngrok
```

Comparte la URL HTTPS con cuidado: cualquier persona que la conozca llegará al
login de Acredittia. No distribuyas cuentas demo conocidas.
Al terminar:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml down
```

Esto detiene el túnel sin borrar los volúmenes de la base de datos. Si el token
ngrok se expone, revócalo en ngrok y reemplázalo localmente antes de iniciar.

**Cuentas semilla**

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | admin@acredittia.cl | Admin2026! |
| Empresa demo | demo@acredittia.cl | Demo2026! |

**Flujo de prueba sugerido**: registra una empresa nueva → entra como admin y
apruébala → entra con la empresa → crea un contrato en Los Pelambres (genera
10 docs de empresa) → agrega un trabajador conductor (genera 13+9 docs) →
sube un PDF a un requisito → revisa el resultado de la IA → mira el dashboard.

## Vistas administrativas de empresa

Desde **Empresas (cuentas)**, un administrador puede abrir el detalle global de
una cuenta para consultar sus agregados y las tablas de cuentas/perfiles y
responsables por contrato. La opción **Ver como empresa** inicia una
impersonación de lectura/operación contextual: conserva la sesión y el rol
`admin`, guarda el identificador de la empresa elegida en `sessionStorage` y lo
envía a la API mediante `X-Company-Id`. No inicia sesión como un usuario de esa
empresa ni cambia los permisos efectivos del administrador.

Por esa diferencia de rol, los controles de la vista de empresa que requieren
una sesión `company` no necesariamente se muestran durante la impersonación.
En particular, el bloque **Responsables de contrato** de la página Contratos
solo se carga para el rol `company`; el administrador puede consultar esos
responsables desde **Empresas (cuentas) → Detalle → Responsables por contrato**.
La página **Mi perfil** también se bloquea durante la impersonación para evitar
confundir el perfil personal del administrador con el de la empresa observada.
Al salir del modo empresa, el administrador vuelve a la consola interna.

El portal de empresa incluye **Planes y servicios** (`/planes-servicios`),
disponible para el rol `company`: muestra planes activos, suscripción/estado y
permite iniciar el trial de 30 días o cambiar/reactivar el plan sin cobro en
línea. No muestra facturas ni ofrece cancelar la suscripción. Los límites de
plan son informativos y aún no se aplican. La experiencia y las rutas API se
detallan en [README_CLIENTE.md](../../README_CLIENTE.md#planes-y-servicios).

## Consola administrativa

La consola interna ofrece **Dashboard global**, **Sistemas y procesos**,
**Indicadores**, **Gestión de empresas**, **Usuarios**, **Salud de clientes**,
**Buscador global**, **Auditoría**, **Respaldos y exportación** y **Mi perfil**.
Su acceso público es `/admin/perfil`; la implementación interna vive en
`app/ops/perfil/page.tsx`. El perfil permite actualizar nombre, correo y
contraseña de la cuenta administrativa mediante `/auth/me`, sin cambiar rol,
empresa ni contrato asignado. Sus funciones incluyen:

- Gestión de empresas (cuentas), con industria, estado de cuenta, actividad y
  detalle expandible de usuarios/perfiles y responsables por contrato.
- Indicadores de negocio y financieros, incluyendo MRR, churn, retención y
  relación LTV/CAC. El CAC necesita datos configurados para poder calcular la
  relación. Actualmente la consola no tiene una sección general de Ajustes para
  administrar precios o supuestos financieros.
- Salud de clientes con detalle desplegable para riesgos y métricas de
  uso/adopción, incluyendo usuarios por plan e industria.
- Buscador global con botones desplegables por categoría y filtros de referencia.
- Auditoría global con filtros de búsqueda, módulo, acción y fechas; permite
  ordenar los hasta 100 registros mostrados por fecha, actor, empresa, acción,
  módulo, entidad, motivo o descripción.
- Ayudas contextuales en gráficos, KPI y tablas para explicar su cálculo y
  significado.
- Administración de usuarios: cambios de rol, empresa o contrato muestran el
  impacto, exigen un motivo de al menos 12 caracteres y se registran con actor,
  fecha y valores anteriores/nuevos. Estos cambios invalidan las sesiones
  activas del usuario. La auditoría de permisos presenta el motivo y los cambios.
  En Usuarios, roles y permisos el plan de la empresa aparece como columna de
  solo lectura y puede usarse para ordenar; no permite contratar ni editar planes.
- Gestión de industria por empresa: ADMIN puede cambiarla en **Usuarios, roles y
  permisos**, y el rol `company` puede hacerlo desde **Mi perfil → Industria de la
  empresa**. Las opciones se limitan a Minería, Construcción, Energía, Industrial
  y Otras. El cambio administrativo exige motivo y queda auditado; las cuentas
  invitadas comparten la industria de su empresa porque pertenecen al mismo
  `company_id`.

La ayuda contextual explica los valores que presenta la interfaz; no reemplaza
la documentación de las fórmulas, límites y contratos de la API.

## Desarrollo sin Docker

```powershell
# API (terminal 1; desde la raíz del proyecto)
Set-Location .\BASE\app\backend
python -m pip install --require-hashes -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/acredittia"
$env:SCHEMA_DIR = "..\..\modelo_datos"
$env:STORAGE_DIR = "$env:TEMP\uploads"
python -m migrate.run
python -m uvicorn app.main:app --reload

# Frontend (terminal 2; desde la raíz del proyecto)
Set-Location .\BASE\app\frontend
npm ci
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

La base PostgreSQL debe existir y aceptar la conexión indicada. Ejecuta el
frontend en una terminal separada mientras la API permanece activa.

`requirements.in` y `requirements-test.in` declaran los rangos de entrada;
`requirements.txt` y `requirements-test.txt` son locks compilados con
`pip-tools==7.7.0` y hashes. Se compilan en Linux para incluir dependencias
específicas de la imagen de despliegue y se instalan con verificación de hashes.
Para regenerar ambos locks desde `backend` en PowerShell:

```powershell
docker run --rm -v "${PWD}:/work" -w /work python:3.12-slim-bookworm sh -c "python -m pip install --no-cache-dir -r requirements-lock-tools.txt && pip-compile --generate-hashes --output-file=requirements.txt requirements.in && pip-compile --generate-hashes --output-file=requirements-test.txt requirements-test.in"
```

La suite usa la compatibilidad local `pgserver` para levantar PostgreSQL 16 en
Docker y se ejecuta desde `backend` con `python -m pytest`, tras
`python -m pip install --require-hashes -r requirements-test.txt`.
Algunos índices de paquetes/plataformas no ofrecen una distribución compatible
de `pgserver`; en ese caso falla la instalación de dependencias de prueba, pero
no la instalación ni la ejecución normal de la imagen de la aplicación.

## Configuración (variables de entorno del backend)

| Variable | Default | Descripción |
|---|---|---|
| DATABASE_URL | postgres local | Conexión SQLAlchemy (psycopg) |
| DB_RLS_ENABLED | true | Activa el contexto de aislamiento por tenant |
| DB_APPLY_SCHEMA_ON_START | false | En Compose el servicio `migrate` aplica el esquema |
| SCHEMA_VERSION_ESPERADA | 23 | Versión de esquema exigida por la API |
| STORAGE_BACKEND / STORAGE_DIR | local / `/data/uploads` | Almacenamiento local o `azure` |
| AZURE_STORAGE_ACCOUNT / AZURE_BLOB_CONN / AZURE_BLOB_CONTAINER | vacío / vacío / `docs` | Configuración de Azure Blob Storage |
| QUEUE_BACKEND / REDIS_URL | inproc / Redis local | `celery` usa Redis para trabajos en segundo plano |
| JWE_BACKEND / KEYS_DIR | local / `/data/keys` | Cifrado local o Azure Key Vault |
| IA_BACKEND / ANTHROPIC_API_KEY | simulada / vacío | Revisión simulada o `claude` |
| JWT_SECRET | valor de desarrollo | Usa un secreto único de al menos 32 bytes en producción |
| CORS_ORIGINS | http://localhost:3000 | Orígenes permitidos |
| SMTP_HOST / SMTP_PORT | vacío / 587 | Servidor SMTP; Gmail usa `smtp.gmail.com:587` |
| SMTP_USER / SMTP_PASSWORD | vacío / vacío | Cuenta remitente y contraseña de aplicación |
| EMAIL_FROM / FRONTEND_URL | vacío / http://localhost:3000 | Remitente y base pública para enlaces |

## Documentación y verificación

- `backend/DESPLIEGUE_AZURE.md`: guía de configuración y despliegue actual para
  Azure Container Apps.
- `Acredittia_Deploy_Local_Postgres.docx`: guía de despliegue local, alineada
  con el Compose y el esquema actual.
- OpenAPI generado desde el código: `http://localhost:8000/docs`.

Para ejecutar la suite del backend se requieren las dependencias de
`backend/requirements-test.txt`; las pruebas aplican el esquema PostgreSQL real
en un servidor efímero.
