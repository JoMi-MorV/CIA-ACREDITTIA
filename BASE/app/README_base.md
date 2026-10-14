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
├── frontend/              # Next.js 14 + React 18
└── ../modelo_datos/       # esquema, RLS, índices, funciones y migraciones
```

El servicio `migrate` aplica los scripts de `../modelo_datos/` antes de iniciar
la API y los workers. PostgreSQL no ejecuta el esquema desde su inicialización:
la versión actual del esquema es **11**. La API comprueba la versión requerida
al arrancar.

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

## Demo temporal por ngrok

El perfil `docker-compose.ngrok.yml` publica únicamente el frontend por ngrok,
sin Basic Auth adicional en el túnel; el login de Acredittia permanece activo.
PostgreSQL, Redis, API y el inspector de ngrok quedan ligados a `127.0.0.1`.
Es exclusivamente para una demostración temporal con
datos sintéticos. El Compose base usa roles de desarrollo y semillas/cuentas
demo conocidas: no cargar información real ni tratarlo como despliegue de
producción. La URL del túnel queda accesible públicamente a quien la conozca.

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

Comparte la URL HTTPS con cuidado: sin Basic Auth, cualquier persona que la
conozca llegará al login de Acredittia. No distribuyas cuentas demo conocidas.
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

## Consola administrativa

La consola interna ofrece **Dashboard global**, **Sistemas y procesos**,
**Indicadores**, **Gestión de empresas**, **Usuarios**, **Salud de clientes**,
**Buscador global** y **Auditoría**. Sus funciones incluyen:

- Gestión de empresas (cuentas), con industria, estado de cuenta, actividad y
  detalle expandible de usuarios/perfiles y responsables por contrato.
- Indicadores de negocio y financieros, incluyendo MRR, churn, retención y
  relación LTV/CAC. El CAC necesita datos configurados para poder calcular la
  relación. Actualmente la consola no tiene una sección general de Ajustes para
  administrar precios o supuestos financieros.
- Salud de clientes con detalle desplegable para riesgos y métricas de
  uso/adopción, incluyendo usuarios por plan e industria.
- Buscador global con botones desplegables por categoría y filtros de referencia.
- Ayudas contextuales en gráficos, KPI y tablas para explicar su cálculo y
  significado.
- Administración de usuarios: cambios de rol, empresa o contrato muestran el
  impacto, exigen un motivo de al menos 12 caracteres y se registran con actor,
  fecha y valores anteriores/nuevos. Estos cambios invalidan las sesiones
  activas del usuario. La auditoría de permisos presenta el motivo y los cambios.

La ayuda contextual explica los valores que presenta la interfaz; no reemplaza
la documentación de las fórmulas, límites y contratos de la API.

## Desarrollo sin Docker

```powershell
# API (terminal 1; desde la raíz del proyecto)
Set-Location .\BASE\app\backend
python -m pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+psycopg://postgres:postgres@localhost:5432/acredittia"
$env:SCHEMA_DIR = "..\..\modelo_datos"
$env:STORAGE_DIR = "$env:TEMP\uploads"
python -m migrate.run
python -m uvicorn app.main:app --reload

# Frontend (terminal 2; desde la raíz del proyecto)
Set-Location .\BASE\app\frontend
npm install
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```

La base PostgreSQL debe existir y aceptar la conexión indicada. Ejecuta el
frontend en una terminal separada mientras la API permanece activa.

La imagen Docker instala solo las dependencias de ejecución desde
`requirements.txt`. Las dependencias de pruebas están separadas en
`requirements-test.txt`; la suite usa `pgserver` para levantar un PostgreSQL
efímero y se ejecuta desde `backend` con `python -m pytest`, tras
`python -m pip install -r requirements-test.txt`.
Algunos índices de paquetes/plataformas no ofrecen una distribución compatible
de `pgserver`; en ese caso falla la instalación de dependencias de prueba, pero
no la instalación ni la ejecución normal de la imagen de la aplicación.

## Configuración (variables de entorno del backend)

| Variable | Default | Descripción |
|---|---|---|
| DATABASE_URL | postgres local | Conexión SQLAlchemy (psycopg) |
| DB_RLS_ENABLED | true | Activa el contexto de aislamiento por tenant |
| DB_APPLY_SCHEMA_ON_START | false | En Compose el servicio `migrate` aplica el esquema |
| SCHEMA_VERSION_ESPERADA | 11 | Versión de esquema exigida por la API |
| STORAGE_BACKEND / STORAGE_DIR | local / `/data/uploads` | Almacenamiento local o `azure` |
| AZURE_STORAGE_ACCOUNT / AZURE_BLOB_CONN / AZURE_BLOB_CONTAINER | vacío / vacío / `docs` | Configuración de Azure Blob Storage |
| QUEUE_BACKEND / REDIS_URL | inproc / Redis local | `celery` usa Redis para trabajos en segundo plano |
| JWE_BACKEND / KEYS_DIR | local / `/data/keys` | Cifrado local o Azure Key Vault |
| IA_BACKEND / ANTHROPIC_API_KEY | simulada / vacío | Revisión simulada o `claude` |
| JWT_SECRET | valor de desarrollo | Usa un secreto único de al menos 32 bytes en producción |
| CORS_ORIGINS | http://localhost:3000 | Orígenes permitidos |

## Documentación y verificación

- `backend/DESPLIEGUE_AZURE.md`: guía de configuración y despliegue actual para
  Azure Container Apps.
- `backend/RUPTURAS.md`: registro histórico de cambios incompatibles de API
  (v1.1); no es un inventario completo de la API actual.
- `Acredittia_Deploy_Local_Postgres.docx`: guía de despliegue local, alineada
  con el Compose y el esquema actual.
- OpenAPI generado desde el código: `http://localhost:8000/docs`.

Para ejecutar la suite del backend se requieren las dependencias de
`backend/requirements-test.txt`; las pruebas aplican el esquema PostgreSQL real
en un servidor efímero.
