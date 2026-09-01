# Acredittia — Aplicación web

Plataforma de acreditación de contratistas para faenas mineras y energéticas.
Implementa el **core funcional** de la Especificación de API Backend v1.0:
autenticación JWT con aprobación de administrador, contratos por faena,
personal y equipos con checklists autogenerados (13/10 requisitos + 9 EMSIPOR
para conductores), subida de documentos con **revisión IA**, vencimientos,
alertas y dashboard.

## Estructura

```
app/
├── docker-compose.yml     # Postgres 16 + API + Web
├── backend/               # FastAPI + SQLAlchemy 2 (Python 3.12)
│   └── app/
│       ├── main.py        # arranque, CORS, cron de vencimientos
│       ├── models.py      # mapeo del modelo de datos (28 tablas)
│       ├── seeds.py       # 8 faenas, 42 plantillas, ejemplos, admin y demo
│       ├── routers/       # auth, admin, faenas, contratos, sujetos, documentos, alertas, dashboard
│       └── services/      # checklist, vencimientos, storage (local/Azure), IA (simulada/Claude)
└── frontend/              # Next.js 14 + Tailwind (estética del wireframe)
```

La base de datos se crea con los scripts de `../modelo_datos/` (01–03),
montados en el primer arranque de Postgres.

## Ejecutar en local

Requisitos: Docker Desktop.

```bash
cd app
docker compose up --build
```

- Web: http://localhost:3000
- API (OpenAPI): http://localhost:8000/docs

**Cuentas semilla**

| Rol | Email | Contraseña |
|---|---|---|
| Administrador | admin@acredittia.cl | Admin2026! |
| Empresa demo | demo@acredittia.cl | Demo2026! |

**Flujo de prueba sugerido**: registra una empresa nueva → entra como admin y
apruébala → entra con la empresa → crea un contrato en Los Pelambres (genera
10 docs de empresa) → agrega un trabajador conductor (genera 13+9 docs) →
sube un PDF a un requisito → revisa el resultado de la IA → mira el dashboard.

## Desarrollo sin Docker

```bash
# Backend (requiere Postgres con los scripts 01-03 aplicados)
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/acredittia \
SCHEMA_DIR=../../modelo_datos STORAGE_DIR=/tmp/uploads \
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

## Configuración (variables de entorno del backend)

| Variable | Default | Descripción |
|---|---|---|
| DATABASE_URL | postgres local | Conexión SQLAlchemy (psycopg) |
| STORAGE_BACKEND | local | `local` o `azure` (Azure Blob Storage) |
| AZURE_BLOB_CONN / AZURE_BLOB_CONTAINER | — | Solo con storage azure |
| IA_BACKEND | simulada | `simulada` o `claude` (revisión real con LLM) |
| ANTHROPIC_API_KEY | — | Solo con IA claude |
| JWT_SECRET | dev | Cambiar en producción |
| CORS_ORIGINS | http://localhost:3000 | Orígenes permitidos |

## Estado de las pruebas

El backend fue validado contra PostgreSQL 16.2 real con un smoke test
end-to-end de 34 verificaciones (auth completo, aprobación admin, checklists
autogenerados, subida + revisión IA, vencimientos, alertas, aislamiento
multi-tenant, impersonación admin, bajas). Resultado: **34/34 PASS**.
El script está en `backend/tests/smoke_test.py`.

## Fuera de alcance de esta versión (ver plan de desarrollo)

Reportes PDF/Excel, calendario, integraciones externas (SIGA, WhatsApp...),
suscripciones/pagos y extracción IA de contratos: los endpoints están
especificados en `Acredittia_Especificacion_API_Backend.docx` y planificados
en `Acredittia_Plan_de_Desarrollo.docx`.
