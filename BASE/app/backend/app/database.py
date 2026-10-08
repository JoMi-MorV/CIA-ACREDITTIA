"""Conexión, contexto multi-tenant para RLS y aplicación del esquema.

Modelo de aislamiento (doble barrera, §7 del modelo de datos):

1. **RLS en el motor.** La API se conecta con `acredittia_app` (NOBYPASSRLS) y
   fija por transacción `app.company_id`, `app.is_admin` y `app.user_id`. Las
   políticas `p_tenant` filtran cada tabla por `company_id`.
2. **Filtros explícitos en las consultas.** No se eliminan: si un endpoint
   nuevo olvida el `WHERE company_id`, el motor lo tapa; si RLS se desactivara
   por un error de despliegue, el filtro sigue en pie.

El contexto viaja en un `ContextVar`, de modo que cada request (incluidos los
endpoints síncronos que corren en el threadpool de anyio) tiene su propia
copia. El listener `after_begin` lo materializa con `set_config(..., true)`,
que es local a la transacción: al terminarla el ajuste desaparece solo.
"""
from __future__ import annotations

import contextlib
import os
import re
import time
from contextvars import ContextVar
from dataclasses import dataclass

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session, sessionmaker

from .config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
    connect_args={"application_name": "acredittia-api"},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class UnsafeDatabaseRole(RuntimeError):
    """La identidad de ejecución puede eludir el aislamiento del motor."""


def validate_runtime_role(dbapi_connection) -> None:
    """Comprueba privilegios efectivos y membresías sin publicar credenciales.

    Se usa en conexiones nuevas de ejecución, no en el motor de migraciones.
    Rechaza también propietarios de tablas, que pueden evitar o modificar RLS.
    """
    try:
        with dbapi_connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_roles r
                    WHERE (r.rolsuper OR r.rolbypassrls OR r.rolcreaterole
                           OR r.rolcreatedb)
                      AND (pg_has_role(session_user, r.oid, 'MEMBER')
                           OR pg_has_role(current_user, r.oid, 'MEMBER'))
                ) OR EXISTS (
                    SELECT 1 FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
                      AND (pg_has_role(session_user, c.relowner, 'MEMBER')
                           OR pg_has_role(current_user, c.relowner, 'MEMBER'))
                )
            """)
            inseguro = cursor.fetchone()[0]
    finally:
        dbapi_connection.rollback()
    if inseguro:
        raise UnsafeDatabaseRole(
            "Rol PostgreSQL inseguro para ejecución: use un rol sin privilegios "
            "administrativos, BYPASSRLS ni propiedad de tablas")


def _validate_production_role(dbapi_connection, connection_record):
    if settings.app_env == "production":
        validate_runtime_role(dbapi_connection)


def install_runtime_role_guard() -> None:
    """API/worker activan la guarda; el comando de migración conserva su rol."""
    if not event.contains(engine, "connect", _validate_production_role):
        event.listen(engine, "connect", _validate_production_role)
        # No reutilizar conexiones abiertas antes de instalar la guarda.
        engine.dispose()

# Scripts del modelo de datos en orden y versión de esquema que representan.
SCHEMA_SCRIPTS = ["01_esquema.sql", "02_indices.sql", "03_triggers.sql",
                  "04_rls.sql", "06_migracion_v11.sql", "07_consola_interna.sql", "08_funciones_consola.sql",
                  "09_indices_consola.sql", "10_version_sesion.sql",
                  "11_ciclo_vida_contratos.sql"]
SCHEMA_VERSION = 11
MIGRATION_LOCK_ID = 918273        # clave del pg_advisory_lock de migración


# ---------------------------------------------------------------- contexto
#
# El ContextVar guarda un contenedor MUTABLE y `set_ctx()` modifica sus campos
# en vez de reasignar la variable. La distinción no es estilística: FastAPI
# ejecuta las dependencias síncronas y el endpoint síncrono en hilos distintos
# del threadpool de anyio, y cada uno recibe una **copia** del contexto del
# request (`contextvars.copy_context()`). Con un valor inmutable, el
# `ContextVar.set()` que hace la dependencia de autenticación se aplica sobre su
# propia copia y el endpoint no lo ve: las políticas de RLS encuentran
# `app.company_id` vacío y toda consulta de negocio devuelve cero filas (o
# rechaza el INSERT). Copiar el contexto copia la *referencia* al contenedor, así
# que mutarlo sí es visible desde cualquier hilo del mismo request.
#
# La separación entre requests la garantiza `reset_ctx()`, que instala un
# contenedor nuevo y lo llama el middleware de `main.py` al entrar en cada
# request, antes de que se cree la tarea que ejecuta el endpoint.
@dataclass
class TenantCtx:
    company_id: str | None = None
    is_admin: bool = False
    user_id: str | None = None

    def instantanea(self) -> tuple:
        return (self.company_id, self.is_admin, self.user_id)

    def restaurar(self, instantanea: tuple) -> None:
        self.company_id, self.is_admin, self.user_id = instantanea


_ctx: ContextVar[TenantCtx] = ContextVar("tenant_ctx")


def _contenedor() -> TenantCtx:
    """Contenedor del contexto actual, creándolo si el request no pasó por el
    middleware (jobs de Celery, scripts, pruebas)."""
    try:
        return _ctx.get()
    except LookupError:
        nuevo = TenantCtx()
        _ctx.set(nuevo)
        return nuevo


def set_ctx(company_id=None, is_admin: bool = False, user_id=None) -> None:
    ctx = _contenedor()
    ctx.company_id = str(company_id) if company_id else None
    ctx.is_admin = is_admin
    ctx.user_id = str(user_id) if user_id else None


def get_ctx() -> TenantCtx:
    return _contenedor()


def reset_ctx() -> None:
    """Instala un contenedor nuevo: aísla el request de cualquier anterior."""
    _ctx.set(TenantCtx())


@event.listens_for(Session, "after_begin")
def _apply_tenant(session: Session, transaction, connection) -> None:
    """Materializa el contexto del request en GUCs locales a la transacción."""
    if not settings.db_rls_enabled:
        return
    ctx = _contenedor()
    connection.exec_driver_sql(
        "SELECT set_config('app.company_id', %s, true),"
        "       set_config('app.is_admin',   %s, true),"
        "       set_config('app.user_id',    %s, true)",
        (ctx.company_id or "", "true" if ctx.is_admin else "false", ctx.user_id or ""),
    )


def get_db():
    """Sesión de request.

    El tenant se aplica al ABRIR la transacción, no al crear la sesión, así que
    basta con que la dependencia de autenticación haya fijado el contexto antes
    de la primera consulta. Crear la sesión no abre transacción.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextlib.contextmanager
def auth_session():
    """Sesión para consultas de autenticación (login, refresh, reset de clave).

    En esas rutas todavía no hay tenant: hay que poder leer `users` por email
    sin saber a qué empresa pertenece. Se abre con `is_admin=true` y se usa
    EXCLUSIVAMENTE para resolver credenciales, nunca para datos de negocio.

    Al salir se restauran los CAMPOS del contenedor en vez de reasignar el
    ContextVar: el contenedor es compartido con el resto del request y
    reemplazarlo dejaría al endpoint sin contexto (ver la nota de `set_ctx`).
    """
    ctx = _contenedor()
    previo = ctx.instantanea()
    set_ctx(is_admin=True)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        ctx.restaurar(previo)


@contextlib.contextmanager
def worker_session(company_id=None, is_admin: bool = False, user_id=None):
    """Sesión para jobs de Celery, que no tienen request asociado."""
    ctx = _contenedor()
    previo = ctx.instantanea()
    set_ctx(company_id=company_id, is_admin=is_admin, user_id=user_id)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        ctx.restaurar(previo)


# ---------------------------------------------------------------- esquema
def wait_for_db(retries: int = 30) -> None:
    for _ in range(retries):
        try:
            with engine.connect() as c:
                c.execute(text("SELECT 1"))
            return
        except UnsafeDatabaseRole:
            raise
        except Exception:
            time.sleep(1)
    raise RuntimeError("Base de datos no disponible")


def _tabla_existe(conn, nombre: str) -> bool:
    return conn.execute(text(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name=:t"
    ), {"t": nombre}).first() is not None


def schema_version() -> int:
    """Versiones históricas por estructura; desde 8, registro explícito de migración."""
    with engine.connect() as c:
        if not _tabla_existe(c, "companies"):
            return 0
        if _tabla_existe(c, "app_schema_migrations"):
            version = c.execute(text("SELECT max(version) FROM app_schema_migrations")).scalar()
            if version is not None:
                return int(version)
        # NUEVO: Verificamos si ya existe la tabla de ops para retornar la versión 7
        if _tabla_existe(c, "ops_jobs"):
            return 7
        if _tabla_existe(c, "plataforma_credenciales"):
            return 6
        rls = c.execute(text(
            "SELECT relrowsecurity FROM pg_class WHERE relname='contratos'"
        )).scalar()
        return 4 if rls else 3


def schema_version_compatible(actual: int, esperada: int = SCHEMA_VERSION) -> bool:
    """La aplicación solo opera contra la versión exacta de esquema requerida."""
    return actual == esperada


def assert_schema_version(esperada: int = SCHEMA_VERSION) -> None:
    actual = schema_version()
    if not schema_version_compatible(actual, esperada):
        raise RuntimeError(
            f"Esquema en versión {actual}, se esperaba {esperada}. "
            "Ejecuta el job de migración (python -m migrate.run) antes de arrancar la API."
        )


_ADD_VALUE = re.compile(r"^\s*ALTER\s+TYPE\s+\w+\s+ADD\s+VALUE\b.*;\s*$",
                        re.IGNORECASE)


def _preparar_script(sql: str) -> tuple[list[str], str]:
    """Separa las extensiones de ENUM del resto del script.

    `ALTER TYPE ... ADD VALUE` se puede ejecutar dentro de una transacción desde
    PG12, pero el valor nuevo **no se puede usar** en esa misma transacción. El
    bloque 7 de `06_migracion_v11.sql` crea un CHECK que referencia
    'contract_admin', así que si el archivo entero va en una sola transacción
    PostgreSQL responde `UnsafeNewEnumValueUsage`. Por eso el encabezado del
    script pide autocommit: psql cumple porque cada sentencia es su propia
    transacción, y aquí se reproduce ejecutando primero cada ADD VALUE por
    separado y confirmándolo antes del resto.

    No se intenta partir el archivo completo en sentencias: los bloques `DO $$`
    y las funciones con cuerpo entre `$$` harían fallar cualquier división por
    punto y coma. Las líneas ADD VALUE, en cambio, son de una sola línea y
    triviales de identificar.
    """
    add_values: list[str] = []
    resto: list[str] = []
    for linea in sql.splitlines():
        if linea.strip().startswith("\\echo"):
            continue          # metacomando de psql; psycopg no lo entiende
        if _ADD_VALUE.match(linea):
            add_values.append(linea.strip())
        else:
            resto.append(linea)
    return add_values, "\n".join(resto)


def apply_schema(schema_dir: str | None = None) -> int:
    """Aplica los scripts pendientes bajo pg_advisory_lock.

    El cerrojo es de PostgreSQL, así que sirve igual si lo invoca el job de
    migración o varias réplicas arrancando a la vez: la primera aplica y las
    demás esperan y encuentran el esquema ya listo.

    Se ejecuta en autocommit para respetar el requisito de los ADD VALUE de
    ENUM (ver `_preparar_script`). El cerrojo es de sesión, así que sobrevive
    igual sin transacción envolvente.
    """
    sdir = schema_dir or settings.schema_dir
    if not os.path.isdir(sdir):
        raise RuntimeError(f"No existe el directorio de esquema {sdir}")

    raw = engine.raw_connection()
    autocommit_previo = getattr(raw.driver_connection, "autocommit", False)
    try:
        raw.driver_connection.autocommit = True
        cur = raw.cursor()
        cur.execute("SELECT pg_advisory_lock(%s)", (MIGRATION_LOCK_ID,))
        try:
            actual = schema_version()
            if actual >= SCHEMA_VERSION:
                return actual
            if actual == 0:
                pendientes = SCHEMA_SCRIPTS
            elif actual == 3:
                pendientes = SCHEMA_SCRIPTS[3:]
            elif actual == 6:
                pendientes = SCHEMA_SCRIPTS[5:]
            elif actual == 7:
                pendientes = ["09_indices_consola.sql", "10_version_sesion.sql",
                              "11_ciclo_vida_contratos.sql"]
            elif actual == 8:
                pendientes = ["10_version_sesion.sql", "11_ciclo_vida_contratos.sql"]
            elif actual == 9:
                pendientes = ["11_ciclo_vida_contratos.sql"]
            elif actual == 10:
                pendientes = ["11_ciclo_vida_contratos.sql"]
            else:
                # Por si viene de otra versión intermedia, aplicamos los scripts desde el 06 en adelante
                pendientes = SCHEMA_SCRIPTS[4:]

            for nombre in pendientes:
                ruta = os.path.join(sdir, nombre)
                if not os.path.exists(ruta):
                    raise RuntimeError(f"Falta el script {nombre} en {sdir}")
                with open(ruta, encoding="utf-8") as f:
                    add_values, resto = _preparar_script(f.read())
                for sentencia in add_values:
                    cur.execute(sentencia)      # confirmada al instante
                if resto.strip():
                    cur.execute(resto)
            return schema_version()
        finally:
            cur.execute("SELECT pg_advisory_unlock(%s)", (MIGRATION_LOCK_ID,))
    finally:
        try:
            raw.driver_connection.autocommit = autocommit_previo
        except Exception:
            pass
        raw.close()
