"""Dependencias transversales: autenticación, tenant, roles y paginación."""
from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Literal

import jwt
from fastapi import Depends, Header, HTTPException, Query, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from .config import settings
from .database import auth_session, get_db, set_ctx
from .models import AdminAccessGrant, Suscripcion, User
from .security import decode_access_token

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
_METODOS_ESCRITURA = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_RUTAS_PERMITIDAS_EN_SOLO_LECTURA = frozenset({
    ("POST", "/api/v1/suscripcion"),
    ("POST", "/api/v1/suscripcion/solicitudes"),
})
GRACIA_MOROSA_DIAS = 7


def acceso_suscripcion(
        estado: str, periodo_actual_hasta: date | None,
        hoy: date | None = None) -> Literal["completo", "solo_lectura"]:
    hoy = hoy or date.today()
    if estado == "cancelada":
        return "solo_lectura" if (
            periodo_actual_hasta is None or hoy > periodo_actual_hasta
        ) else "completo"
    if estado != "morosa" or periodo_actual_hasta is None:
        return "completo"
    dias = (hoy - periodo_actual_hasta).days
    return "solo_lectura" if dias > GRACIA_MOROSA_DIAS else "completo"


def err(status: int, code: str, message: str, details: list | None = None):
    detail = {"code": code, "message": message}
    if details:
        detail["details"] = details
    return HTTPException(status_code=status, detail=detail)


# ------------------------------------------------------------------ usuario
def get_current_user(
        request: Request,
        token: str | None = Depends(oauth2),
        db: Session = Depends(get_db)) -> User:
    """Resuelve el usuario y fija el contexto de tenant para el resto del request.

    Usa `auth_session()` porque leer `users` exige poder consultar sin tenant.
    Inmediatamente después fija el contexto real, que es el que verán las
    sesiones de negocio (`get_db`) al abrir su transacción.
    """
    if not token:
        raise err(401, "TOKEN_AUSENTE", "Falta el header Authorization")
    try:
        payload = decode_access_token(token)
    except Exception:
        raise err(401, "TOKEN_INVALIDO", "Token inválido o expirado")

    with auth_session() as db:
        # `company` se carga con joinedload porque el User se devuelve DESLIGADO
        # de la sesión: los serializadores (`auth._user_out`) leen
        # `user.company.nombre` ya fuera de ella y una carga diferida ahí
        # levantaría DetachedInstanceError.
        user = db.get(User, uuid.UUID(payload["sub"]),
                      options=[joinedload(User.company)])
        if not user or user.status != "approved" or not user.activo:
            raise err(401, "TOKEN_INVALIDO", "Usuario no válido o desactivado")
        if payload.get("av", 0) != user.auth_version:
            raise err(401, "TOKEN_INVALIDO", "Sesión revocada; inicia sesión nuevamente")
        db.expunge(user)

    # Contexto por defecto: la propia empresa del usuario. El admin lo ajusta
    # con X-Company-Id en get_company_id().
    set_ctx(company_id=user.company_id, is_admin=(user.role == "admin"), user_id=user.id)
    if (
        user.role in ("company", "contract_admin")
        and user.company_id is not None
        and request.method in _METODOS_ESCRITURA
        and (request.method, request.url.path.rstrip("/"))
        not in _RUTAS_PERMITIDAS_EN_SOLO_LECTURA
    ):
        suscripcion = db.scalar(select(Suscripcion).where(
            Suscripcion.company_id == user.company_id))
        if (
            suscripcion is not None
            and suscripcion.estado == "cancelada"
            and acceso_suscripcion(
                suscripcion.estado, suscripcion.periodo_actual_hasta,
            ) == "solo_lectura"
        ):
            raise err(
                403,
                "SUSCRIPCION_SOLO_LECTURA",
                "El período del servicio terminó. Reactiva la suscripción "
                "para volver a operar.",
            )
    return user


def get_current_session_id(token: str | None = Depends(oauth2)) -> uuid.UUID:
    """Obtiene el identificador de sesión autenticado incluido en el JWT."""
    if not token:
        raise err(401, "TOKEN_AUSENTE", "Falta el header Authorization")
    try:
        session_id = decode_access_token(token).get("sid")
        if not session_id:
            raise ValueError("Token sin identificador de sesión")
        return uuid.UUID(str(session_id))
    except (jwt.InvalidTokenError, KeyError, TypeError, ValueError):
        raise err(401, "SESION_INVALIDA", "El token no identifica una sesión vigente")


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise err(403, "SOLO_ADMIN", "Requiere rol administrador")
    return user


def autorizar_categoria_informacion(
    categoria: str,
    grant_id: uuid.UUID | None,
    user: User,
    db: Session,
) -> AdminAccessGrant | None:
    """Autoriza categorías ordinarias y exige concesión para información sensible."""
    if categoria not in {"empresa", "contrato", "trabajador", "equipo",
                         "usuario", "documento"}:
        raise err(400, "CATEGORIA_INVALIDA", "Categoría de información no reconocida")

    if categoria not in {"trabajador", "usuario", "documento"}:
        return None
    if grant_id is None:
        raise err(403, "PERMISO_INFORMACION_REQUERIDO",
                  "Esta categoría requiere una concesión excepcional vigente")

    grant = db.get(AdminAccessGrant, grant_id)
    recurso = grant.recurso_tipo if grant else ""
    recursos_por_categoria = {
        "trabajador": {"trabajador", "personal"},
        "usuario": {"usuario"},
        "documento": {"documento"},
    }
    ahora = datetime.now(timezone.utc)
    if (
        not grant
        or grant.admin_user_id != user.id
        or grant.revoked_at is not None
        or grant.expires_at <= ahora
        or recurso not in recursos_por_categoria[categoria]
    ):
        raise err(403, "PERMISO_INFORMACION_INVALIDO",
                  "La concesión no autoriza esta categoría o ya no está vigente")
    return grant


def validar_alcance_concesion(
    grant: AdminAccessGrant,
    company_id: uuid.UUID,
    recurso_id: uuid.UUID | None = None,
) -> AdminAccessGrant:
    """Limita una concesión sensible a su empresa o recurso autorizado."""
    if grant.company_id is None and grant.recurso_id is None:
        raise err(403, "PERMISO_INFORMACION_INVALIDO",
                  "La concesión debe estar limitada a una empresa o recurso")
    if grant.company_id is not None and grant.company_id != company_id:
        raise err(403, "PERMISO_INFORMACION_INVALIDO",
                  "La concesión no autoriza esta empresa")
    if grant.recurso_id is not None and grant.recurso_id != recurso_id:
        raise err(403, "PERMISO_INFORMACION_INVALIDO",
                  "La concesión no autoriza este recurso")
    return grant


def autorizar_concesion_acotada(
    categoria: str,
    grant_id: uuid.UUID | None,
    user: User,
    db: Session,
    company_id: uuid.UUID,
    recurso_id: uuid.UUID | None = None,
) -> AdminAccessGrant | None:
    if user.role != "admin":
        return None
    grant = autorizar_categoria_informacion(categoria, grant_id, user, db)
    return validar_alcance_concesion(grant, company_id, recurso_id)


def require_sensitive_admin(
    grant_id: uuid.UUID | None = Header(default=None, alias="X-Access-Grant"),
    user: User = Depends(require_admin),
    db: Session = Depends(get_db),
) -> AdminAccessGrant:
    """Exige una concesión vigente y específica para operar datos sensibles."""
    if grant_id is None:
        raise err(403, "ACCESO_EXCEPCIONAL_REQUERIDO",
                  "Esta operación requiere una concesión excepcional vigente")
    grant = db.get(AdminAccessGrant, grant_id)
    now = datetime.now(timezone.utc)
    if (not grant or grant.admin_user_id != user.id
            or grant.revoked_at is not None or grant.expires_at <= now):
        raise err(403, "CONCESION_INVALIDA",
                  "La concesión no existe, fue revocada o expiró")
    return grant


def require_company(user: User = Depends(get_current_user)) -> User:
    """Escritura de datos de empresa: rol company o admin impersonando.

    `contract_admin` queda fuera de las mutaciones de alcance empresa; dentro
    de su contrato se le permite operar y eso se verifica con `require_contrato`.
    """
    if user.role not in ("company", "admin"):
        raise err(403, "ROL_INSUFICIENTE",
                  "El administrador de contrato no puede realizar esta operación")
    return user


def get_company_id(
    user: User = Depends(get_current_user),
    x_company_id: str | None = Header(default=None, alias="X-Company-Id"),
) -> uuid.UUID:
    """company_id efectivo. Para el admin proviene del header X-Company-Id."""
    if user.role in ("company", "contract_admin"):
        return user.company_id
    if x_company_id:
        try:
            cid = uuid.UUID(x_company_id)
        except ValueError:
            raise err(400, "COMPANY_ID_INVALIDO", "X-Company-Id no es un UUID")
        # El admin conserva is_admin=true en RLS pero opera sobre esta empresa.
        set_ctx(company_id=cid, is_admin=True, user_id=user.id)
        return cid
    raise err(400, "COMPANY_ID_REQUERIDO",
              "El admin debe indicar X-Company-Id para operar datos de empresa")


def require_contrato(contrato_id: uuid.UUID, user: User) -> None:
    """Un contract_admin solo puede tocar el contrato que tiene asignado.

    Devuelve 404 y no 403 para no filtrar la existencia del recurso (§3.3).
    """
    if user.role == "contract_admin" and user.contrato_id != contrato_id:
        raise err(404, "NO_ENCONTRADO", "Recurso inexistente")


def contrato_scope(user: User) -> uuid.UUID | None:
    """Contrato al que está acotado el usuario, o None si ve todos."""
    return user.contrato_id if user.role == "contract_admin" else None


# --------------------------------------------------------------- paginación
@dataclass
class Page:
    page: int
    page_size: int
    sort: str | None
    search: str | None

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def paginacion(
    page: int = Query(1, ge=1),
    page_size: int = Query(default=settings.page_size_default, ge=1,
                           le=settings.page_size_max),
    sort: str | None = Query(None, description="campo; prefijo - para descendente"),
    search: str | None = Query(None),
) -> Page:
    return Page(page=page, page_size=page_size, sort=sort, search=search)


def sobre(items: list, total: int, p: Page) -> dict:
    """Envoltura estándar de listados (§3.2 de la especificación)."""
    return {
        "items": items,
        "page": p.page,
        "page_size": p.page_size,
        "total": total,
        "total_pages": (total + p.page_size - 1) // p.page_size if p.page_size else 0,
    }


def aplicar_orden(stmt, modelo, sort: str | None, permitidos: set[str], defecto: str):
    """Traduce `sort=-created_at` a ORDER BY, restringido a campos permitidos."""
    campo = sort or defecto
    desc = campo.startswith("-")
    campo = campo.lstrip("-")
    if campo not in permitidos:
        campo, desc = defecto.lstrip("-"), defecto.startswith("-")
    col = getattr(modelo, campo)
    return stmt.order_by(col.desc() if desc else col.asc())


__all__ = [
    "err", "get_db", "get_current_user", "require_admin", "require_company",
    "get_company_id", "require_contrato", "contrato_scope",
    "Page", "paginacion", "sobre", "aplicar_orden", "Session",
]
