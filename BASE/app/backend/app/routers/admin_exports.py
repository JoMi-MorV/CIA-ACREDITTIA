"""Exportaciones inmediatas de datos de negocio y archivos documentales."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from ..database import get_db, worker_session
from ..deps import err, get_current_user, require_admin
from ..models import AdminAccessGrant, Company, Contrato, Sujeto, User
from ..services import actividad
from ..services.business_exports import (
    DEFAULT_CATEGORIES,
    EXPORT_CATEGORIES,
    BusinessExportError,
    create_business_export,
)

router = APIRouter(
    prefix="/admin/exports",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


class BusinessExportIn(BaseModel):
    alcance: Literal["empresa", "contrato", "persona", "equipo"]
    company_id: uuid.UUID
    recurso_id: uuid.UUID | None = None
    categorias: list[str] = Field(default_factory=lambda: list(DEFAULT_CATEGORIES))
    motivo: str = Field(min_length=12, max_length=240)


class AuditedExportResponse(FileResponse):
    def __init__(
        self,
        path: Path,
        temporary: TemporaryDirectory,
        grant_id: uuid.UUID,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        metadata: dict,
    ):
        super().__init__(
            path,
            filename=f"acredittia-exportacion-datos-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}.zip",
            media_type="application/zip",
            headers={
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )
        self.temporary = temporary
        self.grant_id = grant_id
        self.user_id = user_id
        self.company_id = company_id
        self.audit_metadata = metadata

    async def __call__(self, scope, receive, send):
        body_sent = False

        async def track_send(message):
            nonlocal body_sent
            await send(message)
            if (message["type"] == "http.response.body"
                    and not message.get("more_body", False)):
                body_sent = True

        result = "respuesta_interrumpida"
        try:
            await super().__call__(scope, receive, track_send)
            if body_sent:
                result = "respuesta_http_completada"
        finally:
            try:
                with worker_session(is_admin=True, user_id=self.user_id) as db:
                    grant = db.get(AdminAccessGrant, self.grant_id)
                    if grant and grant.revoked_at is None:
                        grant.revoked_at = datetime.now(timezone.utc)
                        grant.revoked_by = self.user_id
                    actividad.log(
                        db, self.company_id, "visualizacion", "admin_export",
                        "Transferencia de exportación de datos finalizada",
                        user_id=self.user_id, entidad_tipo="exportacion_datos",
                        entidad_id=self.grant_id,
                        metadata={**self.audit_metadata, "resultado": result},
                    )
                    db.commit()
            finally:
                self.temporary.cleanup()


@router.post("/data")
def exportar_datos(
    body: BusinessExportIn,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    motivo = " ".join(body.motivo.split())
    if len(motivo) < 12:
        raise err(400, "MOTIVO_REQUERIDO",
                  "Indique un motivo de al menos 12 caracteres para exportar")
    if body.alcance == "empresa":
        if body.recurso_id is not None:
            raise err(422, "ALCANCE_INVALIDO",
                      "La exportación de empresa no debe indicar un recurso")
    elif body.recurso_id is None:
        raise err(422, "ALCANCE_REQUERIDO",
                  "Seleccione el contrato, persona o equipo que desea exportar")
    if not db.get(Company, body.company_id):
        raise err(404, "EMPRESA_NO_ENCONTRADA",
                  "La empresa seleccionada no existe")
    if body.alcance == "contrato":
        resource = db.get(Contrato, body.recurso_id)
        resource_valid = bool(
            resource and resource.company_id == body.company_id)
    elif body.alcance in {"persona", "equipo"}:
        resource = db.get(Sujeto, body.recurso_id)
        expected_type = "trabajador" if body.alcance == "persona" else "equipo"
        resource_valid = bool(
            resource and resource.company_id == body.company_id
            and resource.tipo == expected_type)
    else:
        resource_valid = True
    if not resource_valid:
        actividad.log(
            db, body.company_id, "visualizacion", "admin_export",
            "Solicitud de exportación denegada por alcance del recurso",
            user_id=user.id, entidad_tipo="exportacion_datos",
            entidad_id=body.recurso_id,
            metadata={"alcance": body.alcance,
                      "company_id": str(body.company_id),
                      "recurso_id": str(body.recurso_id)
                      if body.recurso_id else None,
                      "motivo": motivo, "resultado": "denegada"},
        )
        db.commit()
        raise err(404, "RECURSO_NO_ENCONTRADO",
                  "El recurso no existe dentro de la empresa seleccionada")
    categorias = list(dict.fromkeys(body.categorias))
    if not categorias:
        raise err(422, "CATEGORIAS_REQUERIDAS",
                  "Seleccione al menos una categoría de datos")
    categorias_invalidas = sorted(set(categorias) - set(EXPORT_CATEGORIES))
    if categorias_invalidas:
        raise err(422, "CATEGORIA_INVALIDA",
                  "Una o más categorías de exportación no son válidas")

    grant = AdminAccessGrant(
        admin_user_id=user.id,
        granted_by=user.id,
        company_id=body.company_id,
        recurso_tipo=f"exportacion_datos_{body.alcance}",
        recurso_id=body.recurso_id,
        motivo=motivo,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    metadata = {
        "alcance": body.alcance,
        "company_id": str(body.company_id),
        "recurso_id": str(body.recurso_id) if body.recurso_id else None,
        "categorias": categorias,
        "motivo": motivo,
    }
    db.add(grant)
    db.flush()
    grant_id = grant.id
    actividad.log(
        db, body.company_id, "visualizacion", "admin_export",
        "Solicitud de exportación de datos de negocio",
        user_id=user.id, entidad_tipo="exportacion_datos", entidad_id=grant.id,
        metadata={**metadata, "resultado": "solicitada"},
    )
    db.commit()

    try:
        path, temporary, counts = create_business_export(
            db, scope=body.alcance, company_id=body.company_id,
            resource_id=body.recurso_id, categories=categorias)
    except Exception as exc:
        db.rollback()
        failed_grant = db.get(AdminAccessGrant, grant_id)
        if failed_grant:
            failed_grant.revoked_at = datetime.now(timezone.utc)
            failed_grant.revoked_by = user.id
        actividad.log(
            db, body.company_id, "visualizacion", "admin_export",
            "Falló la generación de exportación de datos",
            user_id=user.id, entidad_tipo="exportacion_datos", entidad_id=grant_id,
            metadata={**metadata, "resultado": "generacion_fallida",
                      "error_tipo": type(exc).__name__},
        )
        db.commit()
        if isinstance(exc, BusinessExportError):
            message = str(exc)
        else:
            message = ("No se pudo completar el archivo. Verifique el "
                       "almacenamiento e inicie un nuevo intento.")
        raise err(500, "EXPORTACION_FALLIDA", message) from exc

    try:
        actividad.log(
            db, body.company_id, "visualizacion", "admin_export",
            "Generación de exportación de datos completada",
            user_id=user.id, entidad_tipo="exportacion_datos", entidad_id=grant_id,
            metadata={**metadata, "resultado": "generacion_completada",
                      "filas_y_archivos": counts},
        )
        db.commit()
    except Exception:
        temporary.cleanup()
        raise

    return AuditedExportResponse(
        path, temporary, grant_id, user.id, body.company_id,
        {**metadata, "filas_y_archivos": counts},
    )
