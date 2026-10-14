"""Construcción de informes PDF con resumen y tablas paginadas."""
from __future__ import annotations

from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

COLOR_MARCA = colors.HexColor("#6E3E18")
COLOR_ACENTO = colors.HexColor("#AC6E37")
COLOR_FONDO = colors.HexColor("#F5F0E8")
COLOR_LINEA = colors.HexColor("#D8D1C7")


def _parrafo(valor: object, estilo: ParagraphStyle) -> Paragraph:
    texto = escape("" if valor is None else str(valor)).replace("\n", "<br/>")
    return Paragraph(texto or "—", estilo)


def _pie(canvas, doc) -> None:
    canvas.saveState()
    ancho, _ = landscape(A4)
    canvas.setStrokeColor(COLOR_LINEA)
    canvas.line(14 * mm, 11 * mm, ancho - 14 * mm, 11 * mm)
    canvas.setFillColor(colors.HexColor("#6B6259"))
    canvas.setFont("Helvetica", 7)
    canvas.drawString(14 * mm, 7 * mm, "ACREDITTIA · Informe de uso interno")
    canvas.drawRightString(ancho - 14 * mm, 7 * mm, f"Página {doc.page}")
    canvas.restoreState()


def generar_pdf(
    titulo: str,
    cabeceras: list[str],
    filas: list[list],
    metadatos: dict[str, object],
) -> bytes:
    """Genera un informe PDF horizontal, imprimible y con tablas multipágina."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=13 * mm,
        bottomMargin=16 * mm,
        title=titulo,
        author="Acredittia",
    )
    estilos = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "ReporteTitulo",
        parent=estilos["Title"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=20,
        textColor=COLOR_MARCA,
        spaceAfter=2 * mm,
    )
    sub_style = ParagraphStyle(
        "ReporteSubtitulo",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#6B6259"),
    )
    meta_label_style = ParagraphStyle(
        "ReporteMetaLabel",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=COLOR_MARCA,
    )
    meta_value_style = ParagraphStyle(
        "ReporteMetaValue",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#29231E"),
    )
    header_style = ParagraphStyle(
        "ReporteTablaHeader",
        parent=estilos["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7,
        leading=8,
        textColor=colors.white,
        wordWrap="CJK",
    )
    cell_style = ParagraphStyle(
        "ReporteTablaCelda",
        parent=estilos["Normal"],
        fontName="Helvetica",
        fontSize=7,
        leading=8.5,
        textColor=colors.HexColor("#29231E"),
        wordWrap="CJK",
    )
    small_right_style = ParagraphStyle(
        "ReporteMetaRight",
        parent=sub_style,
        alignment=TA_RIGHT,
    )

    story = [
        Table(
            [[
                Paragraph("<b>ACREDITTIA</b>", ParagraphStyle(
                    "ReporteMarca",
                    parent=estilos["Normal"],
                    fontName="Helvetica-Bold",
                    fontSize=11,
                    textColor=colors.white,
                )),
                _parrafo("REPORTE OPERACIONAL", small_right_style),
            ]],
            colWidths=[doc.width * 0.35, doc.width * 0.65],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), COLOR_MARCA),
                ("BACKGROUND", (1, 0), (1, 0), COLOR_FONDO),
                ("TEXTCOLOR", (1, 0), (1, 0), COLOR_MARCA),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]),
        ),
        Spacer(1, 5 * mm),
        _parrafo(titulo, titulo_style),
        _parrafo("Resumen del período y detalle de los registros incluidos.", sub_style),
        Spacer(1, 4 * mm),
    ]

    metadata_rows = []
    for etiqueta, valor in metadatos.items():
        metadata_rows.append([
            _parrafo(etiqueta, meta_label_style),
            _parrafo(valor, meta_value_style),
        ])
    if metadata_rows:
        metadata = Table(
            metadata_rows,
            colWidths=[doc.width * 0.19, doc.width * 0.81],
            hAlign="LEFT",
        )
        metadata.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), COLOR_FONDO),
            ("BOX", (0, 0), (-1, -1), 0.5, COLOR_LINEA),
            ("INNERGRID", (0, 0), (-1, -1), 0.35, COLOR_LINEA),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 7),
            ("RIGHTPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.extend([metadata, Spacer(1, 5 * mm)])

    resumen = Table(
        [[
            _parrafo("REGISTROS INCLUIDOS", meta_label_style),
            _parrafo(f"{len(filas):,}", ParagraphStyle(
                "ReporteConteo",
                parent=meta_value_style,
                fontName="Helvetica-Bold",
                fontSize=13,
                textColor=COLOR_MARCA,
            )),
        ]],
        colWidths=[doc.width * 0.19, doc.width * 0.81],
        hAlign="LEFT",
    )
    resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FBF8F4")),
        ("BOX", (0, 0), (-1, -1), 0.6, COLOR_ACENTO),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.extend([resumen, Spacer(1, 5 * mm)])

    if cabeceras:
        tabla = [[_parrafo(cabecera, header_style) for cabecera in cabeceras]]
        tabla.extend([
            [_parrafo(valor, cell_style) for valor in fila]
            for fila in filas
        ])
        anchos = [doc.width / len(cabeceras)] * len(cabeceras)
        detalle = LongTable(
            tabla,
            colWidths=anchos,
            repeatRows=1,
            hAlign="LEFT",
            splitByRow=1,
        )
        detalle.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_MARCA),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.35, COLOR_LINEA),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [
                colors.white, colors.HexColor("#F8F6F3"),
            ]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(detalle)
    else:
        story.append(_parrafo("No hay columnas de detalle para este reporte.", sub_style))

    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)
    return buffer.getvalue()
