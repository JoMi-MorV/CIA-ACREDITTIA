"""Exportaciones explícitas y auditables de información de la consola ADMIN."""
from __future__ import annotations

import csv
import html
import json
import tempfile
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID
from zoneinfo import ZoneInfo
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.platypus import (PageBreak, Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..models import (Actividad, AdminAccessGrant, Base, Company, Contrato,
                      Documento, IaReview, Plan, Sujeto, Suscripcion, User)
from ..models_ops import (MetricasMensuales, OpsComponente,
                          MetricasMensualesPlan, OpsDisponibilidadDiaria,
                          OpsIncidente, OpsJob, OpsJobRun)
from .actividad import minimizar_metadata, minimizar_texto

# No se incluyen tablas de documentos/archivos, hashes de credenciales, tokens,
# secretos ni el vault. Las columnas sensibles se excluyen por nombre.
_TABLES = (
    "companies", "users", "contratos", "planes", "suscripciones", "actividad",
    "metricas_mensuales", "metricas_mensuales_plan", "ops_componentes",
    "ops_disponibilidad_diaria", "ops_incidentes", "ops_jobs", "ops_job_runs",
)
_EXCLUDED_COLUMNS = {
    "users": {"password_hash", "auth_version"},
    "ops_job_runs": {"error_detalle", "celery_task_id"},
}
_SENSITIVE_NAMES = ("password", "token", "secret", "credential", "jwe", "private_key")


def _json_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (Decimal, UUID)):
        return str(value)
    if isinstance(value, bytes):
        return "[contenido binario omitido]"
    return value


def _tables():
    for name in _TABLES:
        table = Base.metadata.tables.get(name)
        if table is None:
            continue
        columns = [
            column for column in table.columns
            if column.name not in _EXCLUDED_COLUMNS.get(name, set())
            and not any(part in column.name.lower() for part in _SENSITIVE_NAMES)
        ]
        if columns:
            yield table, columns


def create_console_export(
    db: Session, formato: str,
    user_grant: AdminAccessGrant | None = None,
) -> tuple[Path, str, tempfile.TemporaryDirectory]:
    """Genera un ZIP CSV+JSON o PDF de resumen; caller elimina el temporal."""
    tmp = tempfile.TemporaryDirectory(prefix="acredittia-admin-export-")
    root = Path(tmp.name)
    generated = datetime.now(ZoneInfo("America/Santiago"))
    try:
        if formato == "pdf":
            path = root / "exportacion-admin.pdf"
            _create_pdf(db, path, generated)
            return path, "application/pdf", tmp
        if formato != "zip":
            raise ValueError("Formato de exportación no soportado")

        zip_path = root / "exportacion-admin.zip"
        manifest = {
            "generado_at": generated.isoformat(),
            "alcance": "datos visibles de la consola ADMIN; sin archivos documentales, credenciales ni tokens",
            "alcance_usuarios": ({
                "company_id": str(user_grant.company_id) if user_grant.company_id else None,
                "recurso_id": str(user_grant.recurso_id) if user_grant.recurso_id else None,
            } if user_grant else None),
            "contenido": [],
        }
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED) as package:
            for table, columns in _tables():
                csv_path = root / f"{table.name}.csv"
                json_path = root / f"{table.name}.json"
                count = 0
                with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file, \
                        json_path.open("w", encoding="utf-8") as json_file:
                    writer = csv.writer(csv_file)
                    writer.writerow([column.name for column in columns])
                    json_file.write("[")
                    query = select(*columns).select_from(table)
                    if table.name == "users":
                        if user_grant is None:
                            raise ValueError(
                                "La exportación ZIP requiere concesión vigente de usuarios")
                        if user_grant.company_id is not None:
                            query = query.where(User.company_id == user_grant.company_id)
                        if user_grant.recurso_id is not None:
                            query = query.where(User.id == user_grant.recurso_id)
                    elif table.name == "actividad" and user_grant is not None:
                        if user_grant.company_id is not None:
                            query = query.where(
                                Actividad.company_id == user_grant.company_id)
                        if user_grant.recurso_id is not None:
                            query = query.where(
                                Actividad.user_id == user_grant.recurso_id)
                    for row in db.execute(query).mappings():
                        values = {}
                        for column in columns:
                            value = _json_value(row[column.name])
                            if table.name == "actividad":
                                if column.name == "metadata":
                                    value = minimizar_metadata(value)
                                elif isinstance(value, str):
                                    value = minimizar_texto(value)
                            values[column.name] = value
                        writer.writerow([_csv_value(values[column.name]) for column in columns])
                        if count:
                            json_file.write(",")
                        json.dump(values, json_file, ensure_ascii=False, default=str)
                        count += 1
                    json_file.write("]")
                package.write(csv_path, f"csv/{table.name}.csv")
                package.write(json_path, f"json/{table.name}.json")
                manifest["contenido"].append({"tabla": table.name, "filas": count})
            package.writestr("manifest.json",
                             json.dumps(manifest, ensure_ascii=False, indent=2))
        return zip_path, "application/zip", tmp
    except Exception:
        tmp.cleanup()
        raise


def _csv_value(value):
    if isinstance(value, str):
        first = value.lstrip(" \t\r\n")
        if first.startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def _create_pdf(db: Session, path: Path, generated: datetime) -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="ReportSection", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=14, leading=17, textColor=colors.HexColor("#153052"),
        spaceBefore=4, spaceAfter=8))
    styles.add(ParagraphStyle(
        name="ReportSubsection", parent=styles["Heading3"],
        fontName="Helvetica-Bold", fontSize=10, leading=13,
        textColor=colors.HexColor("#315477"), spaceBefore=5, spaceAfter=5))
    styles.add(ParagraphStyle(
        name="ReportCell", parent=styles["BodyText"], fontName="Helvetica",
        fontSize=7.5, leading=9))
    styles.add(ParagraphStyle(
        name="ReportHeaderCell", parent=styles["ReportCell"],
        fontName="Helvetica-Bold", textColor=colors.white))
    styles.add(ParagraphStyle(
        name="ReportKpi", parent=styles["BodyText"], alignment=1,
        fontName="Helvetica-Bold", fontSize=13, leading=16,
        textColor=colors.HexColor("#153052")))
    styles.add(ParagraphStyle(
        name="ReportKpiLabel", parent=styles["BodyText"], alignment=1,
        fontSize=7.5, leading=9, textColor=colors.HexColor("#52657A")))
    document = SimpleDocTemplate(
        str(path), pagesize=landscape(A4), rightMargin=15 * mm,
        leftMargin=15 * mm, topMargin=15 * mm, bottomMargin=17 * mm)
    generated_label = generated.isoformat(timespec="seconds")
    document.title = "Reporte integral de consola ADMIN"
    document.author = "Acredittia"
    document.subject = f"Generated at {generated_label}"
    document.creator = "Acredittia ADMIN"

    def count(model, *conditions) -> int:
        statement = select(func.count()).select_from(model)
        if conditions:
            statement = statement.where(*conditions)
        return int(db.scalar(statement) or 0)

    def grouped(column, model, *conditions):
        statement = select(column, func.count()).select_from(model)
        if conditions:
            statement = statement.where(*conditions)
        return dict(db.execute(statement.group_by(column)).all())

    def n(value) -> str:
        return f"{int(value or 0):,}".replace(",", ".")

    def clp(value) -> str:
        return f"${int(round(float(value or 0))):,}".replace(",", ".")

    def pct(value) -> str:
        return "—" if value is None else f"{float(value):.1f}%".replace(".", ",")

    def safe_text(value) -> str:
        return html.escape(str(value if value is not None else "—"))

    def report_table(rows, widths=None, repeat_rows=1):
        data = []
        for row_index, row in enumerate(rows):
            style = styles["ReportHeaderCell"] if row_index < repeat_rows else styles["ReportCell"]
            data.append([Paragraph(safe_text(cell), style) for cell in row])
        table = Table(data, colWidths=widths, repeatRows=repeat_rows,
                      hAlign="LEFT", splitByRow=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, repeat_rows - 1), colors.HexColor("#153052")),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("ROWBACKGROUNDS", (0, repeat_rows), (-1, -1),
             [colors.white, colors.HexColor("#F3F6FA")]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return table

    def bar_chart(title, labels, values, width=760, height=205):
        if not labels:
            return Paragraph(f"{safe_text(title)}: sin datos disponibles.", styles["ReportCell"])
        drawing = Drawing(width, height)
        drawing.add(String(2, height - 14, title, fontName="Helvetica-Bold",
                           fontSize=10, fillColor=colors.HexColor("#153052")))
        chart = VerticalBarChart()
        chart.x, chart.y = 42, 42
        chart.width, chart.height = width - 58, height - 72
        chart.data = [list(values)]
        chart.categoryAxis.categoryNames = list(labels)
        chart.categoryAxis.labels.fontName = "Helvetica"
        chart.categoryAxis.labels.fontSize = 7
        chart.categoryAxis.labels.angle = 25
        chart.categoryAxis.labels.dx = -2
        chart.categoryAxis.labels.dy = -2
        chart.valueAxis.valueMin = 0
        maximum = max((float(value or 0) for value in values), default=0)
        chart.valueAxis.valueMax = maximum * 1.15 if maximum else 1
        chart.valueAxis.valueStep = (maximum / 4) if maximum else 1
        chart.valueAxis.labels.fontSize = 7
        chart.valueAxis.labelTextFormat = "%0.0f"
        chart.bars[0].fillColor = colors.HexColor("#B56E43")
        chart.bars[0].strokeColor = colors.HexColor("#8F4F2D")
        chart.barSpacing = 3
        chart.groupSpacing = 7
        drawing.add(chart)
        return drawing

    def draw_page(canvas, doc):
        canvas.saveState()
        page_width, page_height = landscape(A4)
        canvas.setStrokeColor(colors.HexColor("#CBD5E1"))
        canvas.line(15 * mm, 12 * mm, page_width - 15 * mm, 12 * mm)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#52657A"))
        canvas.drawString(15 * mm, 7 * mm, f"Confidencial · Generado {generated_label}")
        canvas.drawRightString(page_width - 15 * mm, 7 * mm, f"Página {doc.page}")
        canvas.restoreState()

    now = generated
    today = now.date()
    month_start = today.replace(day=1)
    monthly_from = (month_start.replace(day=1) - timedelta(days=335)).replace(day=1)
    companies_total = count(Company)
    companies_demo = count(Company, Company.es_demo.is_(True))
    companies_status = grouped(Company.status, Company)
    industries = grouped(Company.industria, Company,
                         Company.status == "approved")
    industry_users = dict(db.execute(
        select(Company.industria, func.count(User.id))
        .select_from(Company)
        .outerjoin(User, (User.company_id == Company.id)
                   & (User.role != "admin") & (User.status == "approved")
                   & User.activo.is_(True))
        .where(Company.status == "approved")
        .group_by(Company.industria)).all())
    users_total = count(User)
    users_active = count(User, User.activo.is_(True), User.status == "approved")
    users_groups = db.execute(
        select(User.role, User.status, User.activo, func.count())
        .group_by(User.role, User.status, User.activo)
        .order_by(User.role, User.status, User.activo)).all()
    contracts_total = count(Contrato)
    contracts_status = grouped(Contrato.estado, Contrato)
    subscriptions_total = count(Suscripcion)
    subscription_states = grouped(Suscripcion.estado, Suscripcion)
    plan_states = db.execute(
        select(Plan.nombre, Suscripcion.estado, func.count())
        .join(Suscripcion, Suscripcion.plan_id == Plan.id)
        .group_by(Plan.nombre, Suscripcion.estado)
        .order_by(Plan.nombre, Suscripcion.estado)).all()
    document_states = dict(db.execute(
        select(Documento.estado_calc, func.count())
        .where(Documento.obligatorio.is_(True),
               Documento.es_emsipor.is_(False))
        .group_by(Documento.estado_calc)).all())
    document_totals = sum(document_states.values())
    document_ok = int(document_states.get("ok", 0))
    compliance_rows = db.execute(
        select(
            Company.nombre,
            func.count(Documento.id).label("total"),
            func.count(Documento.id).filter(
                Documento.estado_calc == "ok").label("ok"),
        )
        .join(Documento, Documento.company_id == Company.id)
        .where(Company.status == "approved",
               Documento.obligatorio.is_(True),
               Documento.es_emsipor.is_(False))
        .group_by(Company.id, Company.nombre)).all()
    compliance_by_company = [
        (name, int(ok), int(total), round(100 * int(ok) / int(total)))
        for name, total, ok in compliance_rows if total
    ]
    all_compliance_risks = sorted(
        (row for row in compliance_by_company if row[3] < 70),
        key=lambda row: (row[3], row[0]))[:20]
    compliance_risk_count = sum(1 for row in compliance_by_company if row[3] < 70)
    compliance_average = (
        sum(row[3] for row in compliance_by_company) / len(compliance_by_company)
        if compliance_by_company else None)
    weighted_compliance = (
        100 * document_ok / document_totals if document_totals else None)
    subject_types = grouped(Sujeto.tipo, Sujeto)
    ai_statuses = grouped(IaReview.status, IaReview)
    account_health = dict(db.execute(text("""
        SELECT ops_estado_cuenta(c.id), count(*)
          FROM companies c
         WHERE c.status = 'approved'
         GROUP BY 1
    """)).all())
    usage_rows = db.execute(text(
        "SELECT usuarios, activos, sin_acceso_90d "
        "FROM ops_usuarios_por_empresa(30)")).all()
    usage_risks = {
        "sin_usuarios": sum(1 for row in usage_rows if row.usuarios == 0),
        "sin_actividad_30d": sum(
            1 for row in usage_rows if row.usuarios > 0 and row.activos == 0),
        "baja_actividad_30d": sum(
            1 for row in usage_rows if row.usuarios > 0 and row.activos > 0
            and row.activos * 2 < row.usuarios),
        "sin_acceso_90d": sum(int(row.sin_acceso_90d or 0) for row in usage_rows),
    }

    metric_rows = list(db.scalars(
        select(MetricasMensuales)
        .where(MetricasMensuales.mes >= monthly_from)
        .order_by(MetricasMensuales.mes)))
    latest_metric = metric_rows[-1] if metric_rows else None
    latest_plan_metrics = []
    if latest_metric:
        latest_plan_metrics = db.execute(
            select(MetricasMensualesPlan, Plan.nombre)
            .join(Plan, Plan.id == MetricasMensualesPlan.plan_id)
            .where(MetricasMensualesPlan.mes == latest_metric.mes)
            .order_by(Plan.nombre)).all()
    month_labels = [row.mes.strftime("%m/%y") for row in metric_rows]
    mrr_values = [float(row.mrr_clp or 0) for row in metric_rows]
    churn_values = [float(row.churn_clientes_pct or 0) for row in metric_rows]
    client_values = [int(row.clientes_activos or 0) for row in metric_rows]

    availability_from = today - timedelta(days=89)
    availability_rows = db.execute(
        select(
            OpsDisponibilidadDiaria.componente,
            func.avg(OpsDisponibilidadDiaria.uptime_pct),
            func.max(OpsDisponibilidadDiaria.latencia_p95_ms),
            func.sum(OpsDisponibilidadDiaria.checks_total),
            func.sum(OpsDisponibilidadDiaria.checks_fallidos),
            func.max(OpsDisponibilidadDiaria.fecha),
        )
        .where(OpsDisponibilidadDiaria.fecha >= availability_from,
               OpsDisponibilidadDiaria.fecha <= today)
        .group_by(OpsDisponibilidadDiaria.componente)).all()
    availability = {row[0]: row[1:] for row in availability_rows}
    components = list(db.scalars(
        select(OpsComponente).where(OpsComponente.activo)
        .order_by(OpsComponente.orden)))
    component_rows = []
    for component in components:
        aggregate = availability.get(component.clave)
        latest = db.scalars(
            select(OpsDisponibilidadDiaria)
            .where(OpsDisponibilidadDiaria.componente == component.clave)
            .order_by(OpsDisponibilidadDiaria.fecha.desc()).limit(1)).first()
        component_rows.append((
            component.nombre, latest.estado if latest else "sin medición",
            float(aggregate[0]) if aggregate and aggregate[0] is not None else None,
            aggregate[1] if aggregate else None,
            int(aggregate[2] or 0) if aggregate else 0,
            int(aggregate[3] or 0) if aggregate else 0,
            aggregate[4].isoformat() if aggregate and aggregate[4] else "—",
        ))

    active_jobs = list(db.scalars(select(OpsJob).order_by(OpsJob.clave)))
    runs_from = now - timedelta(days=30)
    run_status_counts = dict(db.execute(
        select(OpsJobRun.status, func.count())
        .where(OpsJobRun.created_at >= runs_from)
        .group_by(OpsJobRun.status)).all())
    job_rows = []
    for job in active_jobs:
        last_run = db.scalars(
            select(OpsJobRun).where(OpsJobRun.job_clave == job.clave)
            .order_by(OpsJobRun.created_at.desc(), OpsJobRun.id.desc())
            .limit(1)).first()
        runs_7d = db.execute(
            select(OpsJobRun.status, func.count())
            .where(OpsJobRun.job_clave == job.clave,
                   OpsJobRun.created_at >= now - timedelta(days=7))
            .group_by(OpsJobRun.status)).all()
        statuses = dict(runs_7d)
        completed = sum(statuses.get(status, 0) for status in ("ok", "error", "timeout"))
        success_pct = (100 * statuses.get("ok", 0) / completed) if completed else None
        last_at = (last_run.finished_at or last_run.started_at or last_run.created_at) \
            if last_run else None
        job_rows.append((
            job.nombre, "Activo" if job.activo else "Pausado",
            job.cron_expr or job.tipo,
            last_run.status if last_run else "sin ejecuciones",
            last_at.astimezone(generated.tzinfo).isoformat(timespec="minutes")
            if last_at else "—",
            pct(success_pct), n(sum(statuses.values())),
        ))

    incident_from = now - timedelta(days=90)
    incident_count = count(OpsIncidente, OpsIncidente.abierto_at >= incident_from)
    open_incidents = count(OpsIncidente, OpsIncidente.estado != "resuelto")
    incidents = list(db.scalars(
        select(OpsIncidente).where(OpsIncidente.abierto_at >= incident_from)
        .order_by(OpsIncidente.abierto_at.desc()).limit(30)))
    incident_component_names = {
        component.clave: component.nombre for component in components
    }

    activity_from = now - timedelta(days=30)
    activity_total = count(Actividad, Actividad.created_at >= activity_from)
    activity_types = db.execute(
        select(Actividad.tipo, func.count())
        .where(Actividad.created_at >= activity_from)
        .group_by(Actividad.tipo).order_by(func.count().desc())).all()
    activity_modules = db.execute(
        select(Actividad.modulo, func.count())
        .where(Actividad.created_at >= activity_from)
        .group_by(Actividad.modulo).order_by(func.count().desc()).limit(12)).all()

    counts = []
    for table, _ in _tables():
        counts.append([table.name, n(db.scalar(select(func.count()).select_from(table)))])

    def kpi(value, label):
        return [Paragraph(safe_text(value), styles["ReportKpi"]),
                Paragraph(safe_text(label), styles["ReportKpiLabel"])]

    kpis = [
        kpi(n(companies_total), f"Empresas · {n(companies_demo)} demo"),
        kpi(n(users_total), f"Usuarios · {n(users_active)} activos"),
        kpi(n(subscriptions_total), "Suscripciones"),
        kpi(n(contracts_total), "Contratos"),
        kpi(clp(latest_metric.mrr_clp) if latest_metric else "—", "MRR último período"),
        kpi(n(latest_metric.clientes_activos) if latest_metric else "—",
            "Clientes activos (último período)"),
        kpi(pct(latest_metric.churn_clientes_pct) if latest_metric else "—",
            "Churn de clientes"),
        kpi(f"{n(len(components))} / {n(open_incidents)}",
            "Servicios monitoreados / incidentes abiertos"),
    ]
    kpi_data = [
        [kpis[index][0] for index in range(4)],
        [kpis[index][1] for index in range(4)],
        [kpis[index][0] for index in range(4, 8)],
        [kpis[index][1] for index in range(4, 8)],
    ]
    kpi_table = Table(kpi_data, colWidths=[(landscape(A4)[0] - 30 * mm) / 4] * 4)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F3F6FA")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D7E0EA")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    story = [
        Paragraph("Reporte integral de consola ADMIN", styles["Title"]),
        Paragraph(f"Fecha y hora exacta de generación: {safe_text(generated_label)}",
                  styles["Heading3"]),
        Paragraph(
            "Informe visual construido desde los datos disponibles en la base al momento "
            "de la solicitud. Incluye series y gráficos vectoriales; no es una captura "
            "estática de la interfaz. Uso confidencial para administración.",
            styles["BodyText"]),
        Spacer(1, 5 * mm),
        kpi_table,
        Spacer(1, 4 * mm),
        Paragraph(
            f"Los indicadores incluyen {n(companies_demo)} empresa(s) de demostración. "
            "Los datos operativos reflejan las ventanas de tiempo indicadas en cada sección.",
            styles["ReportCell"]),
        Paragraph("Empresas y suscripciones", styles["ReportSection"]),
        bar_chart("Empresas por estado", list(companies_status),
                  [companies_status[key] for key in companies_status]),
        bar_chart("Suscripciones por estado", list(subscription_states),
                  [subscription_states[key] for key in subscription_states]),
        PageBreak(),
        Paragraph("Indicadores de negocio", styles["ReportSection"]),
        Paragraph(
            "Serie de snapshots mensuales disponibles en los últimos 12 meses. "
            "El mes en curso puede ser parcial; se identifica en la tabla.",
            styles["ReportCell"]),
        Spacer(1, 2 * mm),
        bar_chart("MRR mensual (CLP)", month_labels, mrr_values),
        bar_chart("Clientes activos por mes", month_labels, client_values),
        bar_chart("Churn de clientes por mes (%)", month_labels, churn_values),
        Spacer(1, 2 * mm),
        Paragraph("Detalle mensual", styles["ReportSubsection"]),
    ]
    if latest_metric:
        previous_metric = metric_rows[-2] if len(metric_rows) > 1 else None
        variation = None
        if previous_metric and float(previous_metric.mrr_clp or 0):
            variation = 100 * (
                float(latest_metric.mrr_clp) - float(previous_metric.mrr_clp)
            ) / float(previous_metric.mrr_clp)
        story.extend([
            report_table([
                ["Indicador del último período disponible", "Valor"],
                ["Mes y carácter del dato",
                 f"{latest_metric.mes.isoformat()[:7]} · "
                 + ("parcial" if latest_metric.mes == month_start
                    and not latest_metric.cerrado else "snapshot")],
                ["ARR anualizado", clp(float(latest_metric.mrr_clp) * 12)],
                ["Variación MRR respecto al período anterior", pct(variation)],
                ["Churn de ingresos", pct(latest_metric.churn_ingresos_pct)],
                ["NRR", pct(latest_metric.nrr_pct)],
                ["Valor UF", f"{float(latest_metric.valor_uf):,.2f}"
                 .replace(",", "X").replace(".", ",").replace("X", ".")],
            ]),
            Paragraph("Desglose de MRR por plan", styles["ReportSubsection"]),
            report_table([["Plan", "Clientes", "Usuarios", "MRR CLP",
                           "Churn clientes", "NRR"], *[
                [plan, n(row.clientes), n(row.usuarios), clp(row.mrr_clp),
                 pct(row.churn_clientes_pct), pct(row.nrr_pct)]
                for row, plan in latest_plan_metrics
            ]]),
        ])
    monthly_table = [["Mes", "MRR CLP", "Clientes", "Altas", "Bajas",
                      "Churn clientes", "Churn ingresos", "NRR", "Usuarios activos/total",
                      "UF", "Estado"]]
    monthly_table.extend([
        [
            row.mes.isoformat()[:7], clp(row.mrr_clp), n(row.clientes_activos),
            n(row.altas), n(row.bajas), pct(row.churn_clientes_pct),
            pct(row.churn_ingresos_pct), pct(row.nrr_pct),
            f"{n(row.usuarios_activos)}/{n(row.usuarios_totales)}",
            f"{float(row.valor_uf):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
            "Cerrado" if row.cerrado else ("Parcial" if row.mes == month_start else "Snapshot"),
        ] for row in metric_rows
    ])
    story.append(report_table(monthly_table))

    story.extend([
        PageBreak(),
        Paragraph("Dashboard global y salud de clientes", styles["ReportSection"]),
        Paragraph(
            "Resumen transversal de acreditación, cuentas, uso reciente y "
            "revisiones IA. El cumplimiento global pondera por documentos; el "
            "promedio por empresa da el mismo peso a cada empresa con documentos. "
            "Empresas sin documentos evaluables no se consideran en esos porcentajes.",
            styles["ReportCell"]),
        report_table([
            ["Indicador del dashboard", "Resultado"],
            ["Documentos obligatorios evaluables", n(document_totals)],
            ["Documentos al día", f"{n(document_ok)} ({pct(weighted_compliance)})"],
            ["Cumplimiento promedio simple por empresa", pct(compliance_average)],
            ["Empresas bajo 70% de cumplimiento", n(compliance_risk_count)],
            ["Empresas aprobadas sin usuarios activos", n(usage_risks["sin_usuarios"])],
            ["Empresas con usuarios pero sin actividad 30d", n(usage_risks["sin_actividad_30d"])],
            ["Empresas con actividad menor al 50% (30d)", n(usage_risks["baja_actividad_30d"])],
            ["Usuarios sin acceso 90d", n(usage_risks["sin_acceso_90d"])],
        ]),
        bar_chart("Documentos requeridos por estado",
                  sorted(document_states),
                  [document_states[key] for key in sorted(document_states)]),
        bar_chart("Empresas aprobadas por estado de cuenta",
                  sorted(account_health),
                  [account_health[key] for key in sorted(account_health)]),
        bar_chart("Usuarios habilitados por industria",
                  [str(key or "sin industria") for key in industry_users],
                  [industry_users[key] for key in industry_users]),
        bar_chart("Revisiones IA por estado",
                  sorted(ai_statuses),
                  [ai_statuses[key] for key in sorted(ai_statuses)]),
        Paragraph("Empresas con cumplimiento bajo 70%", styles["ReportSubsection"]),
        report_table([["Empresa", "Documentos al día", "Evaluables", "Cumplimiento"], *[
            [name, n(ok), n(total), pct(percent)]
            for name, ok, total, percent in all_compliance_risks
        ]]),
        Paragraph(
            f"Sujetos registrados: {n(sum(subject_types.values()))} · "
            + " · ".join(f"{safe_text(kind)}: {n(total)}"
                         for kind, total in sorted(subject_types.items())),
            styles["ReportCell"]),
        PageBreak(),
        Paragraph("Clientes, usuarios y contratos", styles["ReportSection"]),
        bar_chart("Empresas aprobadas por industria", list(industries),
                  [industries[key] for key in industries]),
        Paragraph("Estado de empresas", styles["ReportSubsection"]),
        report_table([["Estado", "Empresas"], *[
            [key, n(value)] for key, value in sorted(companies_status.items())
        ]]),
        Paragraph("Usuarios por rol, estado y habilitación", styles["ReportSubsection"]),
        report_table([["Rol", "Estado", "Cuenta", "Usuarios"], *[
            [role, status, "Activa" if active else "Deshabilitada", n(total)]
            for role, status, active, total in users_groups
        ]]),
        Paragraph("Suscripciones por plan y estado", styles["ReportSubsection"]),
        report_table([["Plan", "Estado", "Suscripciones"], *[
            [plan, state, n(total)] for plan, state, total in plan_states
        ]]),
        Paragraph("Contratos por estado", styles["ReportSubsection"]),
        report_table([["Estado", "Contratos"], *[
            [key, n(value)] for key, value in sorted(contracts_status.items())
        ]]),
        PageBreak(),
        Paragraph("Salud operativa y disponibilidad", styles["ReportSection"]),
        Paragraph(
            "Disponibilidad calculada como promedio de snapshots diarios de los últimos "
            "90 días hasta la fecha de generación. La latencia corresponde al mayor "
            "p95 diario observado en esa ventana.",
            styles["ReportCell"]),
        bar_chart("Disponibilidad promedio por componente (90 días)",
                  [row[0] for row in component_rows],
                  [row[2] or 0 for row in component_rows]),
        report_table([["Componente", "Último estado", "Uptime promedio", "P95 máx. ms",
                       "Checks", "Fallidos", "Último día"], *[
            [name, state, pct(uptime), n(p95) if p95 is not None else "—",
             n(checks), n(failed), last_day]
            for name, state, uptime, p95, checks, failed, last_day in component_rows
        ]]),
        Spacer(1, 3 * mm),
        Paragraph(
            f"Incidentes abiertos actualmente: {n(open_incidents)}. "
            f"Incidentes abiertos durante los últimos 90 días: {n(incident_count)}. "
            "Se muestran hasta 30 eventos recientes.",
            styles["ReportCell"]),
        Paragraph("Incidentes recientes", styles["ReportSubsection"]),
        report_table([["Fecha/hora", "Componente", "Severidad", "Estado", "Título"], *[
            [
                incident.abierto_at.astimezone(generated.tzinfo).isoformat(timespec="minutes"),
                incident_component_names.get(incident.componente, incident.componente),
                incident.severidad, incident.estado, (incident.titulo or "")[:140],
            ] for incident in incidents
        ]]),
        PageBreak(),
        Paragraph("Procesos programados", styles["ReportSection"]),
        Paragraph(
            "Tasa de éxito y volumen calculados sobre las últimas 7 jornadas; "
            "los estados de ejecuciones se agrupan en los últimos 30 días.",
            styles["ReportCell"]),
        bar_chart("Ejecuciones por estado (30 días)", list(run_status_counts),
                  [run_status_counts[key] for key in run_status_counts]),
        report_table([["Proceso", "Programación", "Cron/tipo", "Último estado",
                       "Última ejecución", "Éxito 7d", "Ejecuciones 7d"], *[
            [name, active, cron, last_status, last_at, success, runs]
            for name, active, cron, last_status, last_at, success, runs in job_rows
        ]]),
        PageBreak(),
        Paragraph("Actividad de la consola", styles["ReportSection"]),
        Paragraph(
            f"Se registraron {n(activity_total)} eventos durante los últimos 30 días. "
            "El reporte presenta agregados por categoría y módulo, sin copiar "
            "descripciones libres ni datos de credenciales.",
            styles["ReportCell"]),
        bar_chart("Eventos por módulo (30 días)",
                  [str(module)[:22] for module, _ in activity_modules],
                  [total for _, total in activity_modules]),
        Paragraph("Eventos por tipo", styles["ReportSubsection"]),
        report_table([["Tipo de actividad", "Eventos"], *[
            [kind, n(total)] for kind, total in activity_types
        ]]),
        Paragraph("Inventario de conjuntos exportables", styles["ReportSubsection"]),
        report_table([["Conjunto de datos", "Registros"], *counts]),
        Spacer(1, 3 * mm),
        Paragraph(
            "Alcance y privacidad: este PDF no incluye archivos documentales, "
            "credenciales, tokens ni secretos. Para descargar los registros tabulares "
            "permitidos use el paquete ZIP CSV + JSON.",
            styles["ReportCell"]),
    ])
    document.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
