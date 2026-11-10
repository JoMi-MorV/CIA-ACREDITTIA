"""Respaldos cifrados y exportación de datos de la consola ADMIN."""
from __future__ import annotations

import os
import shutil
import uuid
from datetime import datetime, timezone
import tempfile
from pathlib import Path
from starlette.background import BackgroundTask
from fastapi import APIRouter, Depends, File, Header, Query, Response, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import (autorizar_categoria_informacion, err, get_current_user,
                    require_admin)
from ..models import AdminAccessGrant, User
from ..models_ops import OpsJob
from ..services import ops
from ..services.actividad import minimizar_texto
from ..services.backups import (BackupError, backup_configured, backup_path, delete_backup,
                                import_backup, list_backups, restore_backup, verify_backup)
from ..services.console_exports import create_console_export

router = APIRouter(prefix="/admin/backups", tags=["admin"],
                   dependencies=[Depends(require_admin)])


class RestoreBody(BaseModel):
    confirmation: str = Field(min_length=1, max_length=80)


class DeleteBody(BaseModel):
    confirmation: str = Field(min_length=1, max_length=80)


@router.get("/status")
def estado(db: Session = Depends(get_db)):
    job = db.get(OpsJob, "admin_backup")
    next_run = ops.proxima_ejecucion(job) if job and job.activo else None
    configured = backup_configured()
    encrypted = bool(os.environ.get("BACKUP_ENCRYPTION_KEY"))
    tools = all(shutil.which(command) for command in ("pg_dump", "pg_restore"))
    local_storage = settings.storage_backend == "local"
    maintenance_configured = bool(
        settings.backup_restore_database_url
        or (settings.app_env != "production" and configured))
    return {
        "storage_backend": settings.storage_backend,
        "configured": configured and encrypted and tools and local_storage,
        "restore_configured": (configured and encrypted and tools and local_storage
                               and maintenance_configured
                               and (settings.app_env != "production"
                                    or bool(settings.backup_restore_role))),
        "database_configured": configured,
        "encryption_key_configured": encrypted,
        "postgres_tools_available": tools,
        "retention_count": settings.backup_retention_count,
        "schedule": job.cron_expr if job else None,
        "schedule_active": job.activo if job else False,
        "next_run_at": next_run.isoformat() if next_run else None,
        "storage_note": "Los respaldos locales no sustituyen una copia externa fuera del entorno.",
    }


@router.get("")
def respaldos():
    try:
        return {"items": list_backups()}
    except BackupError as exc:
        raise err(503, "RESPALDOS_NO_DISPONIBLES", str(exc)) from exc


@router.post("/import")
async def importar_respaldo(file: UploadFile = File(...),
                            db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    if not file.filename or not file.filename.lower().endswith(".acb"):
        raise err(422, "FORMATO_RESPALDO_INVALIDO", "Seleccione un archivo .acb cifrado")
    with tempfile.NamedTemporaryFile(prefix="acredittia-upload-", suffix=".acb",
                                     delete=False) as uploaded:
        temporary_path = os.path.abspath(uploaded.name)
        try:
            while chunk := await file.read(1024 * 1024):
                uploaded.write(chunk)
        except Exception as exc:
            os.unlink(temporary_path)
            raise err(422, "CARGA_RESPALDO_FALLIDA", "No se pudo recibir el archivo") from exc
    try:
        result = import_backup(Path(temporary_path), file.filename)
    except BackupError as exc:
        raise err(422, "RESPALDO_NO_IMPORTADO", str(exc)) from exc
    finally:
        Path(temporary_path).unlink(missing_ok=True)
    ops.auditar(db, "creacion",
                f"Respaldo importado {result['id']} desde {file.filename}",
                user_id=user.id, entidad_tipo="admin_backup")
    db.commit()
    return result


@router.get("/{backup_id}/download")
def descargar_respaldo(backup_id: str, db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    try:
        path = backup_path(backup_id)
    except BackupError as exc:
        raise err(404, "RESPALDO_NO_ENCONTRADO", str(exc)) from exc
    ops.auditar(db, "visualizacion", f"Descarga de respaldo cifrado {backup_id}",
                user_id=user.id, entidad_tipo="admin_backup")
    db.commit()
    download_name = path.name
    if not download_name.lower().endswith(".acb"):
        download_name = f"{download_name}.acb"
    return FileResponse(
        path,
        filename=download_name,
        media_type="application/octet-stream",
    )


@router.post("/{backup_id}/verify")
def verificar(backup_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    try:
        result = verify_backup(backup_id)
    except BackupError as exc:
        ops.auditar(db, "visualizacion",
                    f"Verificación fallida de respaldo {backup_id}",
                    user_id=user.id, entidad_tipo="admin_backup")
        db.commit()
        raise err(422, "RESPALDO_INVALIDO", str(exc)) from exc
    ops.auditar(db, "visualizacion", f"Respaldo {backup_id} verificado",
                user_id=user.id, entidad_tipo="admin_backup")
    db.commit()
    return result


@router.delete("/{backup_id}")
def eliminar(backup_id: str, body: DeleteBody, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    expected = f"ELIMINAR {backup_id}"
    if body.confirmation != expected:
        raise err(409, "CONFIRMACION_INCORRECTA",
                  f"Escribe exactamente la confirmación: {expected}")
    try:
        result = delete_backup(backup_id)
    except BackupError as exc:
        raise err(404, "RESPALDO_NO_ENCONTRADO", str(exc)) from exc
    ops.auditar(db, "actualizacion", f"Respaldo eliminado {backup_id}",
                user_id=user.id, entidad_tipo="admin_backup")
    db.commit()
    return result


@router.post("/{backup_id}/restore")
def restaurar(backup_id: str, body: RestoreBody,
              db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    confirmation = body.confirmation
    restore_started_at = datetime.now(timezone.utc)
    ops.auditar(
        db, "actualizacion",
        f"Inicio de restauración del respaldo {backup_id}; requiere corte de servicio",
        user_id=user.id, entidad_tipo="admin_backup")
    db.commit()
    # Libera esta conexión antes de que el procedimiento de recuperación cierre
    # las conexiones al esquema/base que será sustituido.
    db.close()
    try:
        result = restore_backup(backup_id, confirmation=confirmation)
    except BackupError as exc:
        with SessionLocal() as audit_db:
            ops.auditar(audit_db, "actualizacion",
                        f"Restauración fallida del respaldo {backup_id}",
                        user_id=user.id, entidad_tipo="admin_backup")
            audit_db.commit()
        raise err(409, "RESTAURACION_FALLIDA", str(exc)) from exc
    with SessionLocal() as audit_db:
        audit_db.execute(text("""
            UPDATE ops_job_runs
               SET status = 'timeout',
                       finished_at = COALESCE(finished_at, now()),
                       mensaje = COALESCE(mensaje, 'Ejecución abierta restaurada desde el snapshot')
             WHERE job_clave = 'admin_backup'
               AND status IN ('queued', 'running')
               AND created_at < :restore_started_at
        """), {"restore_started_at": restore_started_at})
        ops.auditar(audit_db, "actualizacion",
                    f"Restauración completada del respaldo {backup_id}",
                    user_id=user.id, entidad_tipo="admin_backup")
        audit_db.commit()
    return result


@router.get("/export")
def exportar(resp: Response,
             formato: str = Query("zip", pattern="^(zip|pdf)$"),
             motivo: str | None = Query(None),
             user_grant_id: str | None = Header(default=None, alias="X-Access-Grant"),
             db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    motivo = " ".join((motivo or "").split())
    if len(motivo) > 240:
        raise err(400, "MOTIVO_INVALIDO",
                  "El motivo no puede superar 240 caracteres")
    if len(motivo) < 12:
        raise err(400, "MOTIVO_REQUERIDO",
                  "Indique un motivo de al menos 12 caracteres para exportar")
    user_grant: AdminAccessGrant | None = None
    if formato == "zip":
        if user_grant_id is None:
            raise err(403, "PERMISO_INFORMACION_REQUERIDO",
                      "La exportación ZIP requiere concesión vigente de usuarios")
        try:
            parsed_grant_id = uuid.UUID(user_grant_id)
        except ValueError as exc:
            raise err(403, "PERMISO_INFORMACION_INVALIDO",
                      "La concesión no autoriza esta exportación") from exc
        user_grant = autorizar_categoria_informacion(
            "usuario", parsed_grant_id, user, db)
    try:
        path, media_type, temporary = create_console_export(
            db, formato, user_grant=user_grant)
    except (ValueError, OSError) as exc:
        raise err(500, "EXPORTACION_FALLIDA", str(exc)) from exc
    try:
        ops.auditar(
            db, "visualizacion",
            minimizar_texto(
                f"Exportación ADMIN en formato {formato}; motivo: {motivo}"),
            user_id=user.id, entidad_tipo="admin_export")
        db.commit()
    except Exception:
        temporary.cleanup()
        raise
    if resp is not None:
        resp.headers["Cache-Control"] = "no-store"
        resp.headers["X-Content-Type-Options"] = "nosniff"
    extension = "zip" if formato == "zip" else "pdf"
    filename = f"acredittia-admin-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.{extension}"
    return FileResponse(
        path, filename=filename, media_type=media_type,
        background=BackgroundTask(temporary.cleanup))
