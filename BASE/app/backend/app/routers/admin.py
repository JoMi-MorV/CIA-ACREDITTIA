"""Back-office de Acredittia: empresas, catálogo global y datos demo (§5).

Todo el módulo exige rol `admin` (dependencia del router). El admin NO opera con
`X-Company-Id` aquí: estos endpoints administran el catálogo compartido —faenas,
plataformas del mandante, plantillas de requisitos— y el ciclo de vida de las
cuentas, no los datos de una empresa concreta.

Dos cosas que conviene tener presentes:

* **Las plantillas se borran en blando.** `DELETE /admin/requisitos/templates/{id}`
  pone `activo=false`: los `documentos` ya instanciados apuntan a la plantilla y
  siguen existiendo, con su historial y sus archivos. Desactivar significa «no
  volver a instanciarla», nunca «borrar lo instanciado».
* **`reset-demo` es irreversible y solo aplica a `companies.es_demo`.** Borra los
  datos de operación de la empresa demo y vuelve a sembrarla. La tabla
  `actividad` es append-only por trigger (SQLSTATE 55000) y por eso NO se borra:
  el rastro de auditoría sobrevive al reset a propósito.
"""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import and_, delete, func, or_, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import (Page, aplicar_orden, err, paginacion, require_admin, sobre)
from ..models import (
    Actividad, Alerta, Company, CompanyFaenaPlataforma, Contrato,
    ContratoPlantillaOverride, ContratoPlataforma, ContratoRequisito,
    CumplimientoSnapshot, DocEjemplo, Documento, DocumentoArchivo,
    EventoCalendario, Faena, FaenaPlataforma, IaHallazgo, IaReview,
    LicenciaInterna, Plan, PlataformaCredencial, RefreshToken,
    RequisitoTemplate, Sujeto, Suscripcion, User,
)
from ..models_ops import MetricasMensuales
from ..services import actividad
from ..services.checklist import (calc_estado_doc, calc_estado_sujeto,
                                  crear_expediente_conductor, instanciar_docs,
                                  vencimiento_por_plantilla)
from ..security import hash_password
from ..services.storage import get_storage

logger = logging.getLogger("acredittia.admin")

router = APIRouter(prefix="/admin", tags=["admin"],
                   dependencies=[Depends(require_admin)])

AMBITOS: tuple[str, ...] = ("empresa", "personal", "equipo", "emsipor")
TIPOS_REQ: tuple[str, ...] = ("legal", "medico", "capacitacion", "certificacion",
                              "tecnico", "medioambiental")
ESTADOS_CALC: tuple[str, ...] = ("ok", "porvenc", "venc", "falta")

ORDEN_COMPANIES = {"nombre", "rut", "status", "created_at", "updated_at"}
ORDEN_TEMPLATES = {"titulo", "codigo", "ambito", "tipo", "vigencia_meses",
                   "created_at", "updated_at"}

NOTA_SOFT_DELETE = (
    "La plantilla queda inactiva: no se instanciará en altas futuras. Los "
    "documentos ya creados a partir de ella NO se modifican ni se borran.")


# ============================================================================
# Entradas
# ============================================================================
class RejectIn(BaseModel):
    reason: str


class FaenaIn(BaseModel):
    nombre: str
    mandante: str
    grupo: str | None = None
    region: str | None = None
    sector: str = "mineria"
    activa: bool = True
    logo_url: str | None = None
    color: str | None = None
    lat: float | None = None
    lng: float | None = None


class FaenaPatch(BaseModel):
    nombre: str | None = None
    mandante: str | None = None
    grupo: str | None = None
    region: str | None = None
    sector: str | None = None
    activa: bool | None = None
    logo_url: str | None = None
    color: str | None = None
    lat: float | None = None
    lng: float | None = None


class PlataformaIn(BaseModel):
    nombre: str
    descripcion: str | None = None
    url: str | None = None
    nota: str | None = None
    orden: int = 0


class TemplateIn(BaseModel):
    ambito: str
    titulo: str
    codigo: str | None = None
    tipo: str | None = None
    obligatorio: bool = True
    ejemplo_clave: str | None = None
    faena_id: uuid.UUID | None = None
    vigencia_meses: int | None = None
    plataforma: str | None = None
    aplica_a: str | None = None
    activo: bool = True


class TemplatePatch(BaseModel):
    ambito: str | None = None
    titulo: str | None = None
    codigo: str | None = None
    tipo: str | None = None
    obligatorio: bool | None = None
    ejemplo_clave: str | None = None
    faena_id: uuid.UUID | None = None
    vigencia_meses: int | None = None
    plataforma: str | None = None
    aplica_a: str | None = None
    activo: bool | None = None


class AdminUserPatch(BaseModel):
    role: str | None = None
    company_id: uuid.UUID | None = None
    contrato_id: uuid.UUID | None = None
    activo: bool | None = None


class AdminUserRevoke(BaseModel):
    motivo: str | None = None


SEARCH_PERMISSIONS = {
    "empresa": "admin.companies.read",
    "contrato": "admin.contracts.read",
    "trabajador": "admin.subjects.read",
    "usuario": "admin.users.read",
}


# ============================================================================
# Helpers
# ============================================================================
def _iso(v) -> str | None:
    return v.isoformat() if v else None


def _num(v) -> float | None:
    return float(v) if v is not None else None


def _get_company(db: Session, company_id: uuid.UUID) -> Company:
    c = db.get(Company, company_id)
    if not c:
        raise err(404, "NO_ENCONTRADO", "Empresa no existe")
    return c


def _get_faena(db: Session, faena_id: uuid.UUID) -> Faena:
    f = db.get(Faena, faena_id)
    if not f:
        raise err(404, "NO_ENCONTRADO", "Faena no existe")
    return f


def _get_template(db: Session, tid: uuid.UUID) -> RequisitoTemplate:
    t = db.get(RequisitoTemplate, tid)
    if not t:
        raise err(404, "NO_ENCONTRADO", "Plantilla no existe")
    return t


def _cuenta(db: Session, modelo, *filtros) -> int:
    return db.scalar(select(func.count()).select_from(modelo).where(*filtros)) or 0


def _meses_atras(n: int) -> list[date]:
    """Devuelve los primeros días de los últimos `n` meses, en orden ascendente."""
    actual = date.today().replace(day=1)
    salida = []
    for offset in range(n - 1, -1, -1):
        year, month = actual.year, actual.month - offset
        while month <= 0:
            year, month = year - 1, month + 12
        salida.append(date(year, month, 1))
    return salida


def _docs_por_estado(db: Session, company_id: uuid.UUID) -> dict:
    """Documentos de la empresa agrupados por `estado_calc`."""
    filas = db.execute(
        select(Documento.estado_calc, func.count())
        .where(Documento.company_id == company_id)
        .group_by(Documento.estado_calc)).all()
    conteo = {e: 0 for e in ESTADOS_CALC}
    for estado, n in filas:
        conteo[estado] = int(n)
    conteo["total"] = sum(conteo[e] for e in ESTADOS_CALC)
    return conteo


def _sujetos_por_tipo(db: Session, company_id: uuid.UUID | None = None) -> dict:
    """Personal y equipos activos (sin bajas). Sin `company_id` es global."""
    q = (select(Sujeto.tipo, Sujeto.estado, func.count())
         .where(Sujeto.estado != "baja").group_by(Sujeto.tipo, Sujeto.estado))
    if company_id:
        q = q.where(Sujeto.company_id == company_id)
    salida = {"trabajador": {"total": 0, "acreditados": 0},
              "equipo": {"total": 0, "acreditados": 0}}
    for tipo, estado, n in db.execute(q).all():
        if tipo not in salida:
            continue
        salida[tipo]["total"] += int(n)
        if estado == "ok":
            salida[tipo]["acreditados"] += int(n)
    return salida


def _company_out(db: Session, c: Company, contratos: int | None = None) -> dict:
    # `_cumplimiento_empresa` vive en routers/company.py y es el único cálculo
    # de cumplimiento de la empresa: se importa para que el back-office y el
    # panel de la empresa no puedan divergir.
    from .company import _cumplimiento_empresa

    m = _cumplimiento_empresa(db, c.id, None)
    usuarios = _cuenta(db, User, User.company_id == c.id, User.role != "admin")
    corte_actividad = datetime.now(timezone.utc) - timedelta(days=30)
    actividad_30d = _cuenta(db, Actividad, Actividad.company_id == c.id,
                            Actividad.created_at >= corte_actividad)
    usuarios_con_actividad = db.scalar(
        select(func.count(func.distinct(Actividad.user_id))).where(
            Actividad.company_id == c.id,
            Actividad.user_id.is_not(None),
            Actividad.created_at >= corte_actividad)) or 0
    ultimo_evento = db.scalar(select(func.max(Actividad.created_at)).where(
        Actividad.company_id == c.id))
    plan = db.scalar(select(Plan.nombre).join(
        Suscripcion, Suscripcion.plan_id == Plan.id).where(
            Suscripcion.company_id == c.id))
    sujetos = _sujetos_por_tipo(db, c.id)
    return {
        # RUT y email no forman parte del contrato operativo del listado ni
        # del detalle global; se mantienen fuera de esta respuesta.
        "id": str(c.id), "nombre": c.nombre,
        "status": c.status, "es_demo": c.es_demo,
        "rejection_reason": c.rejection_reason,
        "approved_at": _iso(c.approved_at),
        "created_at": _iso(c.created_at),
        "contratos": (contratos if contratos is not None
                      else _cuenta(db, Contrato, Contrato.company_id == c.id)),
        "trabajadores": sujetos["trabajador"]["total"],
        "usuarios": usuarios,
        "plan": plan,
        "actividad": actividad_30d,
        "usuarios_activos": usuarios_con_actividad,
        "actividad_pct": round(100 * usuarios_con_actividad / usuarios)
        if usuarios else 0,
        "ultima_actividad_at": _iso(ultimo_evento),
        "cumplimiento_pct": m["cumplimiento_pct"],
        "docs_ok": m["docs_ok"], "docs_total": m["docs_total"],
    }


def _faena_out(f: Faena, plataformas: int | None = None) -> dict:
    d = {
        "id": str(f.id), "nombre": f.nombre, "mandante": f.mandante,
        "grupo": f.grupo, "region": f.region, "sector": f.sector,
        "activa": f.activa, "logo_url": f.logo_url, "color": f.color,
        "lat": _num(f.lat), "lng": _num(f.lng),
        "created_at": _iso(f.created_at),
    }
    if plataformas is not None:
        d["plataformas"] = plataformas
    return d


def _plataforma_out(p: FaenaPlataforma) -> dict:
    return {
        "id": str(p.id), "faena_id": str(p.faena_id), "nombre": p.nombre,
        "descripcion": p.descripcion, "url": p.url, "nota": p.nota,
        "orden": p.orden,
    }


def _template_out(t: RequisitoTemplate) -> dict:
    return {
        "id": str(t.id), "ambito": t.ambito, "titulo": t.titulo,
        "codigo": t.codigo, "tipo": t.tipo, "obligatorio": t.obligatorio,
        "ejemplo_clave": t.ejemplo_clave,
        "faena_id": str(t.faena_id) if t.faena_id else None,
        "es_estandar": t.faena_id is None,
        "vigencia_meses": t.vigencia_meses, "plataforma": t.plataforma,
        "aplica_a": t.aplica_a, "activo": t.activo,
        "created_at": _iso(t.created_at), "updated_at": _iso(t.updated_at),
    }


def _valida_template(db: Session, ambito: str | None, tipo: str | None,
                     ejemplo_clave: str | None, faena_id: uuid.UUID | None) -> None:
    """Valida antes de tocar la BD: los ENUM y las FK del catálogo dan 500 si no."""
    if ambito is not None and ambito not in AMBITOS:
        raise err(400, "AMBITO_INVALIDO",
                  f"Ámbito debe ser uno de: {', '.join(AMBITOS)}")
    if tipo is not None and tipo not in TIPOS_REQ:
        raise err(400, "TIPO_INVALIDO",
                  f"Tipo debe ser uno de: {', '.join(TIPOS_REQ)}")
    if ejemplo_clave is not None and not db.get(DocEjemplo, ejemplo_clave):
        raise err(400, "EJEMPLO_INEXISTENTE",
                  f"No existe el ejemplo documental '{ejemplo_clave}'")
    if faena_id is not None:
        _get_faena(db, faena_id)


# ============================================================================
# §5.1 — Empresas
# ============================================================================
@router.get("/search")
def global_search(q: str = Query(..., min_length=2, max_length=100),
                  limite: int = Query(8, ge=1, le=25),
                  db: Session = Depends(get_db)):
    """Busca entidades globales con un alcance de permisos explícito.

    El router ya exige `require_admin`; la matriz por tipo deja documentado el
    alcance que podrá separarse en roles más finos sin volver a exponer datos
    personales en los resultados actuales.
    """
    q = q.strip()
    if len(q) < 2:
        raise err(422, "BUSQUEDA_INVALIDA",
                  "Escribe al menos 2 caracteres sin contar espacios exteriores")
    like = f"%{q}%"
    resultados = []

    empresas = db.scalars(select(Company).where(or_(
        Company.nombre.ilike(like), Company.rut.ilike(like),
        Company.email.ilike(like))).order_by(Company.nombre, Company.id)
        .limit(limite + 1)).all()
    for company in empresas[:limite]:
        resultados.append({
            "tipo": "empresa", "id": str(company.id),
            "titulo": company.nombre, "subtitulo": company.status,
            "company_id": str(company.id),
            "permiso": SEARCH_PERMISSIONS["empresa"],
            "detalle": f"/admin/companies/{company.id}",
        })

    contratos = db.execute(select(Contrato, Company.nombre)
                           .join(Company, Company.id == Contrato.company_id)
                           .where(or_(Contrato.nombre.ilike(like),
                                      Contrato.codigo.ilike(like)))
                           .order_by(Contrato.nombre, Contrato.id)
                           .limit(limite + 1)).all()
    for contrato, company_name in contratos[:limite]:
        resultados.append({
            "tipo": "contrato", "id": str(contrato.id),
            "titulo": contrato.nombre, "subtitulo": contrato.estado,
            "empresa": company_name, "company_id": str(contrato.company_id),
            "permiso": SEARCH_PERMISSIONS["contrato"],
            "detalle": f"/admin/companies/{contrato.company_id}",
        })

    trabajadores = db.execute(select(Sujeto, Company.nombre)
                              .join(Company, Company.id == Sujeto.company_id)
                              .where(Sujeto.tipo == "trabajador",
                                     or_(Sujeto.nombre.ilike(like),
                                         Sujeto.cargo.ilike(like)))
                              .order_by(Sujeto.nombre, Sujeto.id)
                              .limit(limite + 1)).all()
    for sujeto, company_name in trabajadores[:limite]:
        resultados.append({
            "tipo": "trabajador", "id": str(sujeto.id),
            "titulo": sujeto.nombre, "subtitulo": sujeto.cargo or sujeto.tipo,
            "empresa": company_name, "company_id": str(sujeto.company_id),
            "permiso": SEARCH_PERMISSIONS["trabajador"],
            "detalle": f"/admin/companies/{sujeto.company_id}",
        })

    usuarios = db.execute(select(User, Company.nombre)
                          .join(Company, Company.id == User.company_id)
                          .where(or_(User.nombre.ilike(like),
                                     User.email.ilike(like)))
                          .order_by(User.nombre, User.id)
                          .limit(limite + 1)).all()
    for user, company_name in usuarios[:limite]:
        resultados.append({
            "tipo": "usuario", "id": str(user.id),
            "titulo": user.nombre or "Usuario sin nombre",
            "subtitulo": user.role, "empresa": company_name,
            "company_id": str(user.company_id),
            "permiso": SEARCH_PERMISSIONS["usuario"],
            "detalle": f"/admin/companies/{user.company_id}",
        })

    return {
        "query": q, "permisos": SEARCH_PERMISSIONS,
        # Compatibilidad: total cuenta los elementos devueltos, no todas las coincidencias.
        "total": len(resultados), "items": resultados,
        "limite_por_categoria": limite,
        "hay_mas": any(len(filas) > limite for filas in
                       (empresas, contratos, trabajadores, usuarios)),
    }


@router.get("/audit")
def global_audit(modulo: str | None = Query(None),
                 tipo: str | None = Query(None),
                 user_id: uuid.UUID | None = Query(None),
                 desde: date | None = Query(None),
                 hasta: date | None = Query(None),
                 p: Page = Depends(paginacion),
                 db: Session = Depends(get_db)):
    """Auditoría global de toda la plataforma, solo para administradores."""
    q = (select(Actividad, User.nombre.label("actor_nombre"),
                Company.nombre.label("empresa"))
         .outerjoin(User, User.id == Actividad.user_id)
            .outerjoin(Company, Company.id == Actividad.company_id))
    if modulo:
        q = q.where(Actividad.modulo == modulo)
    if tipo:
        q = q.where(Actividad.tipo == tipo)
    if user_id:
        q = q.where(Actividad.user_id == user_id)
    if desde:
        q = q.where(Actividad.created_at >= datetime.combine(
            desde, datetime.min.time(), tzinfo=timezone.utc))
    if hasta:
        q = q.where(Actividad.created_at < datetime.combine(
            hasta + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    if p.search:
        like = f"%{p.search}%"
        q = q.where(or_(Actividad.descripcion.ilike(like),
                        Actividad.modulo.ilike(like),
                        Company.nombre.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    filas = db.execute(q.order_by(Actividad.id.desc())
                       .offset(p.offset).limit(p.page_size)).all()
    return sobre([{
        "id": int(a.id), "empresa": empresa or "Plataforma",
        "actor": actor_nombre or (f"Usuario {str(a.user_id)[:8]}" if a.user_id else "Sistema"),
        "tipo": a.tipo, "modulo": a.modulo,
        "descripcion": a.descripcion, "entidad_tipo": a.entidad_tipo,
        "entidad_id": str(a.entidad_id) if a.entidad_id else None,
        "motivo": (a.meta or {}).get("motivo_acceso"),
        "created_at": a.created_at.isoformat(),
    } for a, actor_nombre, empresa in filas], total, p)


def _admin_user_out(db: Session, user: User) -> dict:
    contrato = db.get(Contrato, user.contrato_id) if user.contrato_id else None
    company = db.get(Company, user.company_id) if user.company_id else None
    return {
        # La gestión de cuentas, restringida a ADMIN, necesita una identidad
        # reconocible para asignar permisos al destinatario correcto.
        "id": str(user.id), "nombre": user.nombre, "email": user.email,
        "role": user.role, "activo": user.activo, "status": user.status,
        "company_id": str(user.company_id) if user.company_id else None,
        "company": company.nombre if company else None,
        "contrato_id": str(user.contrato_id) if user.contrato_id else None,
        "contrato": contrato.nombre if contrato else None,
        "last_login_at": _iso(user.last_login_at),
        "created_at": _iso(user.created_at),
    }


@router.get("/users")
def admin_users(role: str | None = Query(None),
                company_id: uuid.UUID | None = Query(None),
                activo: bool | None = Query(None),
                p: Page = Depends(paginacion),
                db: Session = Depends(get_db)):
    """Listado global de usuarios para administradores de plataforma."""
    q = select(User)
    if role:
        q = q.where(User.role == role)
    if company_id:
        q = q.where(User.company_id == company_id)
    if activo is not None:
        q = q.where(User.activo.is_(activo))
    if p.search:
        like = f"%{p.search}%"
        q = q.where(or_(User.nombre.ilike(like), User.email.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    filas = db.scalars(q.order_by(User.last_login_at.desc().nulls_last(),
                                  User.created_at.desc())
                       .offset(p.offset).limit(p.page_size)).all()
    return sobre([_admin_user_out(db, user) for user in filas], total, p)


@router.get("/users/audit")
def admin_users_audit(p: Page = Depends(paginacion),
                      db: Session = Depends(get_db)):
    """Auditoría de cambios de rol, alcance y activación de usuarios."""
    q = (select(Actividad, User.nombre.label("actor_nombre"),
                User.email.label("actor_email"))
         .outerjoin(User, User.id == Actividad.user_id)
         .where(Actividad.modulo == "usuarios",
                Actividad.entidad_tipo == "usuario")
         .order_by(Actividad.created_at.desc()))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    filas = db.execute(q.offset(p.offset).limit(p.page_size)).all()
    return sobre([{
        "id": int(a.id), "usuario_id": str(a.entidad_id) if a.entidad_id else None,
        "accion": a.tipo, "descripcion": a.descripcion,
        "actor": actor_nombre or actor_email or "Sistema",
        "created_at": a.created_at.isoformat(),
    } for a, actor_nombre, actor_email in filas], total, p)


@router.get("/users/catalog")
def admin_users_catalog(db: Session = Depends(get_db)):
    """Catálogo mínimo para asignar empresa y contrato desde la consola."""
    companies = db.scalars(select(Company)
                           .where(Company.status == "approved")
                           .order_by(Company.nombre)).all()
    contratos = db.execute(select(Contrato.id, Contrato.company_id,
                                 Contrato.nombre)
                           .join(Company, Company.id == Contrato.company_id)
                           .where(Company.status == "approved")
                           .order_by(Contrato.nombre)).all()
    return {
        "companies": [{"id": str(c.id), "nombre": c.nombre} for c in companies],
        "contratos": [{"id": str(c.id), "company_id": str(c.company_id),
                       "nombre": c.nombre} for c in contratos],
    }


@router.patch("/users/{user_id}")
def editar_admin_user(user_id: uuid.UUID, body: AdminUserPatch,
                      db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)):
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise err(404, "NO_ENCONTRADO", "Usuario inexistente")
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise err(400, "SIN_CAMBIOS", "No se indicó ningún cambio")

    role = data.get("role", user.role)
    company_id = data.get("company_id", user.company_id)
    contrato_id = data.get("contrato_id", user.contrato_id)
    if role == "admin":
        company_id = None
        contrato_id = None
    elif role == "company":
        if not company_id:
            raise err(400, "EMPRESA_REQUERIDA", "El rol company necesita una empresa")
        contrato_id = None
    elif role == "contract_admin":
        if not company_id or not contrato_id:
            raise err(400, "ALCANCE_REQUERIDO",
                      "contract_admin necesita empresa y contrato")
    else:
        raise err(400, "ROL_INVALIDO",
                  "role debe ser admin, company o contract_admin")

    if company_id and not db.get(Company, company_id):
        raise err(404, "EMPRESA_INEXISTENTE", "La empresa no existe")
    if contrato_id:
        contrato = db.get(Contrato, contrato_id)
        if not contrato or contrato.company_id != company_id:
            raise err(400, "CONTRATO_INVALIDO",
                      "El contrato no pertenece a la empresa indicada")
    cambios = []
    for campo, valor in (("role", role), ("company_id", company_id),
                         ("contrato_id", contrato_id)):
        anterior = getattr(user, campo)
        if anterior != valor:
            setattr(user, campo, valor)
            cambios.append(campo)
    if "activo" in data and user.activo != data["activo"]:
        if user.id == admin.id and not data["activo"]:
            raise err(400, "AUTO_REVOCACION", "No puede desactivar su propia cuenta")
        user.activo = data["activo"]
        _invalidar_sesiones(db, user)
        cambios.append("activo")
    if not cambios:
        return _admin_user_out(db, user)

    if user.company_id:
        actividad.log(db, user.company_id, "actualizacion", "usuarios",
                      f"Permisos de usuario modificados: {', '.join(cambios)}",
                      user_id=admin.id, entidad_tipo="usuario", entidad_id=user.id)
    db.commit()
    db.refresh(user)
    return _admin_user_out(db, user)


@router.post("/users/{user_id}/revoke")
def revocar_admin_user(user_id: uuid.UUID, body: AdminUserRevoke,
                       db: Session = Depends(get_db),
                       admin: User = Depends(require_admin)):
    """Revoca el acceso completo sin borrar la identidad ni su auditoría."""
    user = db.scalar(select(User).where(User.id == user_id).with_for_update())
    if user is None:
        raise err(404, "NO_ENCONTRADO", "Usuario inexistente")
    if user.id == admin.id:
        raise err(400, "AUTO_REVOCACION", "No puede revocar su propia cuenta")
    user.activo = False
    _invalidar_sesiones(db, user)
    if user.company_id:
        actividad.log(db, user.company_id, "actualizacion", "usuarios",
                      f"Acceso revocado{': ' + body.motivo.strip() if body.motivo else ''}",
                      user_id=admin.id, entidad_tipo="usuario", entidad_id=user.id)
    db.commit()
    return {"ok": True, "id": str(user.id), "activo": False}


def _invalidar_sesiones(db: Session, user: User) -> None:
    # Incremento SQL para que las revocaciones concurrentes no pierdan versiones.
    db.execute(update(User).where(User.id == user.id).values(
        auth_version=User.auth_version + 1))
    db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)
    ).values(revoked_at=datetime.now(timezone.utc)))


@router.get("/companies")
def list_companies(status: str | None = Query(None),
                   es_demo: bool | None = Query(None),
                   p: Page = Depends(paginacion),
                   db: Session = Depends(get_db)):
    """Solicitudes y cuentas de empresa, la más reciente primero."""
    q = select(Company)
    if status:
        q = q.where(Company.status == status)
    if es_demo is not None:
        q = q.where(Company.es_demo.is_(es_demo))
    if p.search:
        like = f"%{p.search}%"
        q = q.where(or_(Company.nombre.ilike(like), Company.rut.ilike(like),
                        Company.email.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = aplicar_orden(q, Company, p.sort, ORDEN_COMPANIES, "-created_at")
    filas = list(db.scalars(q.offset(p.offset).limit(p.page_size)))
    return sobre([_company_out(db, c) for c in filas], total, p)


@router.get("/companies/{company_id}")
def detalle_company(company_id: uuid.UUID, db: Session = Depends(get_db)):
    """Ficha de una empresa con sus estadísticas de operación.

    Es la vista que usa el back-office para decidir sobre una cuenta: cuántos
    usuarios y contratos tiene, cuánta gente y cuántos equipos ha cargado y en
    qué estado está su documentación.
    """
    c = _get_company(db, company_id)
    sujetos = _sujetos_por_tipo(db, c.id)
    out = _company_out(db, c)
    out["stats"] = {
        "usuarios": _cuenta(db, User, User.company_id == c.id),
        "usuarios_activos": _cuenta(db, User, User.company_id == c.id,
                                    User.activo.is_(True)),
        "contratos": _cuenta(db, Contrato, Contrato.company_id == c.id),
        "contratos_vigentes": _cuenta(db, Contrato, Contrato.company_id == c.id,
                                      Contrato.estado == "vigente"),
        "personal": sujetos["trabajador"],
        "equipos": sujetos["equipo"],
        "documentos": _docs_por_estado(db, c.id),
        "alertas_activas": _cuenta(db, Alerta, Alerta.company_id == c.id,
                                   Alerta.resuelta_at.is_(None)),
        "cumplimiento_pct": out["cumplimiento_pct"],
    }
    return out


def _set_status(db: Session, company_id: uuid.UUID, admin: User,
                status: str, reason: str | None = None) -> Company:
    c = _get_company(db, company_id)
    c.status = status
    c.approved_by = admin.id
    c.approved_at = datetime.now(timezone.utc)
    c.rejection_reason = reason
    for u in db.scalars(select(User).where(User.company_id == c.id)):
        u.status = status
    actividad.log(db, c.id, "actualizacion", "empresa",
                  f"Cuenta {status} por administrador", user_id=admin.id,
                  entidad_tipo="empresa", entidad_id=c.id)
    db.commit()
    return c


@router.post("/companies/{company_id}/approve")
def approve(company_id: uuid.UUID, db: Session = Depends(get_db),
            admin: User = Depends(require_admin)):
    c = _set_status(db, company_id, admin, "approved")
    return {"id": str(c.id), "status": c.status}


@router.post("/companies/{company_id}/reject")
def reject(company_id: uuid.UUID, body: RejectIn, db: Session = Depends(get_db),
           admin: User = Depends(require_admin)):
    c = _set_status(db, company_id, admin, "rejected", body.reason)
    return {"id": str(c.id), "status": c.status}


# ============================================================================
# §5.2 — Catálogo de faenas y plataformas del mandante
# ============================================================================
@router.post("/faenas", status_code=201)
def crear_faena(body: FaenaIn, db: Session = Depends(get_db),
                admin: User = Depends(require_admin)):
    """Da de alta una faena en el catálogo global.

    `faenas.nombre` es único en toda la plataforma: la faena identifica al
    mandante y sus requisitos, y dos filas con el mismo nombre partirían en dos
    la plantilla efectiva de los contratos.
    """
    nombre = body.nombre.strip()
    if db.scalar(select(Faena.id).where(func.lower(Faena.nombre) == nombre.lower())):
        raise err(409, "FAENA_DUPLICADA", "Ya existe una faena con ese nombre")
    f = Faena(**{**body.model_dump(), "nombre": nombre})
    db.add(f)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise err(409, "FAENA_DUPLICADA", "Ya existe una faena con ese nombre")
    db.add(Actividad(
        company_id=None, user_id=admin.id, tipo="creacion",
        modulo="admin_catalogo", descripcion=f"Faena creada: {f.nombre}",
        entidad_tipo="faena", entidad_id=f.id,
    ))
    db.commit()
    return _faena_out(f, plataformas=0)


@router.patch("/faenas/{faena_id}")
def editar_faena(faena_id: uuid.UUID, body: FaenaPatch,
                 db: Session = Depends(get_db),
                 admin: User = Depends(require_admin)):
    """Edita los datos y el branding de una faena del catálogo."""
    f = _get_faena(db, faena_id)
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise err(400, "SIN_CAMBIOS", "No se indicó ningún campo a modificar")
    nuevo = (data.get("nombre") or "").strip()
    if nuevo and nuevo.lower() != f.nombre.lower():
        if db.scalar(select(Faena.id).where(
                func.lower(Faena.nombre) == nuevo.lower(), Faena.id != f.id)):
            raise err(409, "FAENA_DUPLICADA", "Ya existe una faena con ese nombre")
        data["nombre"] = nuevo
    for k, v in data.items():
        setattr(f, k, v)
    f.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise err(409, "FAENA_DUPLICADA", "Ya existe una faena con ese nombre")
    logger.info("faena %s actualizada por admin=%s (%s)", f.id, admin.id,
                ", ".join(sorted(data)))
    return _faena_out(f, plataformas=_cuenta(db, FaenaPlataforma,
                                             FaenaPlataforma.faena_id == f.id))


@router.post("/faenas/{faena_id}/plataformas", status_code=201)
def crear_plataforma_faena(faena_id: uuid.UUID, body: PlataformaIn,
                           db: Session = Depends(get_db),
                           admin: User = Depends(require_admin)):
    """Agrega una plataforma del mandante a la faena (SIGA, DIRECTIC, …).

    De aquí las heredan los contratos: `contrato_plataformas` copia estas filas
    la primera vez que una empresa personaliza su lista (§8.1). El nombre es
    único dentro de la faena porque es la clave con la que el contrato empareja
    la plataforma heredada.
    """
    f = _get_faena(db, faena_id)
    nombre = body.nombre.strip()
    if not nombre:
        raise err(400, "NOMBRE_REQUERIDO", "El nombre de la plataforma es obligatorio")
    if db.scalar(select(FaenaPlataforma.id).where(
            FaenaPlataforma.faena_id == f.id,
            func.lower(FaenaPlataforma.nombre) == nombre.lower())):
        raise err(409, "PLATAFORMA_DUPLICADA",
                  f"'{nombre}' ya está registrada en {f.nombre}")
    p = FaenaPlataforma(faena_id=f.id, nombre=nombre,
                        descripcion=body.descripcion, url=body.url,
                        nota=body.nota, orden=body.orden)
    db.add(p)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise err(409, "PLATAFORMA_DUPLICADA",
                  f"'{nombre}' ya está registrada en {f.nombre}")
    logger.info("plataforma '%s' añadida a faena %s por admin=%s", nombre, f.id,
                admin.id)
    return _plataforma_out(p)


# ============================================================================
# §5.3 — Plantillas de requisitos (catálogo global)
# ============================================================================
@router.get("/requisitos/templates")
def listar_templates(ambito: str | None = Query(None),
                     faena_id: uuid.UUID | None = Query(None),
                     activo: bool | None = Query(None),
                     p: Page = Depends(paginacion),
                     db: Session = Depends(get_db)):
    """Catálogo completo de plantillas, incluidas las inactivas.

    Es la vista de administración: a diferencia de `GET /requisitos/templates`
    (que devuelve solo lo aplicable a una empresa y solo lo activo), aquí se ven
    también las plantillas desactivadas para poder reactivarlas.
    """
    if ambito and ambito not in AMBITOS:
        raise err(400, "AMBITO_INVALIDO",
                  f"Ámbito debe ser uno de: {', '.join(AMBITOS)}")
    q = select(RequisitoTemplate)
    if ambito:
        q = q.where(RequisitoTemplate.ambito == ambito)
    if faena_id:
        q = q.where(RequisitoTemplate.faena_id == faena_id)
    if activo is not None:
        q = q.where(RequisitoTemplate.activo.is_(activo))
    if p.search:
        like = f"%{p.search}%"
        q = q.where(or_(RequisitoTemplate.titulo.ilike(like),
                        RequisitoTemplate.codigo.ilike(like)))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = aplicar_orden(q, RequisitoTemplate, p.sort, ORDEN_TEMPLATES, "titulo")
    filas = list(db.scalars(q.offset(p.offset).limit(p.page_size)))
    return sobre([_template_out(t) for t in filas], total, p)


@router.post("/requisitos/templates", status_code=201)
def crear_template(body: TemplateIn, db: Session = Depends(get_db),
                   admin: User = Depends(require_admin)):
    """Crea una plantilla de requisito.

    Con `faena_id` la plantilla es un override de esa faena y prevalece por
    título sobre la estándar homónima al instanciar checklists (§8.3); sin
    `faena_id` es estándar y aplica a todos los contratos.
    """
    _valida_template(db, body.ambito, body.tipo, body.ejemplo_clave, body.faena_id)
    titulo = body.titulo.strip()
    if not titulo:
        raise err(400, "TITULO_REQUERIDO", "El título es obligatorio")
    codigo = (body.codigo or "").strip() or None
    if codigo and db.scalar(select(RequisitoTemplate.id).where(
            RequisitoTemplate.codigo == codigo)):
        raise err(409, "CODIGO_DUPLICADO", f"El código '{codigo}' ya existe")
    t = RequisitoTemplate(**{**body.model_dump(), "titulo": titulo,
                             "codigo": codigo})
    db.add(t)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise err(409, "CODIGO_DUPLICADO", f"El código '{codigo}' ya existe")
    logger.info("plantilla %s '%s' creada por admin=%s", t.id, t.titulo, admin.id)
    return _template_out(t)


@router.patch("/requisitos/templates/{template_id}")
def editar_template(template_id: uuid.UUID, body: TemplatePatch,
                    db: Session = Depends(get_db),
                    admin: User = Depends(require_admin)):
    """Edita una plantilla. Los cambios NO se propagan a lo ya instanciado.

    Cambiar el título o la vigencia afecta a los documentos que se creen desde
    ahora; los existentes conservan el título con el que se instanciaron, que es
    el que el mandante ya vio en la plataforma.
    """
    t = _get_template(db, template_id)
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise err(400, "SIN_CAMBIOS", "No se indicó ningún campo a modificar")
    _valida_template(db, data.get("ambito"), data.get("tipo"),
                     data.get("ejemplo_clave"), data.get("faena_id"))
    if "titulo" in data:
        data["titulo"] = (data["titulo"] or "").strip()
        if not data["titulo"]:
            raise err(400, "TITULO_REQUERIDO", "El título es obligatorio")
    if "codigo" in data:
        codigo = (data["codigo"] or "").strip() or None
        if codigo and db.scalar(select(RequisitoTemplate.id).where(
                RequisitoTemplate.codigo == codigo,
                RequisitoTemplate.id != t.id)):
            raise err(409, "CODIGO_DUPLICADO", f"El código '{codigo}' ya existe")
        data["codigo"] = codigo
    for k, v in data.items():
        setattr(t, k, v)
    t.updated_at = datetime.now(timezone.utc)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise err(409, "CODIGO_DUPLICADO", "El código ya existe")
    logger.info("plantilla %s actualizada por admin=%s (%s)", t.id, admin.id,
                ", ".join(sorted(data)))
    out = _template_out(t)
    out["documentos_instanciados"] = _cuenta(db, Documento,
                                             Documento.template_id == t.id)
    out["nota"] = ("Los documentos ya instanciados conservan el título y la "
                   "obligatoriedad con los que se crearon.")
    return out


@router.delete("/requisitos/templates/{template_id}")
def eliminar_template(template_id: uuid.UUID, db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)):
    """Desactiva la plantilla (borrado en blando). Nunca borra documentos."""
    t = _get_template(db, template_id)
    instanciados = _cuenta(db, Documento, Documento.template_id == t.id)
    if not t.activo:
        return {"ok": True, "id": str(t.id), "activo": False,
                "documentos_instanciados": instanciados,
                "ya_estaba_inactiva": True, "nota": NOTA_SOFT_DELETE}
    t.activo = False
    t.updated_at = datetime.now(timezone.utc)
    db.commit()
    logger.info("plantilla %s desactivada por admin=%s (%s documentos vivos)",
                t.id, admin.id, instanciados)
    return {"ok": True, "id": str(t.id), "titulo": t.titulo, "activo": False,
            "documentos_instanciados": instanciados,
            "ya_estaba_inactiva": False, "nota": NOTA_SOFT_DELETE}


# ============================================================================
# §5.4 — Estadísticas globales
# ============================================================================
@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    """KPI de la plataforma.

    `cumplimiento_promedio` es la media SIMPLE del cumplimiento de las empresas
    aprobadas que tienen al menos un documento obligatorio: mide cómo le va a
    una empresa típica. `cumplimiento_global_pct` es la media ponderada por
    documentos y la domina la empresa más grande; se devuelven las dos porque
    responden preguntas distintas.
    """
    total = _cuenta(db, Company)
    pend = _cuenta(db, Company, Company.status == "pending")
    aprob = _cuenta(db, Company, Company.status == "approved")
    rech = _cuenta(db, Company, Company.status == "rejected")

    # Cumplimiento por empresa en una sola pasada: documentos obligatorios no
    # EMSIPOR, que es la misma base que usa `_cumplimiento_empresa`.
    filas = db.execute(
        select(Documento.company_id,
               func.count().label("total"),
               func.count().filter(Documento.estado_calc == "ok").label("ok"))
        .select_from(Documento)
        .join(Company, Company.id == Documento.company_id)
        .where(Documento.obligatorio.is_(True),
               Documento.es_emsipor.is_(False),
               Company.status == "approved")
        .group_by(Documento.company_id)).all()
    pcts = [round(100 * int(f.ok) / int(f.total)) for f in filas if int(f.total)]
    docs_total = sum(int(f.total) for f in filas)
    docs_ok = sum(int(f.ok) for f in filas)

    sujetos = _sujetos_por_tipo(db)

    # El dashboard distingue falta de vencimiento: mezclar ambos estados
    # oculta dos acciones operativas distintas para el administrador.
    estados_documentos = dict(db.execute(
        select(Documento.estado_calc, func.count())
        .where(Documento.obligatorio.is_(True), Documento.es_emsipor.is_(False))
        .group_by(Documento.estado_calc)).all())
    documentos = {
        "total": sum(int(v) for v in estados_documentos.values()),
        "ok": int(estados_documentos.get("ok", 0)),
        "pendientes": int(estados_documentos.get("falta", 0)),
        "por_vencer": int(estados_documentos.get("porvenc", 0)),
        "vencidos": int(estados_documentos.get("venc", 0)),
    }

    usuarios_total = _cuenta(db, User, User.role != "admin")
    usuarios_activos = _cuenta(db, User, User.role != "admin",
                               User.activo.is_(True))
    clientes_activos = db.scalar(
        select(func.count(func.distinct(Suscripcion.company_id)))
        .join(Company, Company.id == Suscripcion.company_id)
        .where(Company.status == "approved",
               Suscripcion.estado.in_(("activa", "trial")))) or 0

    # Actividad global: además del total, se entrega desglose y serie mensual
    # para que el dashboard no dependa de una tabla de actividad paginada.
    actividad_por_modulo = dict(db.execute(
        select(Actividad.modulo, func.count())
        .group_by(Actividad.modulo).order_by(func.count().desc())).all())
    actividad_por_tipo = dict(db.execute(
        select(Actividad.tipo, func.count())
        .group_by(Actividad.tipo).order_by(func.count().desc())).all())
    inicio_actividad = datetime.now(timezone.utc) - timedelta(days=30)
    actividad_30d = _cuenta(db, Actividad, Actividad.created_at >= inicio_actividad)
    actividad_mensual_filas = db.execute(
        select(func.date_trunc("month", Actividad.created_at).label("mes"),
               func.count().label("total"))
        .where(Actividad.created_at >= datetime.combine(
            _meses_atras(12)[0], datetime.min.time(), tzinfo=timezone.utc))
        .group_by("mes").order_by("mes")).all()
    actividad_mensual = {f.mes.strftime("%Y-%m"): int(f.total)
                         for f in actividad_mensual_filas}
    actividad_evolucion = [
        {"mes": mes.strftime("%Y-%m"), "eventos": actividad_mensual.get(
            mes.strftime("%Y-%m"), 0)} for mes in _meses_atras(12)]
    actividad_reciente = db.execute(
        select(Actividad, Company.nombre.label("company_nombre"))
        .outerjoin(Company, Company.id == Actividad.company_id)
        .order_by(Actividad.created_at.desc()).limit(12)).all()
    actividad_ultimas = [{
        "id": int(a.id), "empresa": nombre or "Plataforma", "tipo": a.tipo,
        "modulo": a.modulo, "descripcion": a.descripcion,
        "created_at": a.created_at.isoformat(),
    } for a, nombre in actividad_reciente]

    actividad_empresas = db.execute(
        select(Company.id, Company.nombre,
               func.count(func.distinct(User.id)).label("usuarios"),
               func.count(func.distinct(Actividad.user_id)).label("activos"))
        .outerjoin(User, and_(User.company_id == Company.id,
                              User.role != "admin", User.activo.is_(True)))
        .outerjoin(Actividad, and_(Actividad.company_id == Company.id,
                                   Actividad.created_at >= inicio_actividad))
        .where(Company.status == "approved")
        .group_by(Company.id, Company.nombre)).all()
    clientes_baja_actividad = [{
        "company_id": str(f.id), "nombre": f.nombre,
        "usuarios": int(f.usuarios), "usuarios_activos": int(f.activos),
        "actividad_pct": round(100 * int(f.activos) / int(f.usuarios))
        if f.usuarios else 0,
    } for f in actividad_empresas
        if not int(f.usuarios) or int(f.activos) * 2 < int(f.usuarios)]
    clientes_baja_actividad.sort(key=lambda f: (f["actividad_pct"], f["nombre"]))

    # No existe una columna de duración de sesión. Se informa el dato real de
    # sesiones vigentes y una estimación de uso basada en eventos por usuario.
    ahora = datetime.now(timezone.utc)
    sesiones_vigentes = _cuenta(db, RefreshToken,
                                RefreshToken.revoked_at.is_(None),
                                RefreshToken.expires_at > ahora)
    usuarios_con_actividad = db.scalar(
        select(func.count(func.distinct(Actividad.user_id))).where(
            Actividad.user_id.is_not(None),
            Actividad.created_at >= inicio_actividad)) or 0
    rangos_uso = select(
        Actividad.user_id,
        func.extract("epoch", func.max(Actividad.created_at)
                             - func.min(Actividad.created_at))
        .label("segundos"),
    ).where(Actividad.user_id.is_not(None),
            Actividad.created_at >= inicio_actividad).group_by(Actividad.user_id).subquery()
    uso = db.scalar(select(func.avg(rangos_uso.c.segundos / 60)))
    inicio_sesiones = ahora - timedelta(days=30)
    duracion_sesiones = db.execute(select(
        func.avg(func.extract(
            "epoch", func.coalesce(RefreshToken.revoked_at, ahora)
            - RefreshToken.created_at) / 60).label("promedio_minutos"),
        func.count().label("medidas"),
    ).where(RefreshToken.created_at >= inicio_sesiones)).one()

    # DAU y WAU se calculan sobre usuarios con eventos reales, no sobre
    # cuentas habilitadas: así la métrica representa uso y no solo capacidad.
    inicio_dau = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    usuarios_activos_diarios = db.scalar(select(
        func.count(func.distinct(Actividad.user_id))).where(
            Actividad.user_id.is_not(None), Actividad.created_at >= inicio_dau)) or 0
    usuarios_activos_semanales = db.scalar(select(
        func.count(func.distinct(Actividad.user_id))).where(
            Actividad.user_id.is_not(None),
            Actividad.created_at >= ahora - timedelta(days=7))) or 0
    dau_filas = db.execute(select(
        func.date(Actividad.created_at).label("dia"),
        func.count(func.distinct(Actividad.user_id)).label("usuarios"),
    ).where(Actividad.user_id.is_not(None),
            Actividad.created_at >= ahora - timedelta(days=30))
        .group_by("dia").order_by("dia")).all()
    wau_filas = db.execute(select(
        func.date_trunc("week", Actividad.created_at).label("semana"),
        func.count(func.distinct(Actividad.user_id)).label("usuarios"),
    ).where(Actividad.user_id.is_not(None),
            Actividad.created_at >= ahora - timedelta(weeks=12))
        .group_by("semana").order_by("semana")).all()

    procesados = db.execute(select(
        func.count().label("total"),
        func.count().filter(IaReview.status == "done").label("completados"),
        func.count().filter(IaReview.status == "processing").label("en_proceso"),
        func.count().filter(IaReview.status == "queued").label("pendientes"),
        func.count().filter(IaReview.status == "failed").label("fallidos"),
    )).one()

    # La serie comercial usa snapshots existentes; no se inventa MRR cuando no
    # hay cierre mensual y se conserva el valor como null.
    mrr_filas = db.scalars(select(MetricasMensuales)
                           .where(MetricasMensuales.mes >= _meses_atras(12)[0])
                           .order_by(MetricasMensuales.mes)).all()
    mrr_evolucion = [{"mes": f.mes.strftime("%Y-%m"), "mrr": float(f.mrr_clp),
                      "clientes_activos": f.clientes_activos}
                     for f in mrr_filas]

    empresas_baja_acreditacion = db.execute(
        select(Company.id, Company.nombre,
               func.count().label("documentos"),
               func.count().filter(Documento.estado_calc == "ok").label("ok"))
        .join(Documento, Documento.company_id == Company.id)
        .where(Company.status == "approved", Documento.obligatorio.is_(True),
               Documento.es_emsipor.is_(False))
        .group_by(Company.id, Company.nombre)).all()
    baja_acreditacion = [{
        "company_id": str(f.id), "empresa": f.nombre,
        "documentos": int(f.documentos), "documentos_ok": int(f.ok),
        "acreditacion_pct": round(100 * int(f.ok) / int(f.documentos)),
    } for f in empresas_baja_acreditacion
        if int(f.documentos) and int(f.ok) * 100 < int(f.documentos) * 70]
    baja_acreditacion.sort(key=lambda f: (f["acreditacion_pct"], f["empresa"]))

    contratos_pendientes = db.execute(
        select(Contrato.id, Contrato.nombre, Contrato.company_id,
               Company.nombre.label("empresa"),
               func.count().filter(Documento.estado_calc.in_(("falta", "venc")))
               .label("pendientes"))
        .join(Company, Company.id == Contrato.company_id)
        .outerjoin(Documento, Documento.contrato_id == Contrato.id)
        .where(Company.status == "approved")
        .group_by(Contrato.id, Contrato.nombre, Contrato.company_id,
                  Company.nombre)
        .having(func.count().filter(Documento.estado_calc.in_(("falta", "venc"))) >= 3)
        .order_by(func.count().filter(Documento.estado_calc.in_(("falta", "venc"))).desc())
        .limit(25)).all()
    contratos_con_pendientes = [{
        "contrato_id": str(f.id), "contrato": f.nombre,
        "company_id": str(f.company_id), "empresa": f.empresa,
        "documentos_pendientes": int(f.pendientes),
    } for f in contratos_pendientes]

    vencidos_filas = db.execute(
        select(Company.id, Company.nombre, func.count().label("vencidos"))
        .join(Documento, Documento.company_id == Company.id)
        .where(Company.status == "approved", Documento.estado_calc == "venc")
        .group_by(Company.id, Company.nombre)
        .order_by(func.count().desc())).all()
    vencidos_por_empresa = [{
        "company_id": str(f.id), "empresa": f.nombre,
        "documentos_vencidos": int(f.vencidos),
    } for f in vencidos_filas]

    morosos_filas = db.execute(
        select(Company.id, Company.nombre, Plan.nombre.label("plan"))
        .join(Suscripcion, Suscripcion.company_id == Company.id)
        .join(Plan, Plan.id == Suscripcion.plan_id)
        .where(Company.status == "approved", Suscripcion.estado == "morosa")
        .order_by(Company.nombre)).all()
    clientes_morosos = [{"company_id": str(f.id), "empresa": f.nombre,
                         "plan": f.plan} for f in morosos_filas]

    alertas_filas = db.execute(
        select(Alerta, Company.nombre.label("empresa"))
        .join(Company, Company.id == Alerta.company_id)
        .where(Alerta.resuelta_at.is_(None))
        .order_by(Alerta.created_at.desc()).limit(50)).all()
    bandeja_alertas = [{
        "id": str(a.id), "empresa": empresa, "company_id": str(a.company_id),
        "severidad": a.severidad, "estado": a.estado, "origen": a.origen,
        "titulo": a.titulo, "descripcion": a.descripcion,
        "created_at": a.created_at.isoformat(),
    } for a, empresa in alertas_filas]

    return {
        "empresas_total": total, "pendientes": pend, "aprobadas": aprob,
        "rechazadas": rech,
        "contratos_total": _cuenta(db, Contrato),
        "faenas_total": _cuenta(db, Faena),
        "faenas_activas": _cuenta(db, Faena, Faena.activa.is_(True)),
        "plantillas_activas": _cuenta(db, RequisitoTemplate,
                                      RequisitoTemplate.activo.is_(True)),
        "personal": sujetos["trabajador"],
        "equipos": sujetos["equipo"],
        # Se conserva por compatibilidad con la versión anterior del endpoint.
        "sujetos_total": sujetos["trabajador"]["total"] + sujetos["equipo"]["total"],
        "usuarios_total": usuarios_total,
        "usuarios_activos": usuarios_activos,
        "clientes_activos": int(clientes_activos),
        "documentos_total": docs_total, "documentos_ok": docs_ok,
        "documentos": documentos,
        "cumplimiento_promedio": round(sum(pcts) / len(pcts)) if pcts else 0,
        "cumplimiento_global_pct": (round(100 * docs_ok / docs_total)
                                    if docs_total else 0),
        "empresas_medidas": len(pcts),
        "actividad_global": {
            "total": _cuenta(db, Actividad),
            "ultimos_30_dias": actividad_30d,
            "por_modulo": actividad_por_modulo,
            "por_tipo": actividad_por_tipo,
            "evolucion_mensual": actividad_evolucion,
            "ultimas": actividad_ultimas,
            "clientes_baja_actividad": clientes_baja_actividad,
        },
        "sesiones": {
            "vigentes": sesiones_vigentes,
            "usuarios_con_actividad_30d": usuarios_con_actividad,
            "tiempo_uso_promedio_minutos_30d": round(float(uso), 1) if uso else 0,
            "tiempo_uso_es_estimado": True,
            "duracion_promedio_minutos_30d": round(
                float(duracion_sesiones.promedio_minutos), 1)
            if duracion_sesiones.promedio_minutos else 0,
            "sesiones_medidas_30d": int(duracion_sesiones.medidas),
            "duracion_es_estimada": True,
            "usuarios_activos_diarios": int(usuarios_activos_diarios),
            "usuarios_activos_semanales": int(usuarios_activos_semanales),
            "evolucion_dau": [{"dia": f.dia.isoformat(), "usuarios": int(f.usuarios)}
                              for f in dau_filas],
            "evolucion_wau": [{"semana": f.semana.date().isoformat(), "usuarios": int(f.usuarios)}
                              for f in wau_filas],
        },
        "documentos_procesados": {
            "total": int(procesados.total),
            "completados": int(procesados.completados),
            "en_proceso": int(procesados.en_proceso),
            "pendientes": int(procesados.pendientes),
            "fallidos": int(procesados.fallidos),
        },
        "mrr": {
            "actual": mrr_evolucion[-1]["mrr"] if mrr_evolucion else None,
            "evolucion_mensual": mrr_evolucion,
        },
        "salud_clientes": {
            "empresas_baja_acreditacion": baja_acreditacion,
            "contratos_con_pendientes": contratos_con_pendientes,
            "vencidos_por_empresa": vencidos_por_empresa,
            "clientes_morosos": clientes_morosos,
            "bandeja_alertas": bandeja_alertas,
        },
    }


# ============================================================================
# §5.5 — Reinicio de la empresa demo
# ============================================================================
# Dotación de la empresa demo. RUT y patente se generan al sembrar para que sean
# válidos y estables; el cargo va como texto porque `checklist.resolver_cargo`
# es quien decide si crearlo en el catálogo de la empresa.
DEMO_CONTRATOS = [
    ("Transporte de Personal Mina", "CTR-DEMO-001", "Los Pelambres"),
    ("Servicios de Mantención Planta", "CTR-DEMO-002", "Minera Centinela"),
    ("Movimiento de Tierra Fase Norte", "CTR-DEMO-003", "Zaldívar"),
    ("Perforación y Tronadura", "CTR-DEMO-004", "Antucoya"),
    ("Mantención de Caminos Industriales", "CTR-DEMO-005", "Candelaria"),
    ("Operación de Equipos de Apoyo", "CTR-DEMO-006", "Caserones"),
    ("Servicios Eléctricos de Faena", "CTR-DEMO-007", "Andina"),
    ("Transporte de Insumos y Residuos", "CTR-DEMO-008", "El Teniente"),
]
DEMO_PERSONAL = [
    ("Juan Pérez Soto", "Conductor Nacional", True),
    ("María González Rojas", "Supervisora de Terreno", False),
    ("Carlos Muñoz Araya", "Conductor Nacional", True),
    ("Patricia Silva Contreras", "Prevencionista de Riesgos", False),
    ("Luis Fuentes Cárdenas", "Operador de Equipo Pesado", False),
    ("Rodrigo Tapia Núñez", "Mecánico Mantenedor", False),
    ("Camila Rojas Valenzuela", "Prevencionista de Riesgos", False),
    ("Andrés Sepúlveda Mella", "Conductor Nacional", True),
    ("Daniela Herrera Pino", "Supervisora de Terreno", False),
    ("Felipe Carrasco Leiva", "Operador de Equipo Pesado", False),
    ("Valentina Orellana Díaz", "Conductor Nacional", True),
    ("Sebastián Lagos Núñez", "Mecánico Mantenedor", False),
    ("Francisca Vidal Cifuentes", "Prevencionista de Riesgos", False),
    ("Tomás Arancibia Soto", "Conductor Nacional", True),
    ("Constanza Paredes Riquelme", "Supervisora de Terreno", False),
    ("Ignacio Morales Figueroa", "Operador de Equipo Pesado", False),
    ("Javiera Contreras Salas", "Conductor Nacional", True),
    ("Matías Bustos Alarcón", "Mecánico Mantenedor", False),
    ("Antonia Reyes Cáceres", "Prevencionista de Riesgos", False),
    ("Nicolás Fuenzalida Vera", "Conductor Nacional", True),
    ("Paula Espinoza Toledo", "Supervisora de Terreno", False),
    ("Cristóbal Sanhueza Pinto", "Operador de Equipo Pesado", False),
    ("Fernanda Molina Godoy", "Conductor Nacional", True),
    ("Benjamín Cáceres Jara", "Mecánico Mantenedor", False),
    ("Josefa Valdés Bravo", "Prevencionista de Riesgos", False),
    ("Vicente Alvarado Tapia", "Conductor Nacional", True),
    ("Trinidad Cárdenas Fuentes", "Supervisora de Terreno", False),
    ("Maximiliano Núñez Palma", "Operador de Equipo Pesado", False),
    ("Emilia Gallardo Reyes", "Conductor Nacional", True),
    ("Joaquín Miranda Silva", "Mecánico Mantenedor", False),
    ("Catalina Campos Ortega", "Prevencionista de Riesgos", False),
    ("Agustín Bravo Escobar", "Conductor Nacional", True),
    ("Florencia Peña Aguilera", "Supervisora de Terreno", False),
    ("Esteban Riquelme Soto", "Operador de Equipo Pesado", False),
]
DEMO_EQUIPOS = [
    ("Tracto-Camión", "Mercedes-Benz", "Actros 2646", 2021),
    ("Camioneta", "Toyota", "Hilux 4x4", 2022),
    ("Camión Aljibe", "Volvo", "FM 440", 2019),
    ("Retroexcavadora", "Caterpillar", "420F", 2020),
    ("Camioneta", "Mitsubishi", "L200 Dakar", 2021),
    ("Bus", "Mercedes-Benz", "OF 1721", 2018),
    ("Camión Pluma", "Scania", "P 280", 2020),
    ("Excavadora", "Komatsu", "PC 210", 2022),
    ("Cargador Frontal", "Caterpillar", "950H", 2017),
    ("Minibús", "Mercedes-Benz", "Sprinter 415", 2023),
    ("Camioneta", "Ford", "Ranger 3.2", 2022),
    ("Motoniveladora", "John Deere", "670G", 2019),
    ("Camión Tolva", "Volvo", "FMX 500", 2021),
    ("Camioneta", "Toyota", "Hilux 4x4", 2023),
    ("Rodillo Compactador", "Bomag", "BW 211", 2018),
    ("Camión Lubricador", "International", "DuraStar", 2019),
    ("Excavadora", "Komatsu", "PC 210", 2020),
    ("Camioneta", "Nissan", "Navara 4x4", 2021),
]

# 1 de cada 3 documentos se deja en `falta` para que la demo tenga pendientes:
# una empresa al 100 % no permite probar alertas ni la matriz de cumplimiento.
DEMO_UNO_DE_CADA = 3


def _dv_rut(cuerpo: str) -> str:
    """Dígito verificador módulo 11 (mismo algoritmo que `security.validar_rut`)."""
    suma, factor = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * factor
        factor = 2 if factor == 7 else factor + 1
    resto = 11 - (suma % 11)
    return "0" if resto == 11 else "K" if resto == 10 else str(resto)


def _rut_demo(n: int) -> str:
    return f"{n:,}".replace(",", ".") + "-" + _dv_rut(str(n))


def _patente_demo(i: int) -> str:
    letras = "BCDFGHJKLPRSTVWXYZ"
    if i < 90:
        base = "".join(letras[(i * 5 + k) % len(letras)] for k in range(4))
        return f"{base}{10 + i:02d}"
    bloque = i // 100
    digitos = []
    for _ in range(4):
        digitos.append(letras[bloque % len(letras)])
        bloque //= len(letras)
    return f"{''.join(reversed(digitos))}{i % 100:02d}"


def asegurar_eventos_operacionales(db: Session, company: Company) -> int:
    hoy = date.today()
    eventos = [
        ("Mantención preventiva de flota", "mantencion", 5,
         "Revisión programada de vehículos y equipos asignados."),
        ("Capacitación de seguridad operacional", "capacitacion", 12,
         "Jornada de actualización de procedimientos de seguridad."),
        ("Entrega de documentación mensual", "administrativo", 20,
         "Consolidación de antecedentes de contratos y personal."),
    ]
    creados = 0
    for titulo, categoria, dias, descripcion in eventos:
        existe = db.scalar(select(EventoCalendario.id).where(
            EventoCalendario.company_id == company.id,
            EventoCalendario.titulo == titulo,
        ))
        if existe is None:
            db.add(EventoCalendario(
                company_id=company.id, titulo=titulo, categoria=categoria,
                fecha=hoy + timedelta(days=dias), descripcion=descripcion,
            ))
            creados += 1
    return creados


def _borrar_datos_empresa(db: Session, cid: uuid.UUID) -> dict:
    """Borra los datos de operación de la empresa. Devuelve los conteos.

    No toca `companies`, `users` de empresa ni `suscripciones`: el reset devuelve
    la demo a su estado inicial de datos, no da de baja la cuenta. Tampoco toca
    `actividad`, que es append-only por trigger (SQLSTATE 55000): el rastro de
    auditoría sobrevive al reset a propósito.
    """
    # Los blobs se borran antes que las filas: sin `blob_path` no hay forma de
    # localizar el archivo en el storage y quedaría huérfano para siempre.
    archivos = list(db.scalars(select(DocumentoArchivo).where(
        DocumentoArchivo.company_id == cid)))
    storage = get_storage()
    blobs = 0
    for a in archivos:
        try:
            storage.delete(a.blob_path)
            blobs += 1
        except Exception:                                   # noqa: BLE001
            logger.warning("no se pudo borrar el blob %s", a.blob_path)

    contratos = list(db.scalars(select(Contrato.id).where(
        Contrato.company_id == cid)))
    revisiones = list(db.scalars(select(IaReview.id).where(
        IaReview.company_id == cid)))

    conteos: dict[str, int] = {"archivos": len(archivos), "blobs": blobs}

    def borrar(clave: str, modelo, *filtros) -> None:
        conteos[clave] = db.execute(
            delete(modelo).where(*filtros)).rowcount or 0

    if revisiones:
        borrar("ia_hallazgos", IaHallazgo, IaHallazgo.review_id.in_(revisiones))
    else:
        conteos["ia_hallazgos"] = 0
    borrar("ia_reviews", IaReview, IaReview.company_id == cid)
    borrar("eventos_calendario", EventoCalendario,
           EventoCalendario.company_id == cid)
    borrar("alertas", Alerta, Alerta.company_id == cid)
    borrar("licencias_internas", LicenciaInterna, LicenciaInterna.company_id == cid)
    borrar("documento_archivos", DocumentoArchivo,
           DocumentoArchivo.company_id == cid)
    borrar("documentos", Documento, Documento.company_id == cid)
    borrar("sujetos", Sujeto, Sujeto.company_id == cid)
    borrar("credenciales", PlataformaCredencial,
           PlataformaCredencial.company_id == cid)
    borrar("contrato_plataformas", ContratoPlataforma,
           ContratoPlataforma.company_id == cid)
    borrar("contrato_requisitos", ContratoRequisito,
           ContratoRequisito.company_id == cid)
    borrar("plantilla_overrides", ContratoPlantillaOverride,
           ContratoPlantillaOverride.company_id == cid)
    borrar("company_faena_plataformas", CompanyFaenaPlataforma,
           CompanyFaenaPlataforma.company_id == cid)
    borrar("snapshots", CumplimientoSnapshot, CumplimientoSnapshot.company_id == cid)
    # `users.contrato_id` cae por CASCADE al borrar el contrato, así que los
    # administradores de contrato se borran explícitamente y se informan: de otro
    # modo desaparecerían sin dejar constancia en la respuesta.
    if contratos:
        borrar("usuarios_contract_admin", User, User.company_id == cid,
               User.contrato_id.in_(contratos))
    else:
        conteos["usuarios_contract_admin"] = 0
    borrar("contratos", Contrato, Contrato.company_id == cid)
    db.flush()
    return conteos


def _sembrar_operacion_empresa(
        db: Session, company: Company, user_id: uuid.UUID, *,
        contratos_data: list[tuple[str, str, str]] | None = None,
        personal_data: list[tuple[str, str, bool]] | None = None,
        equipos_data: list[tuple[str, str, str, int]] | None = None,
        patente_offset: int = 0) -> dict:
    """Crea la dotación operacional de una empresa usando checklists reales.

    Las faenas se buscan por nombre en el catálogo que siembra `app/seeds.py`, y
    los checklists se instancian con `checklist.instanciar_docs` y
    `crear_expediente_conductor`: la demo se construye exactamente con las mismas
    reglas que un alta real, no con inserciones a mano. Deja parte de los
    documentos en `falta` para que existan pendientes que revisar.
    """
    from ..services.checklist import resolver_cargo

    contratos_data = contratos_data or DEMO_CONTRATOS
    personal_data = personal_data or DEMO_PERSONAL
    equipos_data = equipos_data or DEMO_EQUIPOS
    nombres_faena = [c[2] for c in contratos_data]
    faenas = {f.nombre: f for f in db.scalars(select(Faena).where(
        Faena.nombre.in_(nombres_faena)))}
    if not faenas:
        # El catálogo lo siembra `seeds.run` al arrancar; sin faenas no hay nada
        # a lo que colgar un contrato.
        raise err(409, "CATALOGO_VACIO",
                  "El catálogo de faenas está vacío; siembre los datos base antes")

    hoy = date.today()
    creados = {"contratos": 0, "personal": 0, "equipos": 0, "documentos": 0,
               "usuarios_contract_admin": 0,
               "expedientes_emsipor": 0, "cargos": 0}
    contratos: list[Contrato] = []

    for nombre, codigo, faena_nombre in contratos_data:
        faena = faenas.get(faena_nombre) or next(iter(faenas.values()))
        c = Contrato(company_id=company.id, faena_id=faena.id, nombre=nombre,
                     codigo=codigo, fecha_inicio=hoy - timedelta(days=120),
                     fecha_termino=hoy + timedelta(days=610),
                     renovacion_automatica=False, estado="vigente")
        db.add(c)
        db.flush()
        creados["documentos"] += instanciar_docs(
            db, company.id, "empresa", contrato_id=c.id, faena_id=faena.id,
            contrato_plantilla_id=c.id)
        contratos.append(c)
        creados["contratos"] += 1
        email = f"jefatura.{c.codigo.lower()}@acredittia.cl"
        usuario = db.scalar(select(User).where(User.email == email))
        if usuario is None:
            db.add(User(
                email=email, nombre=f"Jefatura {c.codigo}",
                password_hash=hash_password("Demo2026!"),
                role="contract_admin", company_id=company.id,
                contrato_id=c.id, status="approved", activo=True,
            ))
            creados["usuarios_contract_admin"] += 1

    for i, (nombre, cargo_texto, conductor) in enumerate(personal_data):
        c = contratos[i % len(contratos)]
        cargo, nuevo = resolver_cargo(db, company.id, cargo_id=None,
                                      cargo_texto=cargo_texto)
        if nuevo:
            creados["cargos"] += 1
        s = Sujeto(company_id=company.id, contrato_id=c.id, tipo="trabajador",
                   nombre=nombre, rut=_rut_demo(11_000_000 + i * 137_017),
                   cargo=cargo.nombre if cargo else cargo_texto,
                   cargo_id=cargo.id if cargo else None,
                   es_conductor=conductor)
        db.add(s)
        db.flush()
        creados["documentos"] += instanciar_docs(
            db, company.id, "personal", sujeto_id=s.id, faena_id=c.faena_id,
            cargo_id=s.cargo_id, contrato_plantilla_id=c.id)
        if conductor:
            n = crear_expediente_conductor(db, s)
            creados["documentos"] += n
            creados["expedientes_emsipor"] += 1
        creados["personal"] += 1

    for i, (tipo_equipo, marca, modelo, anio) in enumerate(equipos_data):
        c = contratos[i % len(contratos)]
        patente_indice = patente_offset + i
        patente = _patente_demo(patente_indice)
        while db.scalar(select(Sujeto.id).where(Sujeto.patente == patente)):
            patente_indice += 1
            patente = _patente_demo(patente_indice)
        s = Sujeto(company_id=company.id, contrato_id=c.id, tipo="equipo",
                   nombre=f"{marca} {modelo}", patente=patente,
                   tipo_equipo=tipo_equipo, marca=marca, modelo=modelo, anio=anio)
        db.add(s)
        db.flush()
        creados["documentos"] += instanciar_docs(
            db, company.id, "equipo", sujeto_id=s.id, faena_id=c.faena_id,
            contrato_plantilla_id=c.id)
        creados["equipos"] += 1

    db.flush()

    # Se marcan ok dos de cada tres documentos, con el vencimiento derivado de la
    # vigencia de su plantilla. Sin esto la demo arrancaría al 0 % y no habría
    # nada que ver en el dashboard ni en la matriz.
    docs = list(db.scalars(select(Documento).where(
        Documento.company_id == company.id).order_by(Documento.created_at,
                                                     Documento.id)))
    ok = 0
    for i, d in enumerate(docs):
        if i % DEMO_UNO_DE_CADA != 0:
            d.estado = "ok"
            d.vence = vencimiento_por_plantilla(db, d,
                                                desde=hoy - timedelta(days=60))
            ok += 1
        # `estado_calc` es derivado y NO lo recalcula la BD: sin esto los
        # documentos quedarían 'ok' con estado_calc='falta' y el dashboard
        # mostraría 0 % sobre datos que sí están completos.
        d.estado_calc = calc_estado_doc(d)
    creados["documentos_ok"] = ok

    # Y el estado del sujeto se deriva de sus documentos, con la misma regla que
    # el job nocturno de vencimientos.
    por_sujeto: dict[uuid.UUID, list[Documento]] = {}
    for d in docs:
        if d.sujeto_id:
            por_sujeto.setdefault(d.sujeto_id, []).append(d)
    for sujeto in db.scalars(select(Sujeto).where(Sujeto.company_id == company.id)):
        sujeto.estado = calc_estado_sujeto(por_sujeto.get(sujeto.id, []),
                                           sujeto.estado)

    creados["eventos_calendario"] = asegurar_eventos_operacionales(db, company)

    actividad.log(db, company.id, "creacion", "empresa",
                  f"Datos demo regenerados: {creados['contratos']} contratos, "
                  f"{creados['personal']} trabajadores, {creados['equipos']} equipos",
                  user_id=user_id, entidad_tipo="empresa", entidad_id=company.id)
    return creados


@router.post("/companies/{company_id}/reset-demo")
def reset_demo(company_id: uuid.UUID, db: Session = Depends(get_db),
               admin: User = Depends(require_admin)):
    """Reinicia los datos de operación de una empresa demo. Irreversible.

    Solo se permite si `companies.es_demo`: la operación borra contratos,
    sujetos, documentos y archivos sin confirmación por elemento, y sobre una
    empresa real sería una pérdida de datos irrecuperable. `actividad` no se
    borra (append-only), así que el reset queda registrado en el historial.
    """
    c = _get_company(db, company_id)
    if not c.es_demo:
        raise err(409, "NO_ES_DEMO",
                  "Solo se puede reiniciar una empresa marcada como demo")

    try:
        borrados = _borrar_datos_empresa(db, c.id)
    except DBAPIError as e:                                 # noqa: BLE001
        db.rollback()
        # Las tablas append-only (credencial_versiones) rechazan el DELETE con
        # SQLSTATE 55000, incluso en cascada.
        logger.error("reset-demo bloqueado por la BD en empresa %s: %s", c.id, e)
        raise err(409, "RESET_BLOQUEADO",
                  "La base de datos rechazó el borrado de un histórico "
                  "inmutable; revise las credenciales de plataforma rotadas")

    creados = _sembrar_operacion_empresa(db, c, admin.id)
    db.commit()
    logger.info("empresa demo %s reiniciada por admin=%s", c.id, admin.id)

    recuento = _docs_por_estado(db, c.id)
    return {
        "ok": True, "company_id": str(c.id), "nombre": c.nombre,
        "borrados": borrados, "creados": creados,
        "documentos_por_estado": recuento,
        "nota": ("La tabla 'actividad' es append-only y no se borra: el "
                 "historial de auditoría anterior al reset se conserva."),
    }
