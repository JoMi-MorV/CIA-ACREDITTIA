py -0p
py -3.12 --version# Estructura del Repositorio Unificado y Estándar Tecnológico (ACREDITTIA)

**Fecha de Inicio:** 2026-11-01 (Día 1)  
**Hito de Fusión:** 2026-11-04 (Día 4)  
**Cierre y Documentación:** 2026-11-08 (Día 8)  
**Proyectos Involucrados:**
- **Equipo Plataforma (`Acredittia-`)**: Operación de contratos, personal, flota, certificación laboral, agentes IA, RAG (`pgvector`) y landing comercial.
- **Equipo Administración (`CIA-ACREDITTIA-main`)**: Consola Interna de Operaciones (`/ops` y `/admin`), sondas de salud (`ops_probes`), auditoría global, ciclo de vida de contratos, revocación de sesiones (`auth_version`) y métricas de sistemas.

---

## Estado del diseño: objetivo, no estado actual

La estructura y las versiones descritas en este documento corresponden al
repositorio unificado a construir. Al 04-11-2026, `CIA-ACREDITTIA-main` conserva
la estructura `BASE/app/` y el esquema local en versión `15`; por tanto, la
numeración `19`..`22` y la estructura raíz son migraciones previstas, no hechos
ya ejecutados. El frontend actual tiene Next.js 14.2.5 y React 18.3.1, pero no
declara `sonner`, scripts de test ni rutas de consola bajo Route Groups.

---

## 1. Decisiones Tecnológicas Orientadas a la Mejor Opción

Para eliminar divergencias entre ambos repositorios antes del Día 4, se adopta la mejor opción técnica de cada componente:

| Capa / Componente | Decisión Oficial Unificada | Justificación Técnica |
| :--- | :--- | :--- |
| **Motor de Base de Datos** | `pgvector/pgvector:pg16` (PostgreSQL 16 + `vector`) | Soporta el modelo relacional multi-tenant + RLS de ambos equipos y habilita la búsqueda semántica RAG (`documento_chunk` 768 dims) sin requerir un segundo motor vectorial. |
| **Control de Versiones SQL** | Tabla `app_schema_migrations` + `pg_advisory_lock(918273)` | El enfoque de `CIA-ACREDITTIA-main` (`SELECT max(version) FROM app_schema_migrations`) es determinista y superior a la heurística de inspección de columnas de `Acredittia-`. Numeración lineal unificada `01` a `22`. |
| **Seguridad BD en Runtime** | `install_runtime_role_guard()` + `negar_mutaciones_visor` + `auth_version` | Combina la guarda de roles PostgreSQL (`NOBYPASSRLS`) y revocación inmediata de JWT (`auth_version`) de `CIA-ACREDITTIA-main` con el bloqueo fail-closed de mutaciones para el rol `visor` de `Acredittia-`. |
| **Motor IA y Documentos** | Google Gemini (`gemini-1.5-flash` + `text-embedding-004`) + `pymupdf` + `reportlab` + `openpyxl` | Se conserva el pipeline RAG/visión de `Acredittia-` (`pymupdf` para ingesta PDF) y se mantiene `reportlab` de `CIA-ACREDITTIA-main` para reportes PDF ejecutivos del backoffice. |
| **Estructura Frontend** | Next.js 14.2.5 App Router con **Route Groups** (`(marketing)`, `(app)`, `(ops)`) | Aísla los layouts, contextos y componentes de **Plataforma** y **Administración** en carpetas disjuntas. Cero colisiones de archivos al hacer `git merge` en el Día 4. |
| **UI Feedback y Ruteo** | `sonner` (Toasts) + Rewrites `/admin/*` -> `/ops/*` en `next.config.mjs` | Mantiene las URLs semánticas de administración (`/admin/dashboard`, `/admin/empresas`, etc.) de `CIA-ACREDITTIA-main` sin chocar con la vista de administración de empresa (`/admin` del tenant). |
| **Suite de QA y Testing** | `pytest` + `httpx` + estrategia PostgreSQL efímera aprobada (Backend) y `node --test` + `jsdom` (Frontend) | Pruebas contra un motor PostgreSQL efímero real (no SQLite), validando políticas RLS, procedimientos almacenados de consola y tipos `vector`. La compatibilidad local debe reemplazar o complementar un proveedor externo solo tras pruebas reproducibles. |

---

## 2. Árbol de Directorios del Repositorio Final (Sin Conflictos)

Ambos equipos deben reordenar sus repositorios durante los **Días 1 a 3** siguiendo exactamente esta estructura en la raíz (en `CIA-ACREDITTIA-main` se promueve el contenido de `BASE/app/` y `BASE/modelo_datos/` a la raíz del repositorio):

```text
acredittia-monorepo/
├── .env.example                        # Variables unificadas (DB, Redis, Azure, Gemini, Ops)
├── .gitignore                          # Reglas unificadas (Python, Node, Docker, entornos)
├── README.md                           # Documentación maestra (Día 8)
├── docker-compose.yml                  # Stack unificado (db pgvector:pg16, redis, migrate, api, worker, beat, web)
├── infra/                              # Manifiestos Cloud y túneles de desarrollo
│   ├── azure/
│   │   ├── worker.yaml
│   │   ├── cron-diario.yaml
│   │   ├── cron-purga.yaml
│   │   └── cron-reportes.yaml
│   ├── ngrok/
│   │   ├── docker-compose.ngrok.yml
│   │   └── ngrok.yml
│   └── scripts/
│       ├── deploy.ps1
│       └── deploy_update.ps1
│
├── modelo_datos/                       # ÚNICA fuente de verdad SQL (01..22 secuencial)
│   ├── 01_esquema.sql                  # Baseline v1.0
│   ├── 02_indices.sql                  # Índices base
│   ├── 03_triggers.sql                 # Triggers updated_at y auditoría
│   ├── 04_rls.sql                      # Políticas Row Level Security multi-tenant
│   ├── 05_verificacion.sql             # Script de auditoría de integridad
│   ├── 06_migracion_v11.sql            # Baseline aditivo v1.1 (versión 6)
│   ├── 07_migracion_v12.sql            # [Plataforma] archivo_ejemplo en requisito_templates
│   ├── 08_migracion_v13.sql            # [Plataforma] hereda_plataformas en contratos
│   ├── 09_certificacion_laboral.sql    # [Plataforma] periodos_laborales
│   ├── 10_add_telefono_email.sql       # [Plataforma] contacto en sujetos
│   ├── 11_rag_pgvector.sql             # [Plataforma] extensión vector y documento_chunk
│   ├── 12_vinculo_faena.sql            # [Plataforma] enum vinculo_tipo += 'faena'
│   ├── 13_rol_visor.sql                # [Plataforma] enum user_role += 'visor'
│   ├── 14_cascadas_integridad.sql      # [Plataforma] ON DELETE CASCADE
│   ├── 15_unidad_negocio.sql           # [Plataforma] unidad_negocio en contratos y users
│   ├── 16_alertas_ia.sql               # [Plataforma] configuración de alertas IA por contrato
│   ├── 17_gemini_embeddings.sql        # [Plataforma] embeddings 768 dims + índice HNSW
│   ├── 18_contratos_mandante.sql       # [Plataforma] mandante libre en contratos
│   ├── 19_consola_interna.sql          # [Administración] tablas ops_* y app_schema_migrations
│   ├── 20_funciones_consola.sql        # [Administración] procedimientos almacenados de consola
│   ├── 21_indices_consola.sql          # [Administración] índices FK de ops_jobs
│   └── 22_sesion_y_ciclo_vida.sql      # [Administración] users.auth_version + contratos.ciclo_* (versión 22)
│
├── backend/                            # API FastAPI + Worker Celery
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── migrate/
│   │   └── run.py                      # Ejecutor determinista con pg_advisory_lock
│   ├── worker/
│   │   ├── celery_app.py               # Registro unificado de colas y beat schedule
│   │   ├── platform_tasks.py           # [Plataforma] Tareas de vencimientos, RAG y correos
│   │   └── ops_tasks.py                # [Administración] Sondas y jobs de consola interna
│   ├── app/
│   │   ├── main.py                     # Ensamblador de middlewares y routers
│   │   ├── config.py                   # Settings base + importación de config_ops
│   │   ├── config_ops.py               # [Administración] Configuración específica de consola
│   │   ├── database.py                 # Engine pgvector + RLS ContextVar + runtime_role_guard
│   │   ├── security.py                 # JWT + validación de auth_version
│   │   ├── deps.py                     # Dependencias de tenant, visor y super_admin
│   │   ├── seeds.py                    # Semillas idempotentes unificadas
│   │   ├── models/                     # Paquete de modelos SQLAlchemy sin colisión
│   │   │   ├── __init__.py             # Exporta Base y todos los modelos
│   │   │   ├── platform.py             # [Plataforma] Modelos de negocio y RAG
│   │   │   └── ops.py                  # [Administración] Modelos ops_* de consola interna
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── platform/               # [Plataforma] Routers de negocio (contratos, ia, exportar, etc.)
│   │   │   └── ops/                    # [Administración] admin_ops.py y endpoints de consola
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── platform/               # [Plataforma] rag_index, embeddings, ia_consultas, email, etc.
│   │       └── ops/                    # [Administración] ops.py, ops_probes.py, pdf.py
│   └── tests/
│       ├── conftest.py                 # Fixture pgserver con esquema v22
│       ├── platform/                   # [Plataforma] Tests de negocio, RAG y visor
│       └── ops/                        # [Administración] Tests de consola interna y guardas
│
└── frontend/                           # Aplicación Next.js 14.2.5 (React 18, App Router)
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── postcss.config.mjs
    ├── next.config.mjs                 # output: "standalone" + rewrites /admin/* -> /ops/*
    ├── public/
    ├── app/
    │   ├── layout.tsx                  # Root layout compartido (fuentes, Sonner toaster)
    │   ├── globals.css
    │   ├── (marketing)/                # [Plataforma] Landing comercial pública
    │   │   ├── page.tsx
    │   │   ├── privacidad/page.tsx
    │   │   └── terminos/page.tsx
    │   ├── (auth)/                     # Login y recuperación unificados
    │   │   └── login/page.tsx
    │   ├── (app)/                      # [Plataforma] Portal Operativo de Empresas (Tenant)
    │   │   ├── layout.tsx
    │   │   ├── dashboard/page.tsx
    │   │   ├── contratos/
    │   │   ├── personal/
    │   │   ├── equipos/
    │   │   ├── faenas/
    │   │   ├── certificacion-laboral/
    │   │   ├── gestion-cuentas/page.tsx # Incorporado desde Administración
    │   │   ├── perfil/page.tsx          # Incorporado desde Administración
    │   │   └── ...
    │   ├── (ops)/                      # [Administración] Consola Interna Backoffice
    │   │   └── ops/
    │   │       ├── layout.tsx
    │   │       ├── page.tsx
    │   │       ├── dashboard/page.tsx
    │   │       ├── empresas/page.tsx
    │   │       ├── accesos/page.tsx
    │   │       ├── busqueda/page.tsx
    │   │       ├── salud/page.tsx
    │   │       ├── sistemas/page.tsx
    │   │       ├── indicadores/page.tsx
    │   │       ├── auditoria/page.tsx
    │   │       ├── respaldos/page.tsx
    │   │       └── perfil/page.tsx
    │   └── api/
    │       └── contacto/route.ts
    ├── components/
    │   ├── shared/                     # Primitivas UI compartidas (ui.tsx)
    │   ├── landing/                    # [Plataforma] Componentes de landing
    │   ├── platform/                   # [Plataforma] Contratos, dashboard, modales, Sidebar
    │   └── ops/                        # [Administración] charts.tsx, logo.ts, ui.tsx, ResponsablesContratos.tsx
    ├── context/
    │   └── I18nContext.tsx
    ├── lib/
    │   ├── platform/                   # [Plataforma] api.ts, cliente.ts, tipos.ts, rut.ts
    │   └── ops/                        # [Administración] api.ts, auth.ts, i18n.tsx, theme.tsx, mock.ts
    └── tests/
        ├── platform/
        └── ops/
```

---

## 3. Regla de Oro para Cero Conflictos en el Día 4

1. **Separación por Dominios (`platform/` vs `ops/`)**: Ningún archivo de lógica específica de negocio o de consola comparte ruta con el otro equipo.
2. **Archivos Compartidos (Puntos de Unión Controlados)**: Solo 7 archivos en todo el repositorio son puntos de unión en el Día 4 (`docker-compose.yml`, `backend/requirements.txt`, `backend/app/main.py`, `backend/app/database.py`, `backend/app/models/__init__.py`, `frontend/package.json`, `frontend/next.config.mjs`). Sus contratos quedan congelados en el Día 3.
3. **Única Base de Datos (`acredittia`)**: Ambos módulos leen y escriben sobre el mismo cluster PostgreSQL 16 (`pgvector/pgvector:pg16`) en la versión de esquema `22`, garantizando que las métricas, auditorías, bloqueos de sesión (`auth_version`) y estados de ciclo de vida (`ciclo_estado`) que ejecuta **Administración** impacten en tiempo real a **Plataforma**.
