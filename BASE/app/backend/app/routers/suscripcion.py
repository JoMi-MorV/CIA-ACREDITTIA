"""Planes, suscripción y facturación (§17).

Modelo comercial: **suscripción mensual fija**, sin cobro por proceso de
acreditación. Una empresa tiene como máximo una suscripción (`suscripciones`
tiene UNIQUE sobre `company_id`), y esa fila no se borra nunca: cancelar la deja
en `cancelada` conservando el periodo pagado.

Ciclo de estados (§17): `trial` (30 días) → `activa` → `morosa` (pago fallido) →
`cancelada`. `morosa` no corta el acceso de inmediato: durante 7 días desde el
fin del periodo la empresa sigue operando y solo después pasa a solo lectura. El
endpoint expone esa decisión como `acceso` (`completo` | `solo_lectura`) para que
el frontend no reimplemente la regla. La dependencia común de autenticación
bloquea escrituras tras vencer una suscripción cancelada.

Qué NO hace este módulo: no cobra. El inicio del flujo con la pasarela
(Transbank Webpay/OneClick o Stripe) está marcado con un TODO en
`POST /suscripcion`, y la conciliación llega por `POST /webhooks/pagos`
(`routers/webhooks.py`). Mientras no haya pasarela, `POST /suscripcion` deja la
suscripción en `trial` y `pago.requiere_accion` informa de si haría falta un
medio de pago.

`GET /planes` es **público**: es el catálogo de la web comercial y no lleva
dependencia de autenticación. RLS lo permite porque `planes` es un catálogo
global con `SELECT USING (true)` y escritura restringida a admin (§4 de
04_rls.sql).
"""
from __future__ import annotations

import calendar
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..deps import (Page, acceso_suscripcion, aplicar_orden, err,
                    get_company_id, get_current_user, get_db, paginacion,
                    require_admin, require_company, sobre)
from ..models import (Company, Factura, Plan, SolicitudSuscripcion,
                      Suscripcion, User)
from ..services import actividad
from ..services.storage import get_storage

logger = logging.getLogger("acredittia.suscripcion")

router_planes = APIRouter(prefix="/planes", tags=["suscripcion"])
router = APIRouter(prefix="/suscripcion", tags=["suscripcion"])
router_facturas = APIRouter(prefix="/facturas", tags=["suscripcion"])
router_admin = APIRouter(prefix="/admin/planes", tags=["suscripcion"],
                         dependencies=[Depends(require_admin)])
router_admin_suscripciones = APIRouter(
    prefix="/admin/suscripciones", tags=["suscripcion"],
    dependencies=[Depends(require_admin)])

# Días de trial al contratar por primera vez (§17).
TRIAL_DIAS = 30

ESTADOS_FACTURA = ("pendiente", "pagada", "fallida", "anulada")
PERIODOS = ("mensual", "anual")

ORDEN_FACTURAS = {"emitida_at", "pagada_at", "monto", "estado", "created_at"}
ORDEN_PLANES = {"nombre", "precio", "activo", "created_at", "updated_at"}


# ------------------------------------------------------------------ entradas
class SuscripcionIn(BaseModel):
    plan_id: uuid.UUID


class PlanIn(BaseModel):
    nombre: str
    precio: float
    moneda: str = "UF"
    periodo: str = "mensual"
    limites: dict = Field(default_factory=dict)
    activo: bool = True


class PlanPatch(BaseModel):
    nombre: str | None = None
    precio: float | None = None
    moneda: str | None = None
    periodo: str | None = None
    limites: dict | None = None
    activo: bool | None = None


class SolicitudSuscripcionIn(BaseModel):
    tipo: Literal["cambio_plan", "regularizacion"]
    plan_id: uuid.UUID | None = None
    motivo: str = Field(min_length=12, max_length=240)


class ResolverSolicitudSuscripcionIn(BaseModel):
    decision: Literal["aprobada", "rechazada"]
    motivo: str = Field(min_length=12, max_length=240)


# ------------------------------------------------------------------- helpers
def _iso(v: datetime | None) -> str | None:
    return v.isoformat() if v else None


def _fecha(v: date | None) -> str | None:
    return v.isoformat() if v else None


def sumar_mes(d: date, meses: int = 1) -> date:
    """Suma meses de calendario recortando el día al último del mes destino.

    31 de enero + 1 mes es el 28 (o 29) de febrero: es lo que espera un cobro
    mensual y lo que evita saltarse un periodo. Lo usa también
    `routers/webhooks.py` al reactivar una suscripción morosa.
    """
    total = d.month - 1 + meses
    anio = d.year + total // 12
    mes = total % 12 + 1
    return date(anio, mes, min(d.day, calendar.monthrange(anio, mes)[1]))


def _plan_out(p: Plan) -> dict:
    return {
        "id": str(p.id), "nombre": p.nombre,
        # `precio` es numeric(12,2): se serializa como float para el JSON.
        "precio": float(p.precio), "moneda": p.moneda, "periodo": p.periodo,
        "limites": p.limites or {}, "activo": p.activo,
        "created_at": _iso(p.created_at), "updated_at": _iso(p.updated_at),
    }


def dias_restantes_trial(s: Suscripcion, hoy: date | None = None) -> int:
    """Días de trial que quedan. 0 si ya venció o si no está en trial."""
    if s.estado != "trial" or s.trial_hasta is None:
        return 0
    return max(0, (s.trial_hasta - (hoy or date.today())).days)


def acceso_de(s: Suscripcion, hoy: date | None = None) -> str:
    """`completo` o `solo_lectura` según §17.

    Una suscripción cancelada conserva acceso completo hasta el fin del periodo
    vigente y luego pasa a solo lectura.
    Una suscripción morosa conserva el acceso completo durante
    siete días desde el fin del periodo vigente: el impago suele ser un
    problema del medio de pago y cortar el mismo día bloquearía acreditaciones en
    curso. Sin `periodo_actual_hasta` no se puede contar la gracia y se concede
    el acceso completo.
    """
    return acceso_suscripcion(s.estado, s.periodo_actual_hasta, hoy)


def _out(s: Suscripcion, plan: Plan | None = None) -> dict:
    """Suscripción con el plan embebido. Nunca incluye `medio_pago_ref`.

    El token de la pasarela no se devuelve: identifica un medio de pago y no
    aporta nada a la interfaz, que solo necesita saber si existe.
    """
    p = plan or s.plan
    return {
        "id": str(s.id), "estado": s.estado,
        "plan": _plan_out(p) if p is not None else None,
        "trial_hasta": _fecha(s.trial_hasta),
        "dias_restantes_trial": dias_restantes_trial(s),
        "periodo_actual_desde": _fecha(s.periodo_actual_desde),
        "periodo_actual_hasta": _fecha(s.periodo_actual_hasta),
        # El próximo cobro cae al terminar el periodo vigente (suscripción
        # mensual fija: no hay cobros intermedios por uso).
        "proximo_cobro": _fecha(s.periodo_actual_hasta),
        "medio_pago_configurado": bool(s.medio_pago_ref),
        "acceso": acceso_de(s),
        "created_at": _iso(s.created_at), "updated_at": _iso(s.updated_at),
    }


def _estado_cuenta(db: Session, company_id: uuid.UUID) -> str:
    return db.execute(
        text("SELECT ops_estado_cuenta(:company_id)"),
        {"company_id": company_id},
    ).scalar_one()


def _solicitud_out(db: Session, solicitud: SolicitudSuscripcion,
                   empresa: str | None = None) -> dict:
    plan = db.get(Plan, solicitud.plan_id) if solicitud.plan_id else None
    salida = {
        "id": str(solicitud.id),
        "company_id": str(solicitud.company_id),
        "tipo": solicitud.tipo,
        "estado": solicitud.estado,
        "plan": _plan_out(plan) if plan else None,
        "motivo": solicitud.motivo,
        "solicitado_por": str(solicitud.solicitado_por)
        if solicitud.solicitado_por else None,
        "solicitado_at": _iso(solicitud.solicitado_at),
        "resuelto_por": str(solicitud.resuelto_por)
        if solicitud.resuelto_por else None,
        "resuelto_at": _iso(solicitud.resuelto_at),
        "motivo_resolucion": solicitud.motivo_resolucion,
    }
    if empresa is not None:
        salida["empresa"] = empresa
    return salida


def _factura_out(f: Factura) -> dict:
    return {
        "id": str(f.id), "suscripcion_id": str(f.suscripcion_id),
        "folio": f.folio, "monto": float(f.monto), "moneda": f.moneda,
        "estado": f.estado, "gateway_ref": f.gateway_ref,
        "emitida_at": _iso(f.emitida_at), "pagada_at": _iso(f.pagada_at),
        "descargable": bool(f.pdf_blob_path),
        "created_at": _iso(f.created_at),
    }


def _solo_empresa(user: User) -> None:
    """La suscripción es de la empresa, no de un contrato (§17: rol company)."""
    if user.role == "contract_admin":
        raise err(403, "ROL_INSUFICIENTE",
                  "El administrador de contrato no accede a la suscripción")


def suscripcion_de(db: Session, cid: uuid.UUID) -> Suscripcion | None:
    return db.scalar(select(Suscripcion).where(Suscripcion.company_id == cid))


def _get_plan(db: Session, plan_id: uuid.UUID, *, solo_activos: bool) -> Plan:
    p = db.get(Plan, plan_id)
    if p is None:
        raise err(404, "NO_ENCONTRADO", "El plan no existe")
    if solo_activos and not p.activo:
        raise err(400, "PLAN_INACTIVO",
                  "El plan no está disponible para contratación")
    return p


def _valida_periodo(periodo: str) -> str:
    if periodo not in PERIODOS:
        raise err(400, "PERIODO_INVALIDO",
                  f"Periodo debe ser uno de: {', '.join(PERIODOS)}")
    return periodo


def _valida_precio(precio: float) -> float:
    # El CHECK de la tabla exige precio >= 0; se valida antes para dar un 400
    # con mensaje en vez de un 23514 del driver.
    if precio is None or precio < 0:
        raise err(400, "PRECIO_INVALIDO", "El precio no puede ser negativo")
    return precio


# =============================================================================
# §17 — Catálogo público
# =============================================================================
@router_planes.get("")
def listar_planes(db: Session = Depends(get_db)):
    """Catálogo público de planes activos.

    **Sin autenticación**: lo consume la web comercial antes de que exista una
    cuenta. Solo devuelve planes `activo=true` y no se pagina (son unos pocos y
    la página de precios los muestra todos juntos). Los planes retirados se ven
    con `GET /admin/planes`.
    """
    filas = list(db.scalars(select(Plan).where(Plan.activo)
                            .order_by(Plan.precio, Plan.nombre)))
    return {"items": [_plan_out(p) for p in filas], "total": len(filas)}


# =============================================================================
# §17 — Suscripción de la empresa
# =============================================================================
@router.get("")
def detalle(db: Session = Depends(get_db),
            cid: uuid.UUID = Depends(get_company_id),
            user: User = Depends(get_current_user)):
    """Suscripción vigente de la empresa, con el plan y el estado de acceso.

    404 si la empresa nunca contrató: no se inventa una suscripción de cortesía
    en una lectura, porque el alta lleva fechas (trial, periodo) que deben
    nacer de una acción explícita.
    """
    _solo_empresa(user)
    s = suscripcion_de(db, cid)
    if s is None:
        raise err(404, "SIN_SUSCRIPCION",
                  "La empresa no tiene una suscripción; contrátela con "
                  "POST /suscripcion")
    plan = db.get(Plan, s.plan_id)
    salida = _out(s, plan)
    salida["estado_cuenta"] = _estado_cuenta(db, cid)
    return salida


@router.get("/solicitudes")
def listar_solicitudes_empresa(db: Session = Depends(get_db),
                               cid: uuid.UUID = Depends(get_company_id),
                               user: User = Depends(require_company)):
    _solo_empresa(user)
    solicitudes = db.scalars(
        select(SolicitudSuscripcion)
        .where(SolicitudSuscripcion.company_id == cid)
        .order_by(
            (SolicitudSuscripcion.estado == "pendiente").desc(),
            SolicitudSuscripcion.solicitado_at.desc(),
        )
        .limit(20)
    ).all()
    return {"items": [_solicitud_out(db, solicitud)
                      for solicitud in solicitudes]}


@router.post("/solicitudes", status_code=201)
def crear_solicitud_empresa(body: SolicitudSuscripcionIn,
                            db: Session = Depends(get_db),
                            cid: uuid.UUID = Depends(get_company_id),
                            user: User = Depends(require_company)):
    _solo_empresa(user)
    motivo = " ".join(body.motivo.split())
    if len(motivo) < 12:
        raise err(400, "MOTIVO_REQUERIDO",
                  "Indique un motivo de al menos 12 caracteres")

    if db.scalar(select(SolicitudSuscripcion.id).where(
            SolicitudSuscripcion.company_id == cid,
            SolicitudSuscripcion.tipo == body.tipo,
            SolicitudSuscripcion.estado == "pendiente")):
        raise err(409, "SOLICITUD_PENDIENTE",
                  "Ya existe una solicitud pendiente de este tipo")

    plan = None
    if body.tipo == "cambio_plan":
        if body.plan_id is None:
            raise err(400, "PLAN_REQUERIDO",
                      "Seleccione el plan solicitado")
        suscripcion = suscripcion_de(db, cid)
        if suscripcion is None:
            raise err(409, "SIN_SUSCRIPCION",
                      "La primera contratación inicia el trial directamente")
        plan = _get_plan(db, body.plan_id, solo_activos=True)
        if suscripcion.plan_id == plan.id:
            raise err(409, "PLAN_ACTUAL",
                      "La empresa ya tiene este plan")
    elif body.plan_id is not None:
        raise err(400, "PLAN_NO_APLICA",
                  "La regularización no recibe un plan")
    else:
        estado = _estado_cuenta(db, cid)
        if estado not in {"en_riesgo", "moroso"}:
            raise err(409, "CUENTA_NO_REGULARIZABLE",
                      "La cuenta no está en riesgo ni morosa")

    solicitud = SolicitudSuscripcion(
        company_id=cid,
        tipo=body.tipo,
        plan_id=plan.id if plan else None,
        motivo=motivo,
        solicitado_por=user.id,
    )
    db.add(solicitud)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise err(409, "SOLICITUD_PENDIENTE",
                  "Ya existe una solicitud pendiente de este tipo")

    actividad.log(
        db, cid, "creacion", "suscripcion",
        f"Solicitud de {body.tipo} enviada a autorización ADMIN",
        user_id=user.id, entidad_tipo="solicitud_suscripcion",
        entidad_id=solicitud.id,
        metadata={
            "tipo": body.tipo,
            "plan_id": str(plan.id) if plan else None,
            "motivo": motivo,
        },
    )
    db.commit()
    return _solicitud_out(db, solicitud)


@router.post("")
def contratar(body: SuscripcionIn, db: Session = Depends(get_db),
              cid: uuid.UUID = Depends(get_company_id),
              user: User = Depends(require_company)):
    """Inicia el trial o reactiva una suscripción cancelada con el mismo plan.

    Primera contratación: nace en `trial` con 30 días (§17) y un periodo mensual
    abierto desde hoy, de modo que `proximo_cobro` tenga valor desde el principio.

    Los cambios de plan de una suscripción existente se solicitan mediante
    `POST /suscripcion/solicitudes`; una cuenta de empresa aún puede reactivar
    una suscripción cancelada si conserva el mismo plan.

    `pago.requiere_accion` indica si hace falta pasar por la pasarela antes del
    próximo cobro. `redirect_url` es null mientras no haya pasarela conectada.
    """
    _solo_empresa(user)
    plan = _get_plan(db, body.plan_id, solo_activos=True)
    hoy = date.today()
    s = suscripcion_de(db, cid)

    if s is None:
        s = Suscripcion(
            company_id=cid, plan_id=plan.id, estado="trial",
            trial_hasta=hoy + timedelta(days=TRIAL_DIAS),
            periodo_actual_desde=hoy, periodo_actual_hasta=sumar_mes(hoy),
        )
        db.add(s)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            raise err(409, "SUSCRIPCION_DUPLICADA",
                      "La empresa ya tiene una suscripción")
        descripcion = (f"Suscripción contratada en el plan '{plan.nombre}' "
                       f"(trial hasta {s.trial_hasta.isoformat()})")
        tipo_log = "creacion"
    else:
        if s.plan_id != plan.id:
            raise err(403, "AUTORIZACION_ADMIN_REQUERIDA",
                      "Solicite el cambio de plan para que ADMIN lo autorice")
        cambios: list[str] = []
        if s.estado == "cancelada":
            s.estado = ("trial" if s.trial_hasta and s.trial_hasta >= hoy
                        else "activa")
            # Un periodo caducado se renueva desde hoy; si no, se conserva.
            if s.periodo_actual_hasta is None or s.periodo_actual_hasta < hoy:
                s.periodo_actual_desde = hoy
                s.periodo_actual_hasta = sumar_mes(hoy)
            cambios.append(f"reactivada como '{s.estado}'")
        # Repetir la contratación del mismo plan es idempotente: se devuelve la
        # suscripción tal cual, sin registrar un cambio que no ocurrió.
        descripcion = (f"Suscripción actualizada ({'; '.join(cambios)})"
                       if cambios else None)
        tipo_log = "actualizacion"
        if cambios:
            s.updated_at = datetime.now(timezone.utc)

    if descripcion:
        actividad.log(db, cid, tipo_log, "suscripcion", descripcion,
                      user_id=user.id, entidad_tipo="suscripcion",
                      entidad_id=s.id)
        db.commit()
        logger.info("empresa %s: %s", cid, descripcion)

    # TODO(§17): iniciar aquí el flujo con la pasarela (Transbank Webpay/OneClick
    # o Stripe) cuando `requiere_accion` sea true: crear la intención de pago o la
    # inscripción OneClick, guardar el token devuelto en
    # `suscripciones.medio_pago_ref` y devolver su URL en `redirect_url` para que
    # el frontend redirija. La confirmación no llega por esta respuesta sino por
    # `POST /webhooks/pagos`, que es el único punto que marca una factura pagada.
    requiere_accion = bool(s.medio_pago_ref is None and s.estado != "trial")
    suscripcion_out = _out(s, plan)
    suscripcion_out["estado_cuenta"] = _estado_cuenta(db, cid)

    return {
        "suscripcion": suscripcion_out,
        "pago": {"requiere_accion": requiere_accion, "redirect_url": None},
    }


@router_admin_suscripciones.get("/{company_id}/solicitudes")
def admin_listar_solicitudes(company_id: uuid.UUID,
                              db: Session = Depends(get_db)):
    company = db.get(Company, company_id)
    if company is None:
        raise err(404, "NO_ENCONTRADO", "Empresa inexistente")
    solicitudes = db.scalars(
        select(SolicitudSuscripcion)
        .where(SolicitudSuscripcion.company_id == company_id)
        .order_by(
            (SolicitudSuscripcion.estado == "pendiente").desc(),
            SolicitudSuscripcion.solicitado_at.desc(),
        )
        .limit(50)
    ).all()
    return {"items": [
        _solicitud_out(db, solicitud, empresa=company.nombre)
        for solicitud in solicitudes
    ]}


@router_admin_suscripciones.get("/solicitudes")
def admin_listar_solicitudes_pendientes(
        p: Page = Depends(paginacion), db: Session = Depends(get_db)):
    consulta = (
        select(SolicitudSuscripcion, Company.nombre)
        .join(Company, Company.id == SolicitudSuscripcion.company_id)
        .where(SolicitudSuscripcion.estado == "pendiente")
    )
    total = db.scalar(
        select(func.count()).select_from(consulta.subquery())) or 0
    filas = db.execute(
        consulta.order_by(SolicitudSuscripcion.solicitado_at.desc())
        .offset(p.offset).limit(p.page_size)
    ).all()
    return sobre([
        _solicitud_out(db, solicitud, empresa=empresa)
        for solicitud, empresa in filas
    ], total, p)


@router_admin_suscripciones.patch(
        "/solicitudes/{solicitud_id}/resolver")
def admin_resolver_solicitud(
        solicitud_id: uuid.UUID,
        body: ResolverSolicitudSuscripcionIn,
        db: Session = Depends(get_db),
        admin: User = Depends(get_current_user)):
    motivo = " ".join(body.motivo.split())
    if len(motivo) < 12:
        raise err(400, "MOTIVO_REQUERIDO",
                  "Indique un motivo de al menos 12 caracteres")

    solicitud = db.scalar(
        select(SolicitudSuscripcion)
        .where(SolicitudSuscripcion.id == solicitud_id)
        .with_for_update())
    if solicitud is None:
        raise err(404, "NO_ENCONTRADO", "La solicitud no existe")
    if solicitud.estado != "pendiente":
        raise err(409, "SOLICITUD_RESUELTA",
                  "La solicitud ya fue resuelta")

    company = db.get(Company, solicitud.company_id)
    if company is None:
        raise err(404, "NO_ENCONTRADO", "Empresa inexistente")

    plan_anterior = None
    plan_nuevo = None
    suscripcion = None
    estado_cuenta_antes = (
        _estado_cuenta(db, company.id)
        if solicitud.tipo == "regularizacion" else None
    )
    if body.decision == "aprobada" and solicitud.tipo == "cambio_plan":
        suscripcion = db.scalar(
            select(Suscripcion)
            .where(Suscripcion.company_id == company.id)
            .with_for_update())
        if suscripcion is None:
            raise err(409, "SIN_SUSCRIPCION",
                      "La suscripción fue eliminada antes de resolver la solicitud")
        plan_nuevo = _get_plan(db, solicitud.plan_id, solo_activos=True)
        if suscripcion.plan_id == plan_nuevo.id:
            raise err(409, "PLAN_ACTUAL",
                      "La empresa ya tiene el plan solicitado")
        plan_anterior = db.get(Plan, suscripcion.plan_id)
        suscripcion.plan_id = plan_nuevo.id
        suscripcion.updated_at = datetime.now(timezone.utc)

    solicitud.estado = body.decision
    solicitud.resuelto_por = admin.id
    solicitud.resuelto_at = datetime.now(timezone.utc)
    solicitud.motivo_resolucion = motivo
    db.flush()

    cambios = None
    if plan_nuevo:
        cambios = {
            "plan": {
                "antes": plan_anterior.nombre if plan_anterior else None,
                "despues": plan_nuevo.nombre,
            },
        }
    estado_cuenta_despues = _estado_cuenta(db, company.id)
    if solicitud.tipo == "regularizacion":
        cambios = {
            "estado_cuenta": {
                "antes": estado_cuenta_antes,
                "despues": estado_cuenta_despues,
            },
        }
    actividad.log(
        db, company.id, "actualizacion", "suscripcion",
        f"ADMIN {body.decision} solicitud de {solicitud.tipo}",
        user_id=admin.id, entidad_tipo="solicitud_suscripcion",
        entidad_id=solicitud.id,
        metadata={
            "decision": body.decision,
            "motivo_solicitud": solicitud.motivo,
            "motivo_resolucion": motivo,
            "cambios": cambios or {},
        },
    )
    db.commit()

    salida = {
        "solicitud": _solicitud_out(db, solicitud, empresa=company.nombre),
        "estado_cuenta": estado_cuenta_despues,
    }
    if suscripcion is not None and plan_nuevo is not None:
        salida["suscripcion"] = _out(suscripcion, plan_nuevo)
    logger.info("admin %s resolvió solicitud %s (%s): %s",
                admin.id, solicitud.id, body.decision, motivo)
    return salida


@router.delete("")
def cancelar(db: Session = Depends(get_db),
             cid: uuid.UUID = Depends(get_company_id),
             user: User = Depends(require_company)):
    """Cancela al término del periodo vigente.

    No se borra la fila ni se recorta `periodo_actual_hasta`: el periodo está
    pagado y la empresa lo usa hasta el final. Después del vencimiento, la
    dependencia común de autenticación bloquea las escrituras de la empresa.
    """
    _solo_empresa(user)
    s = suscripcion_de(db, cid)
    if s is None:
        raise err(404, "SIN_SUSCRIPCION", "La empresa no tiene una suscripción")
    if s.estado == "cancelada":
        raise err(409, "SUSCRIPCION_CANCELADA",
                  "La suscripción ya está cancelada")
    if s.periodo_actual_hasta is None:
        raise err(409, "PERIODO_SIN_FECHA",
                  "No se puede programar la cancelación sin una fecha de fin "
                  "del periodo vigente")

    s.estado = "cancelada"
    s.updated_at = datetime.now(timezone.utc)
    actividad.log(db, cid, "actualizacion", "suscripcion",
                  f"Suscripción cancelada; el servicio continúa hasta "
                  f"{_fecha(s.periodo_actual_hasta) or 'el fin del periodo'}",
                  user_id=user.id, entidad_tipo="suscripcion", entidad_id=s.id)
    db.commit()

    salida = _out(s, db.get(Plan, s.plan_id))
    salida["vigente_hasta"] = _fecha(s.periodo_actual_hasta)
    return salida


# =============================================================================
# §17 — Facturas
# =============================================================================
@router_facturas.get("")
def listar_facturas(estado: str | None = Query(None),
                    desde: date | None = Query(None),
                    hasta: date | None = Query(None),
                    p: Page = Depends(paginacion), db: Session = Depends(get_db),
                    cid: uuid.UUID = Depends(get_company_id),
                    user: User = Depends(get_current_user)):
    """Historial de facturas de la empresa, la más reciente primero.

    `desde`/`hasta` filtran por fecha de emisión y `hasta` es inclusivo.
    """
    _solo_empresa(user)
    if estado and estado not in ESTADOS_FACTURA:
        raise err(400, "ESTADO_INVALIDO",
                  f"Estado debe ser uno de: {', '.join(ESTADOS_FACTURA)}")
    if desde and hasta and hasta < desde:
        raise err(400, "RANGO_INVALIDO", "'hasta' no puede ser anterior a 'desde'")

    q = select(Factura).where(Factura.company_id == cid)
    if estado:
        q = q.where(Factura.estado == estado)
    if desde:
        q = q.where(Factura.emitida_at >= datetime.combine(
            desde, datetime.min.time(), tzinfo=timezone.utc))
    if hasta:
        q = q.where(Factura.emitida_at < datetime.combine(
            hasta + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc))
    if p.search:
        q = q.where(Factura.folio.ilike(f"%{p.search}%"))

    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = aplicar_orden(q, Factura, p.sort, ORDEN_FACTURAS, "-emitida_at")
    filas = list(db.scalars(q.offset(p.offset).limit(p.page_size)))

    salida = sobre([_factura_out(f) for f in filas], total, p)
    salida["totales"] = {
        "pendiente": float(db.scalar(
            select(func.coalesce(func.sum(Factura.monto), 0)).where(
                Factura.company_id == cid, Factura.estado == "pendiente")) or 0),
        "pagado": float(db.scalar(
            select(func.coalesce(func.sum(Factura.monto), 0)).where(
                Factura.company_id == cid, Factura.estado == "pagada")) or 0),
    }
    return salida


@router_facturas.get("/{factura_id}/download-url")
def download_url(factura_id: uuid.UUID, db: Session = Depends(get_db),
                 cid: uuid.UUID = Depends(get_company_id),
                 user: User = Depends(get_current_user)):
    """SAS de lectura del PDF de la factura.

    409 si todavía no hay PDF: la factura existe pero el documento lo emite el
    proceso de facturación, y una URL firmada contra un blob ausente daría un
    404 opaco en el navegador.
    """
    _solo_empresa(user)
    f = db.get(Factura, factura_id)
    if not f or f.company_id != cid:
        raise err(404, "NO_ENCONTRADO", "La factura no existe")
    if not f.pdf_blob_path:
        raise err(409, "FACTURA_SIN_PDF",
                  "La factura todavía no tiene documento asociado")

    filename = f"factura-{f.folio or str(f.id)[:8]}.pdf"
    dl = get_storage().download_url(f.pdf_blob_path, filename)
    return {"download_url": dl.download_url,
            "expires_at": dl.expires_at.isoformat(), "filename": filename}


# =============================================================================
# §17 — Administración del catálogo (solo admin)
# =============================================================================
# `planes` es un catálogo global sin `company_id`, así que estas mutaciones no
# escriben en `actividad`: esa tabla exige `company_id NOT NULL` y no hay empresa
# a la que atribuirlas. Quedan en el log de la aplicación.
@router_admin.get("")
def admin_listar(activo: bool | None = Query(None),
                 p: Page = Depends(paginacion), db: Session = Depends(get_db)):
    """Catálogo completo, incluidos los planes retirados (`activo=false`)."""
    q = select(Plan)
    if activo is not None:
        q = q.where(Plan.activo.is_(activo))
    if p.search:
        q = q.where(Plan.nombre.ilike(f"%{p.search}%"))
    total = db.scalar(select(func.count()).select_from(q.subquery())) or 0
    q = aplicar_orden(q, Plan, p.sort, ORDEN_PLANES, "precio")
    filas = list(db.scalars(q.offset(p.offset).limit(p.page_size)))
    return sobre([_plan_out(x) for x in filas], total, p)


@router_admin.post("", status_code=201)
def admin_crear(body: PlanIn, db: Session = Depends(get_db)):
    """Crea un plan comercial. `nombre` es único en la tabla."""
    nombre = (body.nombre or "").strip()
    if not nombre:
        raise err(400, "NOMBRE_REQUERIDO", "El nombre del plan es obligatorio")
    _valida_precio(body.precio)
    _valida_periodo(body.periodo)

    p = Plan(nombre=nombre, precio=body.precio, moneda=body.moneda,
             periodo=body.periodo, limites=body.limites or {},
             activo=body.activo)
    db.add(p)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise err(409, "PLAN_DUPLICADO", "Ya existe un plan con ese nombre")
    db.commit()
    logger.info("plan '%s' creado (%s %s/%s)", p.nombre, p.precio, p.moneda,
                p.periodo)
    return _plan_out(p)


@router_admin.patch("/{plan_id}")
def admin_editar(plan_id: uuid.UUID, body: PlanPatch,
                 db: Session = Depends(get_db)):
    """Edita o desactiva un plan.

    Desactivar (`activo=false`) lo retira del catálogo público pero **no** afecta
    a las suscripciones que ya lo tienen: la FK es `ON DELETE RESTRICT` y el plan
    sigue existiendo precisamente para que esas suscripciones se sostengan.
    """
    p = db.get(Plan, plan_id)
    if p is None:
        raise err(404, "NO_ENCONTRADO", "El plan no existe")
    data = body.model_dump(exclude_unset=True)
    if not data:
        raise err(400, "SIN_CAMBIOS", "No se indicó ningún campo a actualizar")

    if "nombre" in data:
        nombre = (data["nombre"] or "").strip()
        if not nombre:
            raise err(400, "NOMBRE_REQUERIDO", "El nombre no puede estar vacío")
        p.nombre = nombre
    if data.get("precio") is not None:
        p.precio = _valida_precio(data["precio"])
    if data.get("moneda"):
        p.moneda = data["moneda"]
    if data.get("periodo"):
        p.periodo = _valida_periodo(data["periodo"])
    if data.get("limites") is not None:
        p.limites = data["limites"]
    if data.get("activo") is not None:
        p.activo = data["activo"]
    p.updated_at = datetime.now(timezone.utc)

    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise err(409, "PLAN_DUPLICADO", "Ya existe un plan con ese nombre")
    db.commit()

    salida = _plan_out(p)
    salida["suscripciones"] = db.scalar(
        select(func.count(Suscripcion.id)).where(
            Suscripcion.plan_id == p.id)) or 0
    return salida
