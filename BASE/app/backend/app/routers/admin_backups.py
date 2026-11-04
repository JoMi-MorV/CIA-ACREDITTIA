"""Respaldos cifrados y exportación de datos de la consola ADMIN."""
from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from starlette.background import BackgroundTask
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config import settings
from ..database import SessionLocal, get_db
from ..deps import err, get_current_user, require_admin
from ..models import User
from ..models_ops import OpsJob
from ..services import ops
from ..services.backups import (BackupError, backup_configured, backup_path, list_backups,
                                restore_backup, verify_backup)
from ..services.console_exports import create_console_export

router = APIRouter(prefix="/admin/backups", tags=["admin"],
                   dependencies=[Depends(require_admin)])


class RestoreBody(BaseModel):
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
    return FileResponse(path, filename=path.name,
                        media_type="application/octet-stream")


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


@router.post("/{backup_id}/restore")
def restaurar(backup_id: str, body: RestoreBody,
              db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    confirmation = body.confirmation
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
        ops.auditar(audit_db, "actualizacion",
                    f"Restauración completada del respaldo {backup_id}",
                    user_id=user.id, entidad_tipo="admin_backup")
        audit_db.commit()
    return result


@router.get("/export")
def exportar(resp: Response,
             formato: str = Query("zip", pattern="^(zip|pdf)$"),
             db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    try:
        path, media_type, temporary = create_console_export(db, formato)
    except (ValueError, OSError) as exc:
        raise err(500, "EXPORTACION_FALLIDA", str(exc)) from exc
    try:
        ops.auditar(
            db, "visualizacion",
            f"Exportación ADMIN en formato {formato}; datos administrativos autorizados",
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
