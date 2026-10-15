# Guia de la vista de empresa de Acredittia

Fecha: 17 de septiembre de 2026

## 1. Objetivo de este documento

Este README explica como funciona la plataforma desde el punto de vista de una empresa contratista. Sirve como mapa para entender:

- que ve una empresa al iniciar sesion;
- que archivos controlan cada pantalla;
- como viajan los datos entre Next.js, FastAPI y PostgreSQL;
- que endpoints utiliza cada modulo;
- como se relacionan las tablas principales;
- donde se generan los datos de `DEMO SpA`;
- donde hacer cambios cuando se agregue o modifique una funcionalidad.

La cuenta demo utiliza exactamente la misma vista que una empresa real. La diferencia es que sus datos operativos son simulados.

---

## 2. Recorrido general de una empresa

```text
Usuario empresa
    |
    v
frontend/app/login/page.tsx
    |
    | POST /api/v1/auth/login
    v
backend/app/routers/auth.py
    |
    | JWT + refresh token + company_id
    v
frontend/lib/api.ts
    |
    | Authorization: Bearer <token>
    v
frontend/app/(app)/layout.tsx + components/Sidebar.tsx
    |
    v
Pagina seleccionada dentro de frontend/app/(app)/
    |
    v
frontend/lib/cliente.ts
    |
    | GET/POST/PATCH/DELETE /api/v1/...
    v
backend/app/routers/*.py
    |
    v
SQLAlchemy + RLS + filtros company_id
    |
    v
PostgreSQL
```

### 2.1 Login

La empresa inicia sesion con `POST /api/v1/auth/login`.

El backend busca el usuario por email, verifica la contrasena y devuelve:

- `access_token`: JWT usado en cada llamada;
- `refresh_token`: permite renovar la sesion;
- `user`: usuario, rol, empresa y, si corresponde, contrato asignado.

El frontend guarda estos datos en `localStorage` desde `frontend/lib/api.ts`.

### 2.2 Identidad y empresa activa

El JWT contiene el `company_id` del usuario. Para usuarios con rol `company` o `contract_admin`, el backend utiliza automaticamente esa empresa.

Un administrador puede operar temporalmente como otra empresa usando:

```text
sessionStorage.impersonar = <company_id>
```

`frontend/lib/api.ts` convierte ese valor en el header:

```text
X-Company-Id: <company_id>
```

El backend acepta ese header solo para usuarios con rol `admin`.

### 2.3 Aislamiento multiempresa

El aislamiento tiene dos capas:

1. Los routers agregan filtros explicitos por `company_id`.
2. PostgreSQL aplica Row Level Security mediante el contexto `app.company_id`.

La logica se encuentra principalmente en:

- `backend/app/deps.py`: resuelve usuario, rol y empresa activa.
- `backend/app/database.py`: fija el contexto de tenant en cada transaccion.
- `BASE/modelo_datos/04_rls.sql`: politicas RLS.
- `backend/app/main.py`: limpia el contexto al iniciar y terminar cada request.

---

## 3. Estructura del frontend de empresa

Ruta base: `BASE/app/frontend/`

### 3.1 Paginas principales

| Archivo | Ruta visible | Responsabilidad |
|---|---|---|
| `app/page.tsx` | `/` | Redirige a `/login`, `/admin` o `/dashboard`. |
| `app/login/page.tsx` | `/login` | Login, registro de empresa y usuario inicial con nombre, y solicitud de recuperacion de contrasena. |
| `app/(app)/layout.tsx` | Layout protegido | Verifica que exista una sesion y monta el sidebar. |
| `app/(app)/perfil/page.tsx` | `/perfil` | Perfil personal; para ADMIN en «Ver como empresa», perfil de la empresa (nombre/correo editables; RUT/estado de solo lectura). |
| `app/(app)/gestion-cuentas/page.tsx` | `/gestion-cuentas` | Listado paginado y administracion de roles/estado de cuentas asociadas; invitacion de cuentas existentes pendiente. |
| `components/Sidebar.tsx` | Navegacion lateral | Enlaces, empresa actual, impersonacion y cierre de sesion. |
| `components/ui.tsx` | Compartido | KPIs, tablas, modales, chips, spinner y paginacion. |

### 3.2 Modulos de la empresa

| Archivo | Ruta | Que muestra o modifica |
|---|---|---|
| `app/(app)/dashboard/page.tsx` | `/dashboard` | Inicio, KPI, cumplimiento, acreditaciones, vencimientos y actividad. |
| `app/(app)/contratos/page.tsx` | `/contratos` | Listado y alta de contratos. |
| `app/(app)/contratos/[id]/page.tsx` | `/contratos/:id` | Detalle, matriz, documentos, personal, equipos, alertas e historial del contrato. |
| `app/(app)/faenas/page.tsx` | `/faenas` | Catalogo de faenas, estadisticas de la empresa y plataformas del mandante. |
| `app/(app)/personal/page.tsx` | `/personal` | Listado y alta de trabajadores. |
| `app/(app)/equipos/page.tsx` | `/equipos` | Listado y alta de equipos o vehiculos. |
| `app/(app)/alertas/page.tsx` | `/alertas` | Alertas activas, estado y lectura. |
| `app/(app)/admin/page.tsx` | `/admin` | Back-office de plataforma. No es la vista normal de empresa. |

### 3.3 Cliente HTTP

`frontend/lib/api.ts` contiene la infraestructura comun:

- guarda y recupera tokens;
- agrega `Authorization`;
- agrega `X-Company-Id` cuando hay impersonacion;
- renueva el access token ante un `401`;
- transforma errores de API a `ApiError`;
- serializa query params;
- ofrece helpers de paginacion;
- centraliza carga y descarga de archivos.

`frontend/lib/cliente.ts` contiene los metodos agrupados por modulo. No dibuja la interfaz. Por ejemplo:

```ts
Api.dashboard.kpis()
Api.contratos.listar({ page_size: 25 })
Api.faenas.listar({ activa: true })
Api.personal.crear(body)
```

La pantalla visual esta en `app/(app)/*/page.tsx`; el metodo HTTP normalmente esta en `lib/cliente.ts`.

---

## 4. Estructura del backend

Ruta base: `BASE/app/backend/app/`

### 4.1 Arranque y registro de routers

`main.py` registra todos los routers bajo el prefijo `/api/v1`.

Los routers mas relevantes para la empresa son:

- `routers/auth.py`
- `routers/company.py`
- `routers/dashboard.py`
- `routers/contratos.py`
- `routers/faenas.py`
- `routers/sujetos.py`
- `routers/personas.py`
- `routers/documentos.py`
- `routers/alertas.py`
- `routers/actividad.py`
- `routers/calendario.py`
- `routers/reportes.py`
- `routers/integraciones.py`

### 4.2 Dependencias de seguridad

`deps.py` contiene las dependencias transversales:

- `get_current_user`: valida JWT y carga el usuario.
- `get_company_id`: determina la empresa efectiva.
- `require_company`: permite operaciones de empresa.
- `require_admin`: limita operaciones al administrador.
- `contract_scope`: limita a un contrato a los usuarios `contract_admin`.
- `paginacion`: normaliza pagina, tamano, orden y busqueda.

### 4.3 Reglas de checklist

`services/checklist.py` es una pieza central. Decide que documentos aplican a:

- una empresa dentro de un contrato;
- un trabajador;
- un conductor;
- un equipo.

La resolucion de requisitos sigue esta prioridad:

1. override especifico del contrato;
2. requisitos asociados al cargo;
3. plantillas especificas de la faena;
4. plantillas base globales;
5. requisitos extra del contrato.

Tambien calcula estados documentales:

- `ok`;
- `falta`;
- `porvenc`;
- `venc`.

---

## 5. Endpoints de la vista de empresa

Todos los endpoints siguientes usan el prefijo `/api/v1`.

### 5.1 Autenticacion y cuenta

Router: `backend/app/routers/auth.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `POST` | `/auth/login` | Iniciar sesion. |
| `POST` | `/auth/register` | Registrar empresa y primer usuario. |
| `POST` | `/auth/refresh` | Renovar tokens. |
| `POST` | `/auth/logout` | Revocar refresh token. |
| `GET` | `/auth/me` | Consultar usuario actual. |
| `PATCH` | `/auth/me` | Editar perfil o contrasena. |
| `POST` | `/auth/password/forgot` | Solicitar recuperacion. |
| `POST` | `/auth/password/reset` | Restablecer contrasena. |

### 5.2 Empresa y usuarios

Router: `backend/app/routers/company.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/company` | Perfil de la empresa activa. |
| `PATCH` | `/company` | Editar nombre o email. |
| `GET` | `/company/usuarios` | Listar usuarios de la empresa. |
| `POST` | `/company/usuarios` | Invitar usuario o administrador de contrato. |
| `PATCH` | `/company/usuarios/{id}` | Editar rol, contrato o estado. |
| `DELETE` | `/company/usuarios/{id}` | Desactivar usuario. |

### 5.3 Dashboard e inicio

Router: `backend/app/routers/dashboard.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/dashboard/kpis` | Contratos, faenas, personal, equipos, documentos y alertas. |
| `GET` | `/dashboard/cumplimiento-contratos` | Cumplimiento contrato por contrato. |
| `GET` | `/dashboard/acreditaciones-estado` | Distribucion de acreditados, pendientes y vencidos. |
| `GET` | `/dashboard/actividad` | Feed de actividad reciente. |
| `GET` | `/dashboard/proximos-vencimientos` | Documentos que vencen pronto. |
| `GET` | `/dashboard/tendencia` | Historico de cumplimiento desde snapshots. |

La pantalla correspondiente es `frontend/app/(app)/dashboard/page.tsx`.

### 5.4 Contratos

Router: `backend/app/routers/contratos.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/contratos` | Listar contratos de la empresa. |
| `POST` | `/contratos` | Crear contrato e instanciar documentos de empresa. |
| `GET` | `/contratos/{id}` | Detalle y estadisticas. |
| `PATCH` | `/contratos/{id}` | Editar contrato. |
| `DELETE` | `/contratos/{id}` | Eliminar contrato y datos asociados. |
| `GET` | `/contratos/{id}/documentos` | Documentos del contrato. |
| `GET` | `/contratos/{id}/personal` | Personal del contrato. |
| `GET` | `/contratos/{id}/equipos` | Equipos del contrato. |
| `GET` | `/contratos/{id}/alertas` | Alertas del contrato. |
| `GET` | `/contratos/{id}/historial` | Actividad del contrato. |
| `POST` | `/contratos/analizar` | Encolar analisis IA de contrato. |
| `GET` | `/contratos/{id}/matriz` | Matriz sujeto por requisito. |
| `GET/POST/PATCH` | `/contratos/{id}/requisitos...` | Requisitos personalizados. |

Un contrato es la unidad principal de acreditacion: relaciona empresa, faena, personal, equipos, documentos, requisitos, alertas y cumplimiento.

### 5.5 Faenas y plataformas

Router: `backend/app/routers/faenas.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/faenas` | Catalogo global con estadisticas de la empresa. |
| `GET` | `/faenas/{id}` | Detalle de faena y plataformas. |
| `GET` | `/faenas/{id}/plataformas` | Plataformas del mandante con acceso de la empresa. |
| `PATCH` | `/faenas/{id}/plataformas/{pid}/acceso` | Marcar acceso como solicitado o activo. |
| `GET` | `/catalogo/tipos-equipo` | Tipos permitidos de equipo. |
| `GET` | `/catalogo/requisitos-templates` | Plantillas activas. |
| `GET` | `/catalogo/ejemplos` | Ejemplos de documentos. |
| `GET` | `/catalogo/requisitos-terreno` | Requisitos de terreno. |
| `GET` | `/catalogo/laboratorios` | Proveedores de laboratorio. |
| `GET` | `/catalogo/talleres` | Talleres homologados. |
| `GET` | `/catalogo/proveedores-gps` | Proveedores GPS. |

Las faenas y plantillas son catalogos globales. Los contratos y accesos a plataformas son datos propios de cada empresa.

### 5.6 Personal y equipos

Router: `backend/app/routers/sujetos.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/personal` | Listar trabajadores. |
| `POST` | `/personal` | Crear trabajador y sus documentos. |
| `GET` | `/personal/{id}` | Detalle del trabajador. |
| `GET` | `/personal/{id}/documentos` | Documentos del trabajador. |
| `PATCH` | `/personal/{id}` | Editar trabajador. |
| `POST` | `/personal/{id}/baja` | Dar de baja. |
| `DELETE` | `/personal/{id}` | Eliminar trabajador. |
| `GET` | `/equipos` | Listar equipos. |
| `POST` | `/equipos` | Crear equipo y sus documentos. |
| `GET` | `/equipos/{id}` | Detalle del equipo. |
| `GET` | `/equipos/{id}/documentos` | Documentos del equipo. |
| `PATCH` | `/equipos/{id}` | Editar equipo. |
| `POST` | `/equipos/{id}/baja` | Dar de baja. |
| `DELETE` | `/equipos/{id}` | Eliminar equipo. |

`routers/personas.py` contiene endpoints de apoyo para busquedas de identidad y flota.

### 5.7 Documentos, IA y alertas

Routers: `documentos.py`, `ia.py`, `alertas.py`

| Metodo | Endpoint | Uso |
|---|---|---|
| `GET` | `/documentos` | Listar documentos filtrados. |
| `GET` | `/documentos/{id}` | Ver detalle. |
| `PATCH` | `/documentos/{id}` | Editar estado o vencimiento. |
| `POST` | `/documentos/{id}/upload-url` | Solicitar URL de carga. |
| `POST` | `/documentos/{id}/archivos` | Confirmar archivo subido. |
| `GET` | `/documentos/{id}/archivos/{archivo_id}/download-url` | Descargar. |
| `GET` | `/alertas` | Listar alertas. |
| `GET` | `/alertas/resumen` | Resumen de alertas no leidas. |
| `PATCH` | `/alertas/{id}` | Actualizar alerta. |
| `POST` | `/alertas/marcar-leidas` | Marcar alertas como leidas. |

El flujo normal de archivo es: solicitar URL, subir archivo al storage, confirmar archivo y esperar la revision IA cuando corresponda.

---

## 6. Modelo de datos principal

Los scripts estan en `BASE/modelo_datos/`:

- `01_esquema.sql`: tablas, enums y relaciones base.
- `02_indices.sql`: indices.
- `03_triggers.sql`: auditoria y reglas automaticas.
- `04_rls.sql`: Row Level Security por empresa.
- `05_verificacion.sql`: verificaciones del esquema.
- `06_migracion_v11.sql`: cambios de version 1.1.
- `07_consola_interna.sql`: tablas para la consola Ops.
- `08_funciones_consola.sql`: funciones y metricas internas.

### 6.1 Tablas de identidad y tenant

- `companies`: empresas, estado, RUT y marca `es_demo`.
- `users`: usuarios, roles, empresa y contrato opcional.
- `refresh_tokens`: sesiones renovables.
- `password_reset_tokens`: recuperacion de contrasena.

### 6.2 Tablas de catalogo

- `faenas`: faenas o centros de trabajo.
- `faena_plataformas`: plataformas de cada mandante.
- `requisito_templates`: plantillas de requisitos.
- `doc_ejemplos`: ejemplos y referencias de documentos.
- `requisitos_terreno`: requisitos especificos de terreno.
- `proveedores_catalogo`: laboratorios, talleres y GPS.
- `planes`: planes comerciales.

### 6.3 Tablas operativas de empresa

- `contratos`: contrato de una empresa en una faena.
- `company_faena_plataformas`: acceso de una empresa a una plataforma.
- `contrato_plataformas`: plataformas materializadas en un contrato.
- `contrato_requisitos`: requisitos personalizados del contrato.
- `contrato_plantilla_overrides`: reemplazos de plantillas por contrato.
- `sujetos`: trabajadores y equipos.
- `cargos`: cargos de trabajadores.
- `cargo_requisitos`: requisitos asociados a cargos.
- `documentos`: requisitos instanciados para empresa, trabajador o equipo.
- `documento_archivos`: archivos almacenados de cada documento.
- `licencias_internas`: expedientes internos, especialmente EMSIPOR.

### 6.4 Tablas de operacion y seguimiento

- `ia_reviews`: revisiones de documentos o contratos por IA.
- `ia_hallazgos`: hallazgos de una revision IA.
- `alertas`: alertas de vencimiento, IA o integraciones.
- `actividad`: historial de acciones.
- `eventos_calendario`: calendario de la empresa.
- `reportes`: reportes generados.
- `reportes_programados`: reportes recurrentes.
- `integraciones`: conectores externos por empresa.
- `sync_logs`: historial de sincronizaciones.
- `notificacion_preferencias`: preferencias de notificacion.
- `bitacora_cambios`: cambios auditables.

### 6.5 Relaciones principales

```text
companies
  |
  +-- users
  +-- contratos
  |     |
  |     +-- faenas
  |     +-- sujetos
  |     |     +-- documentos
  |     |     +-- licencias_internas
  |     +-- contrato_requisitos
  |     +-- contrato_plataformas
  |
  +-- documentos
  |     +-- documento_archivos
  |     +-- ia_reviews
  |           +-- ia_hallazgos
  +-- alertas
  +-- actividad
  +-- integraciones
        +-- sync_logs

faenas
  +-- faena_plataformas
  +-- requisito_templates

requisito_templates
  +-- documentos
  +-- cargo_requisitos
```

---

## 7. Datos de Demo SpA

### 7.1 Cuenta y empresa

`backend/app/seeds.py` crea:

```text
Empresa: DEMO SpA
RUT: 76.111.222-8
Usuario: demo@acredittia.cl
Contrasena: Demo2026!
Rol: company
Company.es_demo: true
```

El mismo seed tambien crea el catalogo base de faenas, plataformas, ejemplos y plantillas.

### 7.2 Datos operativos simulados

`backend/app/routers/admin.py` contiene las constantes y la funcion `_sembrar_demo()` que genera:

- contrato `CTR-DEMO-001` en Los Pelambres;
- contrato `CTR-DEMO-002` en Minera Centinela;
- seis trabajadores;
- cuatro equipos;
- documentos de empresa, personal y equipos;
- expedientes EMSIPOR para conductores;
- estados mixtos para que el dashboard muestre cumplimiento y pendientes.

El endpoint de reinicio es:

```text
POST /api/v1/admin/companies/{company_id}/reset-demo
```

Solo funciona cuando `companies.es_demo = true`.

### 7.3 Importante sobre el arranque

El `lifespan` de `backend/app/main.py` ejecuta `seeds.run(db)` al iniciar la API. Eso garantiza la empresa demo, el usuario y el catalogo base.

La poblacion operativa detallada de contratos, trabajadores y equipos esta separada en `admin.py` y se ejecuta mediante `reset-demo`. Si se necesita que una base nueva aparezca completamente poblada sin pulsar el boton de reinicio, hay que llamar ese proceso durante el seed inicial o crear un seed operativo idempotente separado.

---

## 8. Como trabajar una funcionalidad nueva

### Si cambia la apariencia

Editar la pagina de `frontend/app/(app)/...` y reutilizar componentes de `frontend/components/`.

### Si cambia una llamada existente

Editar el metodo correspondiente en `frontend/lib/cliente.ts`. Si cambia autenticacion, headers o manejo comun, revisar `frontend/lib/api.ts`.

### Si cambia el calculo de datos

Editar el router backend responsable:

- dashboard: `routers/dashboard.py`;
- contratos: `routers/contratos.py`;
- faenas: `routers/faenas.py`;
- personal/equipos: `routers/sujetos.py`;
- documentos: `routers/documentos.py`.

### Si cambia la creacion automatica de requisitos

Editar `services/checklist.py` y verificar tambien las plantillas en `requisito_templates`.

### Si cambia la estructura de datos

Actualizar, en orden:

1. modelo SQL en `BASE/modelo_datos/`;
2. modelo SQLAlchemy en `backend/app/models.py`;
3. router o servicio que utiliza la tabla;
4. tipos TypeScript en `frontend/lib/tipos.ts`;
5. cliente en `frontend/lib/cliente.ts`;
6. pantalla frontend;
7. pruebas backend y frontend disponibles.

Nunca agregar un endpoint de empresa sin revisar el filtro `company_id`, `get_company_id()` y las politicas RLS.

---

## 9. Como ejecutar localmente

### Con Docker

```bash
cd BASE/app
docker compose up --build
```

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Documentacion OpenAPI: `http://localhost:8000/docs`

### Sin Docker

Backend:

```bash
cd BASE/app/backend
pip install -r requirements.txt
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/acredittia \
SCHEMA_DIR=../../modelo_datos STORAGE_DIR=/tmp/uploads \
uvicorn app.main:app --reload
```

Frontend:

```bash
cd BASE/app/frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

### Credenciales de prueba

```text
Empresa demo: demo@acredittia.cl / Demo2026!
Administrador: admin@acredittia.cl / Admin2026!
```

---

## 10. Checklist rapido para depurar una pantalla

1. Abrir la pagina en `frontend/app/(app)/...`.
2. Identificar la llamada `Api.*` que carga los datos.
3. Buscar ese metodo en `frontend/lib/cliente.ts`.
4. Confirmar el endpoint en el router backend.
5. Revisar `get_company_id()` y el filtro por tenant.
6. Revisar las tablas consultadas en `01_esquema.sql`.
7. Revisar RLS si la respuesta llega vacia o aparece un error de permisos.
8. Revisar `seeds.py` o `admin.py` si el problema es falta de datos demo.
9. Ejecutar la prueba del modulo afectado antes de cambiar otros archivos.

La regla practica es: `page.tsx` presenta, `cliente.ts` transporta, `router.py` decide, `checklist.py` genera requisitos y PostgreSQL persiste y aisla los datos.


---

## 11. Estado de prioridades ADMIN

Esta seccion resume que capacidades administrativas ya existen y que queda por
implementar. Sirve como guia de trabajo para no confundir una funcionalidad
parcial con una funcionalidad terminada.

### 11.1 Dashboard global

**Estado: Parcial.**

Ya existe:

- cantidad global de empresas, contratos, trabajadores y usuarios;
- porcentaje de acreditacion y documentos correctos;
- actividad y crecimiento mensual de usuarios;
- clientes activos, altas y bajas;
- consola de sistemas, procesos, incidentes y disponibilidad.

Estado actual y pendientes:

- existe un dashboard global bajo `/admin` con contadores, acreditacion,
    documentos, actividad y accesos a las areas administrativas;
- los universos de algunos contadores y la definicion de crecimiento de
    adopcion aun deben acordarse; la actividad por eventos no equivale a nuevas
    empresas, nuevos usuarios ni tiempo efectivo de uso;
- MRR y crecimiento comercial se presentan en Metricas SaaS, no como
    crecimiento de adopcion del dashboard.

Archivos principales:

- `backend/app/routers/admin.py`;
- `backend/app/routers/admin_ops.py`;
- `frontend/app/(app)/admin/page.tsx`;
- `frontend/app/ops/`.

### 11.2 Gestion global de empresas

**Estado: Implementado en gran parte.**

Ya existe:

- listado paginado de empresas;
- filtros por estado y empresa demo;
- busqueda por nombre, RUT y email;
- la tabla «Empresas (cuentas)» presenta industria y estado de cuenta (al dia,
    en riesgo, moroso o no aplica);
- contratos, usuarios, trabajadores, equipos y alertas activas por empresa;
- porcentaje de cumplimiento y documentos por estado;
- plan, suscripcion, actividad, ultima actividad y nivel de uso en la consola
    Ops;
- acceso al detalle de cada cliente, con cuentas/perfiles y responsables por
    contrato, sin listar sus documentos personales en la tabla general.

Pendiente o recomendable:

- revisar si el RUT debe ocultarse o limitarse en listados globales;
- definir una politica explicita de minimizacion de datos para el detalle de
    empresa.

Archivos principales:

- `backend/app/routers/admin.py`;
- `backend/app/routers/admin_ops.py`;
- `frontend/app/(app)/admin/page.tsx`.

### 11.3 Buscador global

**Estado: Implementado parcialmente; validacion y permisos por completar.**

Ya existe `GET /api/v1/admin/search` y la vista global `/admin/busqueda`.
Busca empresas, contratos, trabajadores/personas, equipos y usuarios; aplica
filtros por categoria y filtros especificos. Los filtros de cargo y tipo de
equipo se cargan desde catalogos. Se puede ejecutar una busqueda sin texto si
hay filtros especificos; sin ellos se requieren al menos dos caracteres.
Empresas y sujetos se pueden localizar por RUT, pero el RUT no se devuelve en
los resultados y las cuentas de acceso no tienen RUT propio.

La ficha agregada se expande bajo la fila seleccionada, se mantiene una sola
abierta y se descartan respuestas tardias al cambiar la consulta o la fila, o
al cerrar la ficha. La interfaz agrupa las listas de resultados en botones
desplegables por categoria; esto no sustituye la autorizacion por categoria en
el servidor, que sigue pendiente de validacion.

Pendiente: acordar el tratamiento de usuarios sin empresa, definir y verificar
la matriz de permisos por categoria en servidor, y completar pruebas/recorrido
visual de filtros, limites, expansion y cambios rapidos de seleccion. Ver
`documentacion/SRS.md` RF-BUS-01/02 y `documentacion/VALIDACION_ACTUAL.md`.

### 11.4 Metricas SaaS

**Estado: Parcial.**

Ya existe:

- empresas activas, trial, morosas y canceladas;
- usuarios totales y activos en una ventana configurable;
- usuarios sin acceso durante 90 dias;
- actividad mensual y evolucion de usuarios;
- planes, MRR, altas, bajas, churn y series comerciales; los desgloses visibles
  de usuarios por plan e industria se encuentran ahora en Salud de clientes;
- procesos y ejecuciones de la plataforma.

Falta:

- telemetria observada para calcular duracion real de sesiones y tiempo de uso;
- una definicion unica de "usuario activo" que incluya claramente login,
    actividad y sesiones;
- fuente y fecha del valor UF en cada respuesta y cobertura de periodos/monedas;
- mantener diferenciadas las revisiones de IA procesadas y la cantidad de
    documentos unicos.

La vista de Salud de clientes presenta los indicadores de uso/adopcion,
clientes de baja actividad con clasificacion de sin usuarios, usuarios sin
actividad o baja actividad, y usuarios por plan e industria. Los detalles de
riesgos son desplegables y los graficos incluyen ayudas informativas. El tiempo
de uso se etiqueta como estimado. El detalle de
validacion y criterios abiertos esta en RF-MET-01/02/03 del SRS.

Archivos principales:

- `backend/app/routers/admin_ops.py`;
- `BASE/modelo_datos/07_consola_interna.sql`;
- `BASE/modelo_datos/08_funciones_consola.sql`;
- `backend/app/models_ops.py`;
- `backend/app/services/ops.py`.

### 11.5 Alertas y salud de clientes

**Estado: Parcial.**

Ya existe:

- cumplimiento por empresa;
- documentos agrupados por estado;
- alertas activas por empresa;
- clientes con baja actividad o sin acceso reciente;
- estado de API, base de datos, workers, storage, IA e integraciones;
- incidentes operacionales y ejecuciones de procesos con error.

Salud de clientes clasifica la baja actividad como sin usuarios, usuarios sin
actividad o baja actividad. Esta clasificacion, los detalles plegables y las
ayudas explicativas no cierran por si solas los requisitos de alertas y salud.

Falta o debe validarse:

- alertas globales accionables para empresas bajo un umbral de acreditacion;
- alertas para contratos con muchos requisitos pendientes;
- alertas globales de documentos vencidos;
- validar umbrales, casos sin datos y cobertura de empresas sin usuarios o con
    usuarios sin eventos en el flujo de salud;
- totales/paginacion de listas limitadas y sondas operacionales que verifiquen
    disponibilidad real.

### 11.6 Usuarios, roles y permisos

**Estado: Parcial, con aislamiento entre empresas implementado.**

Ya existe:

- roles `admin`, `company` y `contract_admin`;
- usuarios administrables por empresa;
- acceso de `contract_admin` limitado a un contrato;
- ultimo acceso mediante `last_login_at`;
- proteccion del ultimo administrador activo de una empresa;
- validacion de que un contrato pertenece a la empresa antes de asignarlo;
- bloqueo para que un usuario de una empresa no gestione usuarios de otra.

En el registro se solicita el nombre del usuario inicial, separado de la razon
social. `/perfil` edita el perfil personal; si ADMIN usa «Ver como empresa», la
misma ruta muestra y permite editar el nombre/correo de la empresa, mientras
RUT y estado son de solo lectura. La API usa el `X-Company-Id` de la
impersonacion para operar sobre la empresa seleccionada.

`/gestion-cuentas` lista, busca, pagina y administra las cuentas del tenant.
`/contratos` muestra Responsables de contrato a `company` y a ADMIN con empresa
impersonada. Se puede asignar una cuenta `company` como `contract_admin` con
confirmacion doble; el backend impide dejar a la empresa sin otro usuario
`company` activo (`ULTIMO_ADMINISTRADOR`). Las cuentas `contract_admin`
existentes se pueden reasignar entre contratos. La invitacion/aceptacion de
cuentas ya existentes no esta implementada; `POST /company/usuarios` crea
usuarios nuevos y el envio/canje del token de activacion por email sigue
pendiente.

En la consola ADMIN, los cambios de rol, empresa o contrato requieren una
confirmacion que explica consecuencias y un motivo obligatorio. El registro
auditable conserva actor, motivo y valores anteriores/nuevos; el cambio
invalida las sesiones del usuario. La validacion de las pruebas backend
especificas y la cobertura integral de auditoria siguen pendientes.

Falta:

- completar altas/invitaciones y activacion por correo;
- permisos mas finos que los tres roles actuales;
- matriz formal de permisos por recurso y accion;
- flujo de aprobacion y revision de accesos excepcionales del administrador.

La gestion administrativa global ya dispone de listado, cambios de estado,
revocacion y reactivacion. Sigue pendiente la paginacion para mas de 100
usuarios y la validacion integral de permisos y alcance. Estas funciones no
deben confundirse con las altas/invitaciones del portal de empresa.

Archivos principales:

- `backend/app/routers/company.py`;
- `backend/app/routers/auth.py`;
- `backend/app/deps.py`;
- `BASE/modelo_datos/01_esquema.sql`;
- `BASE/modelo_datos/04_rls.sql`.

### 11.7 Auditoria y trazabilidad

**Estado: Parcial.**

Ya existe:

- tabla `actividad` append-only para acciones de negocio;
- tabla `bitacora_cambios` escrita por triggers en tablas criticas;
- registro de creaciones, modificaciones, bajas, usuarios, contratos,
    documentos, permisos e integraciones;
- actor, empresa, entidad, fecha y modulo en gran parte de los eventos;
- auditoria de consultas a indicadores confidenciales de Ops;
- auditoria de operaciones internas de la consola Ops.

Falta:

- registrar siempre el login exitoso y los intentos fallidos;
- registrar la descarga de documentos con usuario, archivo, fecha y empresa;
- registrar la visualizacion de informacion personal sensible;
- exigir y guardar el motivo de accesos excepcionales del Admin;
- un visor global de auditoria con filtros de actor, empresa, accion, recurso
    sensible y rango de fechas.

Archivos principales:

- `backend/app/services/actividad.py`;
- `backend/app/routers/actividad.py`;
- `BASE/modelo_datos/03_triggers.sql`;
- `BASE/modelo_datos/01_esquema.sql`;
- `backend/app/services/ops.py`.

### 11.8 Seguridad y aislamiento de datos

**Estado: Implementado en gran parte, con faltantes de auditoria y minimo
privilegio.**

Ya existe:

- aislamiento por `company_id`;
- RLS en PostgreSQL;
- contexto de tenant por transaccion;
- filtros explicitos en las consultas de negocio;
- restricciones por rol y por contrato;
- comprobacion de pertenencia de documentos, archivos y contratos;
- URLs firmadas y de corta duracion para archivos;
- rutas de blobs que incluyen el `company_id`;
- exportaciones filtradas por la empresa activa.

Falta o debe reforzarse:

- auditar descargas y accesos a documentos sensibles;
- auditar quien, cuando y por que uso una impersonacion Admin;
- aplicar permisos mas granulares al administrador global;
- minimizar RUT, documentos personales y otros datos sensibles en dashboards;
- revisar que cada exportacion registre actor, filtros, recurso y descarga;
- contar con pruebas automatizadas de no acceso cruzado para cada nuevo recurso.

### 11.9 Orden recomendado de trabajo

1. **Permisos y aislamiento:** matriz de acciones, alcance ADMIN y pruebas
     negativas por empresa/contrato.
2. **Auditoria:** login, cambios administrativos, lecturas sensibles,
     descargas, impersonacion y exportaciones.
3. **Buscador global:** cerrar alcance/permisos por categoria y validar
     filtros, ficha y limites.
4. **Salud de clientes y operacion:** umbrales, listas completas, sondas
     verificables y recorrido distribuido Celery.
5. **Metricas y dashboard:** acordar universos/definiciones, completar fuente
     de UF y decidir si se requiere telemetria real de sesiones.
6. **Portal de empresa:** completar invitaciones/activacion por correo y
     recorridos de mutaciones.

### 11.10 Resumen rapido

**Ya esta:** portal multiempresa y roles basicos; contratos, trabajadores,
equipos, documentos, cumplimiento, actividad; consola ADMIN con dashboard,
gestion de empresas con industria/estado de cuenta, salud de clientes,
buscador por categorias, metricas SaaS, usuarios y operacion;
registro del nombre del usuario inicial y edicion de perfil.

**Falta cerrar o validar:** permisos finos y aislamiento con identidades de
minimo privilegio; auditoria integral de autenticacion y accesos sensibles;
validacion de interfaces y recorridos; invitaciones por correo; telemetria real
de sesiones si se aprueba; y los criterios de salud, sondas y listas completas.
El detalle de estados, limites y evidencia vigente esta en `documentacion/SRS.md`
y `documentacion/VALIDACION_ACTUAL.md`.
