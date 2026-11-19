"""Exportaciones de datos de negocio y archivos documentales por alcance."""
from __future__ import annotations

import csv
import io
import json
import tempfile
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from ..models import (
    Actividad,
    Alerta,
    Cargo,
    CargoRequisito,
    Company,
    CompanyFaenaPlataforma,
    Contrato,
    ContratoPlantillaOverride,
    ContratoPlataforma,
    ContratoRequisito,
    CumplimientoSnapshot,
    DocEjemplo,
    Documento,
    DocumentoArchivo,
    EventoCalendario,
    Faena,
    FaenaPlataforma,
    IaHallazgo,
    IaReview,
    LicenciaInterna,
    RequisitoTemplate,
    Sujeto,
    User,
)
from ..models import Base
from .actividad import minimizar_metadata, minimizar_texto
from .storage import get_storage

EXPORT_CATEGORIES = {
    "empresa": ("companies", "users", "company_faena_plataformas"),
    "contratos": ("contratos", "faenas"),
    "personas_equipos": ("sujetos", "licencias_internas", "cargos",
                         "cargo_requisitos"),
    "documentos": ("documentos", "documento_archivos", "ia_reviews",
                   "ia_hallazgos"),
    "alertas": ("alertas",),
    "actividad": ("actividad",),
    "requisitos": ("contrato_requisitos", "contrato_plantilla_overrides",
                   "requisito_templates", "doc_ejemplos"),
    "plataformas": ("contrato_plataformas", "faena_plataformas"),
    "cumplimiento": ("cumplimiento_snapshots",),
    "calendario": ("eventos_calendario",),
}
DEFAULT_CATEGORIES = tuple(EXPORT_CATEGORIES)

_EXCLUDED_COLUMNS = {
    "users": {"password_hash", "auth_version"},
    "documento_archivos": {"blob_path"},
}
_SENSITIVE_NAMES = (
    "password", "token", "secret", "credential", "jwe", "private_key",
)


class BusinessExportError(Exception):
    """Error de generación que debe cancelar el paquete completo."""


def _json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, bytes):
        return "[contenido binario omitido]"
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _csv_value(value: Any) -> Any:
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False, default=str)
    if isinstance(value, str) and value.lstrip(" \t\r\n").startswith(
            ("=", "+", "-", "@")):
        return "'" + value
    return value


def _safe_filename(filename: str) -> str:
    basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    normalized = unicodedata.normalize("NFKC", basename)
    safe = "".join(
        char if char.isalnum() or char in " ._-" else "_"
        for char in normalized
        if ord(char) >= 32 and ord(char) != 127
    ).strip(" .")
    return safe[:160] or "archivo"


def _selected_tables(categories: list[str]) -> list[str]:
    tables = []
    for category in categories:
        tables.extend(EXPORT_CATEGORIES[category])
    return list(dict.fromkeys(tables))


def _scope_queries(db: Session, scope: str, company_id: UUID,
                   resource_id: UUID | None) -> dict[str, Any]:
    contract_ids = select(Contrato.id).where(Contrato.company_id == company_id)
    subject_ids = select(Sujeto.id).where(Sujeto.company_id == company_id)
    if scope == "contrato":
        contract_ids = contract_ids.where(Contrato.id == resource_id)
        subject_ids = subject_ids.where(Sujeto.contrato_id == resource_id)
        target = db.get(Contrato, resource_id)
        if not target or target.company_id != company_id:
            raise BusinessExportError("El contrato no pertenece a la empresa indicada")
    elif scope in {"persona", "equipo"}:
        target = db.get(Sujeto, resource_id)
        expected_type = "trabajador" if scope == "persona" else "equipo"
        if (not target or target.company_id != company_id
                or target.tipo != expected_type):
            raise BusinessExportError(
                "La persona o equipo no pertenece a la empresa indicada")
        contract_ids = contract_ids.where(Contrato.id == target.contrato_id)
        subject_ids = subject_ids.where(Sujeto.id == resource_id)
    elif scope != "empresa":
        raise BusinessExportError("El alcance de exportación no es válido")

    document_ids = select(Documento.id).where(Documento.company_id == company_id)
    if scope == "contrato":
        document_ids = document_ids.where(or_(
            Documento.contrato_id == resource_id,
            Documento.sujeto_id.in_(subject_ids),
        ))
    elif scope in {"persona", "equipo"}:
        document_ids = document_ids.where(Documento.sujeto_id == resource_id)

    archive_ids = select(DocumentoArchivo.id).where(
        DocumentoArchivo.company_id == company_id,
        DocumentoArchivo.documento_id.in_(document_ids),
    )
    review_ids = select(IaReview.id).where(
        IaReview.company_id == company_id,
        IaReview.archivo_id.in_(archive_ids),
    )
    subject_cargo_ids = select(Sujeto.cargo_id).where(
        Sujeto.id.in_(subject_ids), Sujeto.cargo_id.is_not(None))
    requirement_cargo_ids = select(ContratoRequisito.cargo_id).where(
        ContratoRequisito.company_id == company_id,
        ContratoRequisito.contrato_id.in_(contract_ids),
        ContratoRequisito.cargo_id.is_not(None),
    )
    cargo_ids = select(Cargo.id).where(
        or_(
            Cargo.id.in_(subject_cargo_ids),
            Cargo.id.in_(requirement_cargo_ids),
        ))
    template_ids = select(RequisitoTemplate.id).where(or_(
        RequisitoTemplate.id.in_(
            select(Documento.template_id).where(
                Documento.id.in_(document_ids),
                Documento.template_id.is_not(None))),
        RequisitoTemplate.id.in_(
            select(ContratoRequisito.requisito_template_id).where(
                ContratoRequisito.company_id == company_id,
                ContratoRequisito.contrato_id.in_(contract_ids),
                ContratoRequisito.requisito_template_id.is_not(None))),
        RequisitoTemplate.id.in_(
            select(CargoRequisito.requisito_template_id).where(
                CargoRequisito.cargo_id.in_(cargo_ids))),
    ))
    faena_ids = select(Contrato.faena_id).where(Contrato.id.in_(contract_ids))
    platform_ids = select(FaenaPlataforma.id).where(
        FaenaPlataforma.faena_id.in_(faena_ids))
    related_activity = {
        "contract_requirement_ids": select(ContratoRequisito.id).where(
            ContratoRequisito.company_id == company_id,
            ContratoRequisito.contrato_id.in_(contract_ids)),
        "contract_override_ids": select(ContratoPlantillaOverride.id).where(
            ContratoPlantillaOverride.company_id == company_id,
            ContratoPlantillaOverride.contrato_id.in_(contract_ids)),
        "contract_platform_ids": select(ContratoPlataforma.id).where(
            ContratoPlataforma.company_id == company_id,
            ContratoPlataforma.contrato_id.in_(contract_ids)),
        "alerta_ids": select(Alerta.id).where(
            Alerta.company_id == company_id,
            or_(Alerta.contrato_id.in_(contract_ids),
                Alerta.sujeto_id.in_(subject_ids),
                Alerta.documento_id.in_(document_ids))),
        "calendar_ids": select(EventoCalendario.id).where(
            EventoCalendario.company_id == company_id,
            EventoCalendario.documento_id.in_(document_ids)),
    }
    return {
        "contract_ids": contract_ids,
        "subject_ids": subject_ids,
        "document_ids": document_ids,
        "archive_ids": archive_ids,
        "review_ids": review_ids,
        "cargo_ids": cargo_ids,
        "template_ids": template_ids,
        "faena_ids": faena_ids,
        "platform_ids": platform_ids,
        **related_activity,
    }


def _conditions(table_name: str, scope: str, company_id: UUID,
                queries: dict[str, Any]) -> tuple[Any, ...] | None:
    cid = company_id
    contract_ids = queries["contract_ids"]
    subject_ids = queries["subject_ids"]
    document_ids = queries["document_ids"]
    archive_ids = queries["archive_ids"]
    review_ids = queries["review_ids"]
    if table_name == "companies":
        return (Company.id == cid,)
    if table_name == "users":
        return (User.company_id == cid,) if scope == "empresa" else None
    if table_name == "company_faena_plataformas":
        return ((CompanyFaenaPlataforma.company_id == cid,)
                if scope == "empresa" else None)
    if table_name == "contratos":
        return (Contrato.id.in_(contract_ids),)
    if table_name == "faenas":
        return (Faena.id.in_(queries["faena_ids"]),)
    if table_name == "sujetos":
        return (Sujeto.id.in_(subject_ids),)
    if table_name == "licencias_internas":
        return (LicenciaInterna.company_id == cid,
                LicenciaInterna.sujeto_id.in_(subject_ids))
    if table_name == "documentos":
        return (Documento.id.in_(document_ids),)
    if table_name == "documento_archivos":
        return (DocumentoArchivo.company_id == cid,
                DocumentoArchivo.documento_id.in_(document_ids))
    if table_name == "ia_reviews":
        return (IaReview.company_id == cid, IaReview.archivo_id.in_(archive_ids))
    if table_name == "ia_hallazgos":
        return (IaHallazgo.review_id.in_(review_ids),)
    if table_name == "alertas":
        if scope == "empresa":
            return (Alerta.company_id == cid,)
        return (
            Alerta.company_id == cid,
            or_(
                Alerta.contrato_id.in_(contract_ids),
                Alerta.sujeto_id.in_(subject_ids),
                Alerta.documento_id.in_(document_ids),
            ),
        )
    if table_name == "actividad":
        scope_activity = or_(
            Actividad.company_id == cid,
            and_(
                Actividad.company_id.is_(None),
                Actividad.entidad_tipo == "faena_plataforma",
                Actividad.entidad_id.in_(queries["platform_ids"]),
            ),
        )
        if scope == "empresa":
            return (scope_activity,)
        return (
            scope_activity,
            or_(
                and_(Actividad.entidad_tipo == "contrato",
                     Actividad.entidad_id.in_(contract_ids)),
                and_(Actividad.entidad_tipo.in_(
                         ("sujeto", "trabajador", "equipo")),
                     Actividad.entidad_id.in_(subject_ids)),
                and_(Actividad.entidad_tipo == "documento",
                     Actividad.entidad_id.in_(document_ids)),
                and_(Actividad.entidad_tipo.in_(
                         ("archivo", "documento_archivo")),
                     Actividad.entidad_id.in_(archive_ids)),
                and_(Actividad.entidad_tipo == "contrato_requisito",
                     Actividad.entidad_id.in_(
                         queries["contract_requirement_ids"])),
                and_(Actividad.entidad_tipo == "contrato_plantilla_override",
                     Actividad.entidad_id.in_(
                         queries["contract_override_ids"])),
                and_(Actividad.entidad_tipo == "contrato_plataforma",
                     Actividad.entidad_id.in_(
                         queries["contract_platform_ids"])),
                and_(Actividad.entidad_tipo == "faena_plataforma",
                     Actividad.entidad_id.in_(queries["platform_ids"])),
                and_(Actividad.entidad_tipo == "alerta",
                     Actividad.entidad_id.in_(queries["alerta_ids"])),
                and_(Actividad.entidad_tipo == "evento_calendario",
                     Actividad.entidad_id.in_(queries["calendar_ids"])),
                and_(Actividad.entidad_tipo == "ia_review",
                     Actividad.entidad_id.in_(review_ids)),
                and_(Actividad.entidad_tipo == "cargo",
                     Actividad.entidad_id.in_(queries["cargo_ids"])),
                and_(Actividad.entidad_tipo == "usuario",
                     Actividad.entidad_id.in_(select(User.id).where(
                         User.company_id == cid,
                         User.contrato_id.in_(contract_ids)))),
            ),
        )
    if table_name == "cargos":
        return (Cargo.id.in_(queries["cargo_ids"]),)
    if table_name == "cargo_requisitos":
        return (CargoRequisito.cargo_id.in_(queries["cargo_ids"]),)
    if table_name == "contrato_plataformas":
        return (ContratoPlataforma.company_id == cid,
                ContratoPlataforma.contrato_id.in_(contract_ids))
    if table_name == "contrato_requisitos":
        return (ContratoRequisito.company_id == cid,
                ContratoRequisito.contrato_id.in_(contract_ids))
    if table_name == "contrato_plantilla_overrides":
        return (ContratoPlantillaOverride.company_id == cid,
                ContratoPlantillaOverride.contrato_id.in_(contract_ids))
    if table_name == "cumplimiento_snapshots":
        if scope == "empresa":
            return (CumplimientoSnapshot.company_id == cid,)
        return (CumplimientoSnapshot.company_id == cid,
                CumplimientoSnapshot.contrato_id.in_(contract_ids))
    if table_name == "eventos_calendario":
        if scope == "empresa":
            return (EventoCalendario.company_id == cid,)
        return (EventoCalendario.company_id == cid,
                EventoCalendario.documento_id.in_(document_ids))
    if table_name == "faena_plataformas":
        return (FaenaPlataforma.id.in_(queries["platform_ids"]),)
    if table_name == "requisito_templates":
        return (RequisitoTemplate.id.in_(queries["template_ids"]),)
    if table_name == "doc_ejemplos":
        example_keys = select(DocEjemplo.clave).join(
            RequisitoTemplate,
            RequisitoTemplate.ejemplo_clave == DocEjemplo.clave,
        ).where(RequisitoTemplate.id.in_(queries["template_ids"]))
        return (DocEjemplo.clave.in_(example_keys),)
    return None


def _columns(table_name: str):
    table = Base.metadata.tables[table_name]
    return [
        column for column in table.columns
        if column.name not in _EXCLUDED_COLUMNS.get(table_name, set())
        and not any(part in column.name.lower() for part in _SENSITIVE_NAMES)
    ]


def _write_csv_entry(package: ZipFile, path: str, table_name: str,
                     columns, db: Session, query, *, extra_columns=()):
    count = 0
    first_row = True
    with package.open(path, "w") as archive_file:
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)

        def write_row(values):
            nonlocal first_row
            buffer.seek(0)
            buffer.truncate(0)
            writer.writerow(values)
            archive_file.write(buffer.getvalue().encode(
                "utf-8-sig" if first_row else "utf-8"))
            first_row = False

        write_row([column.name for column in columns] + list(extra_columns))
        result = db.execute(query.execution_options(stream_results=True)).mappings()
        for row in result.yield_per(500):
            values = {}
            for column in columns:
                value = _json_value(row[column.name])
                if table_name == "actividad":
                    if column.name == "metadata":
                        value = minimizar_metadata(value)
                    elif isinstance(value, str):
                        value = minimizar_texto(value)
                values[column.name] = value
            write_row([_csv_value(values[column.name]) for column in columns]
                      + list(extra_columns))
            count += 1
    return count


def _document_owner(document: Documento, subject: Sujeto | None) -> tuple[str, UUID]:
    if subject:
        return ("persona" if subject.tipo == "trabajador" else "equipo", subject.id)
    if document.contrato_id:
        return "contrato", document.contrato_id
    return "documento", document.id


def create_business_export(
    db: Session,
    *,
    scope: str,
    company_id: UUID,
    resource_id: UUID | None,
    categories: list[str],
) -> tuple[Path, tempfile.TemporaryDirectory, dict[str, int]]:
    """Build a CSV-and-files ZIP in a temporary directory, streaming rows/blobs."""
    tmp = tempfile.TemporaryDirectory(prefix="acredittia-business-export-")
    root = Path(tmp.name)
    generated = datetime.now().astimezone()
    try:
        queries = _scope_queries(db, scope, company_id, resource_id)
        zip_path = root / "exportacion-datos.zip"
        counts: dict[str, int] = {}
        file_count = 0
        selected_tables = _selected_tables(categories)
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, allowZip64=True) as package:
            for table_name in selected_tables:
                table = Base.metadata.tables.get(table_name)
                if table is None:
                    continue
                conditions = _conditions(table_name, scope, company_id, queries)
                if conditions is None:
                    continue
                columns = _columns(table_name)
                query = select(*columns).select_from(table).where(*conditions)
                if table_name != "documento_archivos":
                    counts[table_name] = _write_csv_entry(
                        package, f"datos/{table_name}.csv", table_name,
                        columns, db, query)
                    continue

                count = 0
                metadata_path = root / "documento_archivos.csv"
                document_query = (
                    select(DocumentoArchivo, Documento, Sujeto)
                    .join(Documento, Documento.id == DocumentoArchivo.documento_id)
                    .outerjoin(Sujeto, Sujeto.id == Documento.sujeto_id)
                    .where(*conditions, Documento.company_id == company_id)
                    .order_by(DocumentoArchivo.id)
                    .execution_options(stream_results=True)
                )
                with metadata_path.open(
                        "w", newline="", encoding="utf-8-sig") as metadata_file:
                    writer = csv.writer(metadata_file)
                    writer.writerow([column.name for column in columns] + ["ruta_archivo"])
                    for archivo, documento, sujeto in (
                            db.execute(document_query).yield_per(100)):
                        if archivo.company_id != company_id or documento.company_id != company_id:
                            raise BusinessExportError(
                                "Se detectó un archivo fuera del alcance autorizado")
                        if archivo.documento_id != documento.id:
                            raise BusinessExportError(
                                "La relación entre documento y archivo no es válida")
                        if sujeto and sujeto.company_id != company_id:
                            raise BusinessExportError(
                                "El titular del documento está fuera del alcance autorizado")
                        tipo, owner_id = _document_owner(documento, sujeto)
                        safe_name = _safe_filename(archivo.filename)
                        archive_path = (
                            f"archivos/{tipo}/{owner_id}/"
                            f"{archivo.id}_{safe_name}")
                        if archivo.blob_path in (None, ""):
                            raise BusinessExportError(
                                "Un archivo documental no tiene una ruta de almacenamiento")
                        with package.open(archive_path, "w") as file_entry:
                            for chunk in get_storage().iter_chunks(archivo.blob_path):
                                file_entry.write(chunk)
                        row_values = []
                        for column in columns:
                            value = _json_value(getattr(archivo, column.name))
                            row_values.append(_csv_value(value))
                        writer.writerow(row_values + [archive_path])
                        count += 1
                        file_count += 1
                package.write(metadata_path, "datos/documento_archivos.csv")
                counts[table_name] = count

            package.writestr("manifest.json", json.dumps({
                "generado_at": generated.isoformat(),
                "alcance": scope,
                "company_id": str(company_id),
                "resource_id": str(resource_id) if resource_id else None,
                "categorias": categories,
                "filas_por_tipo": counts,
                "archivos_incluidos": file_count,
            }, ensure_ascii=False, indent=2))
        counts["archivos_incluidos"] = file_count
        return zip_path, tmp, counts
    except Exception:
        tmp.cleanup()
        raise
