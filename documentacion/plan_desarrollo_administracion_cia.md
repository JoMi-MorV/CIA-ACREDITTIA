# Plan de Desarrollo (8 Días) — Equipo Administración (`CIA-ACREDITTIA-main`)

**Fecha de Inicio:** Día 1 (2026-11-01) · **Fusión:** Día 4 (2026-11-04) · **Cierre:** Día 8 (2026-11-08)  
**Repositorio Origen:** `c:\Users\Cristobal\Downloads\Universidad\GPI\Proyecto Acredittia\CIA-ACREDITTIA-main`  
**Objetivo del Equipo:** Promover la aplicación desde `BASE/app/` y `BASE/modelo_datos/` a la raíz del repositorio, aislar todos los módulos de la Consola Interna de Operaciones bajo el namespace `ops/` (Backend y Frontend Next.js App Router `(ops)`), renumerar sus scripts SQL a `19`..`22`, fusionar con `Acredittia-` en el Día 4 sobre la misma base de datos PostgreSQL 16 + `pgvector` (versión `22`), ejecutar QA de consola y seguridad (Días 5–7) y documentar la operación y gobernanza (Día 8).

---

## Estado de revisión de la documentación — 2026-11-04

Este documento describe el **plan objetivo de fusión**. Antes de ejecutar las
tareas debe actualizarse contra el repositorio real disponible:

| Hallazgo comprobado en `CIA-ACREDITTIA-main` | Impacto en el plan |
|---|---|
| El código aún usa la estructura `BASE/app/` y `BASE/modelo_datos/` | Las tareas 1.1 a 3.1 requieren ejecución real; no asumirlas completadas. |
| La versión esperada del esquema es `15`, definida en `app/database.py` | No declarar la versión `22` hasta fusionar las migraciones de Plataforma y renumerar Administración. |
| Los scripts Administración existentes llegan a la versión `15` (`07` Consola hasta `15` Acceso excepcional) | Renumerar `19`..`22` solo dentro de una secuencia unificada acordada con Plataforma. |
| `sonner` no aparece en `frontend/package.json` | Agregarlo antes de incluirlo como dependencia obligatoria. |
| `pgserver` oficial no está declarado ni hay una librería PyPI disponible según `requirements-test.txt` | Mantener la compatibilidad local existente; no ejecutar `backend/pgserver/__init__.py` en Python. |
| `pytest` y `httpx` están aislados en `requirements-test.txt`, y el frontend no tiene scripts `test` | Deben incorporarse al alcance real antes de declarar QA automatizado listo. |
| La consola incluye además `/ops/respaldos` y `/ops/perfil` | Incorporar ambas rutas al inventario de vistas, pruebas, rewrites y documentación. |

**Convención de estados:** una casilla marcada solo debe representar evidencia
real (comando ejecutado, prueba aprobada o archivo confirmado). Los textos en
futuro no deben marcarse como completados.

---

## Arquitectura y Decisiones Clave para Administración

1. **Aplanamiento de la estructura raíz:** En `CIA-ACREDITTIA-main`, el código vive anidado en `BASE/app/` y `BASE/modelo_datos/`. En el Día 1 se promueve a la raíz (`backend/`, `frontend/`, `modelo_datos/`, `infra/`) para que coincida 1:1 con `estructura_repositorio_unificado.md`.
2. **Secuencia SQL Unificada (`19`..`22`):** Para evitar colisión con las migraciones `07`..`18` de Plataforma (certificación laboral, RAG `pgvector`, vínculo faena, rol visor, alertas IA), los scripts de la Consola Interna se renumeran como:
   - `19_consola_interna.sql` (antes `07_consola_interna.sql`)
   - `20_funciones_consola.sql` (antes `08_funciones_consola.sql`)
   - `21_indices_consola.sql` (antes `09_indices_consola.sql`)
   - `22_sesion_y_ciclo_vida.sql` (fusión limpia de `10_version_sesion.sql` y `11_ciclo_vida_contratos.sql`, dejando `SCHEMA_VERSION = 22`).
3. **Aislamiento de namespaces (`ops/`):** Todos los modelos (`models/ops.py`), routers (`routers/ops/admin_ops.py`), servicios (`services/ops/`) y vistas Next.js (`app/(ops)/ops/*`, `components/ops/`, `lib/ops/`) quedan encapsulados en sus propias carpetas, garantizando **cero conflictos de archivos** al hacer `git merge` en el Día 4.

---

## Cronograma Diario y Desglose de Tareas

### 📅 DÍA 1 (2026-11-01): Aplanamiento de Repositorio y Renumeración SQL (`19`..`22`)

#### Tarea 1.1: Promover `BASE/app/*` y `BASE/modelo_datos/*` a la raíz del proyecto
- **Descripción:** Mover `BASE/app/backend`, `BASE/app/frontend`, `BASE/app/docker-compose.yml` y `BASE/modelo_datos` a la raíz del repositorio. Mover `docker-compose.ngrok.yml` y `ngrok.yml` a `infra/ngrok/` y consolidar la documentación histórica (`BASE/`, `IDEA/`, `documentacion/`) fuera del árbol productivo o en `docs/legacy/`.
- **Criterios de aceptación:**
  - [ ] El repositorio tiene exactamente las carpetas raíz `backend/`, `frontend/`, `modelo_datos/`, `infra/` y `docker-compose.yml`.
  - [ ] `docker-compose.yml` monta `./modelo_datos:/schema:ro` en lugar de `../modelo_datos:/schema:ro`.
- **Verificación:**
  - [ ] `docker compose config` valida rutas y volúmenes sin errores desde la raíz.
- **Dependencias:** Ninguna.
- **Archivos tocados:** `docker-compose.yml`, `infra/ngrok/*`, estructura raíz.
- **Alcance estimado:** Medium (4–5 archivos de configuración + `git mv`).
- **Commit:** `Feat(repo): aplanar estructura moviendo backend, frontend y modelo_datos a la raiz`

#### Tarea 1.2: Renumerar migraciones de Consola Interna a `19`..`22` y migrar motor BD a `pgvector:pg16`
- **Descripción:** Renombrar los scripts SQL propios de Administración a `19_consola_interna.sql`, `20_funciones_consola.sql`, `21_indices_consola.sql` y consolidar `10_version_sesion.sql` + `11_ciclo_vida_contratos.sql` en `22_sesion_y_ciclo_vida.sql` registrando la versión `22` en `app_schema_migrations`. Actualizar la imagen de PostgreSQL en `docker-compose.yml` a `pgvector/pgvector:pg16` para igualar el motor con Plataforma.
- **Criterios de aceptación:**
  - [ ] Los scripts `19` a `22` son 100% idempotentes (`CREATE TABLE IF NOT EXISTS`, `CREATE OR REPLACE FUNCTION`, `ADD COLUMN IF NOT EXISTS`).
  - [ ] La tabla `app_schema_migrations` registra versión `22` al finalizar la migración.
- **Verificación:**
  - [ ] Ejecución limpia de `19`..`22` sobre PostgreSQL 16 (`pgvector/pgvector:pg16`).
- **Dependencias:** Tarea 1.1.
- **Archivos tocados:** `modelo_datos/19_consola_interna.sql`, `modelo_datos/20_funciones_consola.sql`, `modelo_datos/21_indices_consola.sql`, `modelo_datos/22_sesion_y_ciclo_vida.sql`, `docker-compose.yml`.
- **Alcance estimado:** Medium (5 archivos).
- **Commit:** `Feat(db): renumerar scripts sql de consola interna a 19-22 y adoptar imagen pgvector pg16`

---

### 📅 DÍA 2 (2026-11-02): Modularización del Backend hacia `ops/`

#### Tarea 2.1: Estandarizar modelos de Consola en `backend/app/models/ops.py`
- **Descripción:** Convertir `backend/app/models.py` y `backend/app/models_ops.py` en el paquete `backend/app/models/` ubicando los modelos exclusivos de consola (`OpsJob`, `OpsAudit`, vistas y métricas operativas) en `backend/app/models/ops.py` y re-exportándolos en `backend/app/models/__init__.py`. Eliminar copias obsoletas de modelos de negocio que serán provistas por `models/platform.py`.
- **Criterios de aceptación:**
  - [ ] `backend/app/models_ops.py` desaparece de la raíz de `app/` y vive en `backend/app/models/ops.py`.
  - [ ] Todos los imports en servicios de consola usan `from app.models.ops import ...` o `from app.models import ...`.
- **Verificación:**
  - [ ] `python -c "import app.models.ops"` ejecuta sin errores.
- **Dependencias:** Tarea 1.2.
- **Archivos tocados:** `backend/app/models/__init__.py`, `backend/app/models/ops.py`.
- **Alcance estimado:** Small (2–3 archivos).
- **Commit:** `Feat(models): encapsular modelos de consola interna en paquete app/models/ops`

#### Tarea 2.2: Aislar routers y servicios de Administración en `routers/ops/` y `services/ops/`
- **Descripción:** Mover `backend/app/routers/admin_ops.py` a `backend/app/routers/ops/admin_ops.py`, y mover `backend/app/services/ops.py`, `backend/app/services/ops_probes.py` y `backend/app/services/pdf.py` a `backend/app/services/ops/`. Actualizar imports en `backend/worker/ops_tasks.py` y `backend/app/main.py`.
- **Criterios de aceptación:**
  - [ ] Todos los archivos exclusivos de Administración viven bajo `routers/ops/`, `services/ops/` y `worker/ops_tasks.py`.
  - [ ] Los endpoints `/api/v1/admin/*` y `/api/v1/admin/ops/*` responden igual que antes.
- **Verificación:**
  - [ ] Pruebas de sondas (`ops_probes`) y endpoints de consola devuelven `200 OK`.
- **Dependencias:** Tarea 2.1.
- **Archivos tocados:** `backend/app/routers/ops/admin_ops.py`, `backend/app/services/ops/*`, `backend/worker/ops_tasks.py`, `backend/app/main.py`.
- **Alcance estimado:** Medium (5 archivos).
- **Commit:** `Feat(backend): aislar routers y servicios de consola interna bajo namespace ops`

---

### 📅 DÍA 3 (2026-11-03): Estandarización del Frontend Next.js `(ops)` y Preparación Pre-Merge

#### Tarea 3.1: Encapsular rutas de Consola en Route Group `frontend/app/(ops)/ops/`
- **Descripción:** Mover todas las páginas de `frontend/app/ops/*` (`dashboard`, `empresas`, `accesos`, `busqueda`, `salud`, `sistemas`, `indicadores`, `auditoria`, `layout.tsx`, `page.tsx`) dentro del Route Group `frontend/app/(ops)/ops/`. Preparar las vistas `frontend/app/(app)/gestion-cuentas/page.tsx`, `frontend/app/(app)/perfil/page.tsx` y el componente `ResponsablesContratos.tsx` para integrarse limpiamente en el grupo `(app)` sin pisar archivos de Plataforma.
- **Criterios de aceptación:**
  - [ ] Las URLs `/ops/*` y los rewrites `/admin/*` -> `/ops/*` en `next.config.mjs` funcionan sin cambios para el usuario final.
  - [ ] No existen archivos de consola fuera de `app/(ops)/`, `components/ops/` y `lib/ops/`.
- **Verificación:**
  - [ ] `npm run build` compila todas las rutas de `/(ops)/ops/*` exitosamente.
- **Dependencias:** Tarea 1.1.
- **Archivos tocados:** `frontend/app/(ops)/ops/*`, `frontend/app/(app)/gestion-cuentas/page.tsx`, `frontend/app/(app)/perfil/page.tsx`, `frontend/next.config.mjs`.
- **Alcance estimado:** Medium (4–5 archivos clave + movimientos).
- **Commit:** `Feat(frontend): estructurar consola de administracion en route group (ops) de nextjs`

#### Tarea 3.2: Alinear dependencias Frontend/Backend y congelar contratos de puntos de unión
- **Descripción:** Sincronizar versiones en `frontend/package.json` (incorporando `sonner` solo si se adopta y scripts de test) y alinear el backend entre `backend/requirements.txt` y `backend/requirements-test.txt` manteniendo `reportlab>=4.2`. No depender de `pgserver` de PyPI: la suite actual usa la compatibilidad local documentada en el repositorio y requiere revisión antes de publicar un paquete externo. Si Plataforma define su propio motor vectorial, confirmar la biblioteca y versión reales; el plan no debe asumir `pgvector==0.5.1` sin evidenciar el entorno objetivo.
- **Criterios de aceptación:**
  - [ ] Se adopta una única estrategia de PostgreSQL efímero y queda documentada en `requirements-test.txt`.
  - [ ] `frontend/components/ops/` y `frontend/lib/ops/` compilan con `strict: true` en `tsconfig.json`.
- **Verificación:**
  - [ ] `npx tsc --noEmit` en `frontend/` y `pytest` en `backend/` ejecutan sin errores.
- **Dependencias:** Tarea 3.1.
- **Archivos tocados:** `frontend/package.json`, `backend/requirements.txt`, `backend/pgserver/__init__.py`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Fix(deps): alinear dependencias con plataforma y eliminar stub local de pgserver`

#### 🏁 Checkpoint: Pre-Fusión (Fin del Día 3)
- [ ] Estructura de `CIA-ACREDITTIA-main` idéntica a `estructura_repositorio_unificado.md`.
- [ ] Todos los archivos propios de Administración aislados en `ops/` y SQL `19`..`22`.
- [ ] Cero conflictos en simulación de `git merge --no-commit`.

---

### 📅 DÍA 4 (2026-11-04): Fusión de Repositorios y Conexión a Base de Datos Única

#### Tarea 4.1: Ejecutar Fusión en el Monorepo y Unificar `main.py`, `config.py` y `next.config.mjs`
- **Descripción:** Fusionar las ramas de Administración y Plataforma en el repositorio final. En `backend/app/config.py`, combinar la validación de seguridad de producción (`validar_produccion`, `app_env`, `seed_demo_enabled`) de Administración con las variables de Gemini/RAG de Plataforma. En `frontend/next.config.mjs`, conservar `output: "standalone"` junto con los `rewrites` y `redirects` de `/admin/*` a `/ops/*`.
- **Criterios de aceptación:**
  - [ ] El servidor FastAPI expone simultáneamente todos los routers de `platform` y `ops` (`admin_ops.router`).
  - [ ] El servidor Next.js sirve landing `(marketing)`, portal `(app)` y consola `(ops)` en el mismo puerto `3000`.
- **Verificación:**
  - [ ] Navegar a `/admin/dashboard` (reescrito a `/ops/dashboard`) y a `/dashboard` carga ambas interfaces sin conflicto.
- **Dependencias:** Checkpoint Día 3.
- **Archivos tocados:** `backend/app/config.py`, `backend/app/main.py`, `frontend/next.config.mjs`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Feat(merge): integrar configuracion de seguridad, routers ops y rewrites en monorepo`

#### Tarea 4.2: Aplicar cadena completa SQL (`01`..`22`) y procedimientos almacenados sobre la BD compartida
- **Descripción:** Configurar `SCHEMA_SCRIPTS` (`01`..`22`) y `SCHEMA_VERSION = 22` en `backend/app/database.py`, unificando `schema_version()` mediante `app_schema_migrations` y manteniendo `install_runtime_role_guard()`. Verificar que las funciones SQL de `20_funciones_consola.sql` consulten directamente las tablas operativas pobladas por Plataforma.
- **Criterios de aceptación:**
  - [ ] `python -m migrate.run` aplica los 22 scripts sin error en la base de datos compartida `acredittia`.
  - [ ] Las funciones almacenadas de consola leen contratos, sujetos, documentos y jobs reales de la base de datos única.
- **Verificación:**
  - [ ] `GET /api/v1/admin/ops/dashboard` devuelve KPIs reales desde la base de datos PostgreSQL compartida.
- **Dependencias:** Tarea 4.1.
- **Archivos tocados:** `backend/app/database.py`, `modelo_datos/19_consola_interna.sql`, `modelo_datos/20_funciones_consola.sql`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Feat(db): activar esquema unificado v22 y funciones almacenadas de consola sobre bd compartida`

#### 🏁 Checkpoint: Fusión Completada (Fin del Día 4)
- [ ] Ambos proyectos fusionados en un único repositorio sin conflictos.
- [ ] Base de datos única conectada y operando en versión `22`.

---

### 📅 DÍA 5 (2026-11-05): Integración de Gobernanza, Sondas de Salud y Ciclo de Vida

#### Tarea 5.1: Conectar Sondas de Salud (`ops_probes`) a los subsistemas de Plataforma (DB, Redis, Storage, RAG)
- **Descripción:** Extender `backend/app/services/ops/ops_probes.py` y `backend/worker/ops_tasks.py` para monitorear en tiempo real el estado de la extensión `pgvector`, la cola Celery unificada, el almacenamiento de blobs y el estado de migración `v22`, exponiendo los resultados en `/ops/salud` y `/ops/sistemas`.
- **Criterios de aceptación:**
  - [ ] La vista `/ops/salud` reporta latencia y estado real de PostgreSQL (`pgvector`), Redis, Worker y Storage.
  - [ ] Pausar o reanudar un job desde `/ops/sistemas` actualiza `ops_jobs` en la BD compartida.
- **Verificación:**
  - [ ] `GET /api/v1/admin/ops/salud` y `GET /api/v1/admin/ops/sistemas` responden con métricas en vivo.
- **Dependencias:** Tarea 4.2.
- **Archivos tocados:** `backend/app/services/ops/ops_probes.py`, `backend/app/services/ops/ops.py`, `backend/worker/ops_tasks.py`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Feat(ops): conectar sondas de salud y control de jobs a infraestructura unificada`

#### Tarea 5.2: Integrar gestión de ciclo de vida de contratos (`ciclo_estado`) y revocación de accesos (`auth_version`)
- **Descripción:** Verificar y ajustar los endpoints de `/ops/empresas` y `/ops/accesos` para que los cambios de estado de empresas/contratos (`ciclo_estado`, `ciclo_motivo`) y el bloqueo/revocación de sesiones (`users.auth_version += 1`) impacten de inmediato en las sesiones activas de Plataforma y registren trazabilidad en `/ops/auditoria`.
- **Criterios de aceptación:**
  - [ ] Toda acción administrativa sobre una empresa, contrato o usuario genera su registro inmutable en la bitácora de auditoría y actualiza la tabla compartida.
  - [ ] El componente `ResponsablesContratos.tsx` y las vistas `/gestion-cuentas` y `/perfil` operan contra los endpoints unificados.
- **Verificación:**
  - [ ] Prueba funcional desde `/ops/accesos` revocando sesión y comprobando el registro en `/ops/auditoria`.
- **Dependencias:** Tarea 5.1.
- **Archivos tocados:** `backend/app/routers/ops/admin_ops.py`, `frontend/app/(ops)/ops/accesos/page.tsx`, `frontend/app/(ops)/ops/empresas/page.tsx`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Fix(ops): sincronizar bloqueo de cuentas, ciclo de vida de contratos y bitacora de auditoria`

---

### 📅 DÍA 6 (2026-11-06): QA Funcional y Automatizado — Consola de Administración y Seguridad

#### Tarea 6.1: Desarrollar y ejecutar suite de pruebas Backend para Consola Interna (`backend/tests/ops/`)
- **Descripción:** Crear pruebas automatizadas con `pytest` y `pgserver` en `backend/tests/ops/` cubriendo: control de acceso exclusivo `super_admin` a `/api/v1/admin/ops/*`, ejecución de procedimientos almacenados (`20_funciones_consola.sql`), generación de reportes PDF ejecutivos (`services/ops/pdf.py` con `reportlab`) y validación de `install_runtime_role_guard()`.
- **Criterios de aceptación:**
  - [ ] Un token de `company_admin`, `operator` o `visor` recibe `403 Forbidden` al intentar invocar cualquier ruta de `/api/v1/admin/ops/*`.
  - [ ] `validate_runtime_role()` detecta y bloquea roles con `rolsuper` o `rolbypassrls` cuando se simula entorno de producción.
- **Verificación:**
  - [ ] `pytest backend/tests/ops -v` pasa al 100%.
- **Dependencias:** Tarea 5.2.
- **Archivos tocados:** `backend/tests/ops/test_admin_ops_api.py`, `backend/tests/ops/test_runtime_role_guard.py`, `backend/tests/ops/test_ops_pdf.py`.
- **Alcance estimado:** Medium (3 archivos).
- **Commit:** `Feat(qa): agregar suite pytest para endpoints de consola interna, reportes pdf y guarda de roles`

#### Tarea 6.2: QA de Interfaz y Navegación en Consola Next.js (`/ops/*` y rewrites `/admin/*`)
 - **Descripción:** Validar todas las vistas de la Consola Interna (`dashboard`, `empresas`, `busqueda`, `salud`, `sistemas`, `indicadores`, `accesos`, `auditoria`, `respaldos`, `perfil`), asegurando que `frontend/lib/ops/api.ts` consuma datos reales de la BD unificada (desactivando fallbacks a `mock.ts` en producción), y verificar temas claro/oscuro (`theme.tsx`) e internacionalización (`i18n.tsx`). La ruta raíz `/ops` forma parte de la navegación y también debe validar identidad.
- **Criterios de aceptación:**
  - [ ] Las 10 rutas secundarias de `/ops/*` y sus alias vigentes renderizan sin errores de consola ni datos simulados cuando la API está activa.
  - [ ] El buscador global `/ops/busqueda` localiza empresas, contratos y sujetos creados en Plataforma.
- **Verificación:**
  - [ ] `npm test` y recorrido de pruebas de renderizado en `frontend/tests/ops/`.
- **Dependencias:** Tarea 6.1.
- **Archivos tocados:** `frontend/lib/ops/api.ts`, `frontend/app/(ops)/ops/busqueda/page.tsx`, `frontend/tests/ops/ops_routes.test.mjs`.
- **Alcance estimado:** Small (3 archivos).
- **Commit:** `Fix(qa): verificar consumo de datos reales en vistas ops y pruebas de ruteo admin`

---

### 📅 DÍA 7 (2026-11-07): QA de Integración Cruzada (Administración ↔ Plataforma) y Hardening

#### Tarea 7.1: Ejecutar QA Cruzado de Gobernanza, Auditoría y Métricas en Tiempo Real
- **Descripción:** Ejecutar junto al equipo de Plataforma las pruebas E2E sobre la base de datos compartida:
  1. Verificar que las altas de empresas, contratos, trabajadores y documentos en Plataforma actualicen los gráficos de `/ops/indicadores` y `/ops/dashboard`.
  2. Verificar que las acciones de soporte en `/ops/empresas` y `/ops/accesos` se reflejen instantáneamente en Plataforma y queden auditadas en `/ops/auditoria`.
- **Criterios de aceptación:**
  - [ ] Consistencia del 100% entre los conteos SQL de Plataforma y los indicadores agregados por `20_funciones_consola.sql`.
  - [ ] Ninguna operación de consola rompe el aislamiento RLS de las empresas cuando se consulta desde Plataforma.
- **Verificación:**
  - [ ] Ejecución conjunta de `pytest backend/tests/test_cross_platform_ops.py` y script `modelo_datos/05_verificacion.sql`.
- **Dependencias:** Tarea 6.2.
- **Archivos tocados:** `modelo_datos/05_verificacion.sql`, `modelo_datos/20_funciones_consola.sql`.
- **Alcance estimado:** Small (2 archivos).
- **Commit:** `Fix(qa): certificar metricas de procedimientos almacenados y auditoria cruzada con plataforma`

#### Tarea 7.2: Auditoría de Seguridad de Configuración (`validar_produccion`) y Contenedores
- **Descripción:** Verificar que las validaciones de `Settings.validar_produccion` rechacen secretos débiles (`dev-*`), semillas demo en producción o desactivación de RLS, y comprobar el levantamiento limpio de todos los contenedores (`api`, `worker`, `beat`, `migrate`, `web`, `db`, `redis`).
- **Criterios de aceptación:**
  - [ ] Con `APP_ENV=production`, la API se niega a arrancar si `JWT_SECRET` es inseguro o si `DB_RLS_ENABLED=false`.
  - [ ] El job `migrate` y el endpoint `/health/esquema` validan estrictamente la versión `22`.
- **Verificación:**
  - [ ] `pytest backend/tests/ops/test_production_security.py` pasa al 100%.
- **Dependencias:** Tarea 7.1.
- **Archivos tocados:** `backend/app/config.py`, `backend/tests/ops/test_production_security.py`.
- **Alcance estimado:** Small (2 archivos).
- **Commit:** `Fix(security): validar guardas de configuracion de produccion y readiness de esquema v22`

#### 🏁 Checkpoint: QA Integral Aprobado (Fin del Día 7)
- [ ] Consola de Administración 100% operativa sobre la misma base de datos de Plataforma.
- [ ] Pruebas de seguridad, roles, RLS y procedimientos almacenados en verde.

---

### 📅 DÍA 8 (2026-11-08): Documentación Final del Proyecto y Entrega

#### Tarea 8.1: Documentar Consola de Administración (`/ops`), Procedimientos SQL (`19`..`22`) y Seguridad
- **Descripción:** Consolidar y actualizar la documentación de `README_ops_Back.md` y `README_ops_Front.md` dentro de `docs/arquitectura_administracion_ops.md` y en el `README.md` raíz del monorepo, detallando las rutas `/ops/*` (y rewrites `/admin/*`), los endpoints `/api/v1/admin/ops/*`, las tablas y funciones de consola (`19`..`22`) y el modelo de seguridad (`install_runtime_role_guard`, `auth_version`).
- **Criterios de aceptación:**
  - [ ] Toda la arquitectura de Administración queda documentada con las rutas definitivas del monorepo unificado.
  - [ ] Se eliminan los archivos `README_ops_*.md` sueltos de la raíz, integrándolos en `docs/` y `README.md`.
- **Verificación:**
  - [ ] Revisión de enlaces y comandos en `README.md` y `docs/arquitectura_administracion_ops.md`.
- **Dependencias:** Checkpoint Día 7.
- **Archivos tocados:** `README.md`, `docs/arquitectura_administracion_ops.md`.
- **Alcance estimado:** Small (2 archivos).
- **Commit:** `Feat(docs): documentar consola interna ops, funciones sql 19-22 y modelo de seguridad`

#### Tarea 8.2: Documentar Runbook de Operaciones, Monitoreo de Sondas y Guía de Troubleshooting
- **Descripción:** Redactar en `docs/runbook_operaciones_y_soporte.md` la guía operativa para administradores de Acredittia: cómo interpretar `/ops/salud` y `/ops/sistemas`, cómo pausar/reanudar jobs de Celery desde la consola, cómo gestionar el ciclo de vida de contratos (`ciclo_estado`) y cómo auditar incidentes en `/ops/auditoria`.
- **Criterios de aceptación:**
  - [ ] Incluye procedimientos paso a paso de operación, respaldo, migración (`python -m migrate.run`) y respuesta ante alertas de salud.
- **Verificación:**
  - [ ] Validación final del repositorio documentado y listo para entrega.
- **Dependencias:** Tarea 8.1.
- **Archivos tocados:** `docs/runbook_operaciones_y_soporte.md`.
- **Alcance estimado:** Small (1–2 archivos).
- **Commit:** `Feat(docs): publicar runbook de operaciones, monitoreo de sondas y guia de soporte`

---

## Matriz de Riesgos y Mitigación (Equipo Administración)

| Riesgo | Impacto | Mitigación |
| :--- | :---: | :--- |
| Colisión entre la ruta `/admin` (administración de empresa del tenant en Plataforma) y `/admin/*` (Consola Interna) | Alto | Mantener las vistas de consola física bajo `app/(ops)/ops/*` y usar los `rewrites` específicos de `next.config.mjs` (`/admin/:view(dashboard\|empresas\|busqueda\|salud\|sistemas\|auditoria)` -> `/ops/:view`), dejando `/admin` libre para el tenant o redirigido limpiamente. |
| Ambigüedad sobre PostgreSQL efímero en QA | Medio | Verificar disponibilidad real de `pgserver`, Docker y compatibilidad local; congelar una estrategia probada antes del Día 6. No presentar el paquete local como distribución oficial. |
| Bloqueo de arranque en desarrollo local por `install_runtime_role_guard()` cuando se usa el rol `postgres` en Docker | Medio | Mantener la condición `if settings.app_env == "production": validate_runtime_role(...)` para que en desarrollo (`APP_ENV=development`) permita operar con el contenedor local y en producción exija `acredittia_app` (`NOBYPASSRLS`). |
