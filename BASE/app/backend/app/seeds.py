"""Datos semilla idempotentes: catálogos, clientes demo y telemetría de Ops."""
from datetime import date, datetime, timedelta, timezone  # Manejo de fechas y deltas en el seed de ops/métricas
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .models import (
    Company, DocEjemplo, Faena, FaenaPlataforma, RequisitoTemplate, User,
    Factura, Integracion, SyncLog,
    Plan, Suscripcion,  # Datos comerciales usados por los indicadores Ops
)
from .models_ops import (  # Bloque completo para la consola interna de operaciones
    OpsComponente,
    OpsDisponibilidadDiaria,
    OpsIncidente,
    OpsJob,
    OpsJobRun,
    MetricasMensuales,
    MetricasMensualesPlan,
)
from .security import hash_password

FAENAS = [
    ("Los Pelambres", "Antofagasta Minerals", "AMSA", "Coquimbo", "#1f6f54", -31.72, -70.49),
    ("Minera Centinela", "Antofagasta Minerals", "AMSA", "Antofagasta", "#8a5a00", -22.97, -69.09),
    ("Zaldívar", "Antofagasta Minerals", "AMSA", "Antofagasta", "#7a3030", -24.20, -69.05),
    ("Antucoya", "Antofagasta Minerals", "AMSA", "Antofagasta", "#3a5f8a", -22.63, -69.85),
    ("Candelaria", "Lundin Mining", "Lundin", "Atacama", "#795c9c", -27.51, -70.29),
    ("Caserones", "Lundin Mining", "Lundin", "Atacama", "#2f7d8a", -28.03, -69.28),
    ("Andina", "Codelco", "Codelco", "Valparaíso", "#b04a17", -33.15, -70.25),
    ("El Teniente", "Codelco", "Codelco", "O'Higgins", "#5f7a30", -34.09, -70.35),
]

PLATAFORMAS = {
    "Los Pelambres": ["SIGA", "DIRECTIC", "SGES", "Academia MLP", "EMSIPOR"],
    "Minera Centinela": ["SIGA", "INTELICONTROL"],
    "Zaldívar": ["WEBCONTROL"],
    "Antucoya": ["SIGA", "INTELICONTROL"],
    "Candelaria": ["WEBCONTROL"],
    "Caserones": ["WEBCONTROL", "SUCAL"],
    "Andina": ["META CONTRATAS", "WEBCONTROL"],
    "El Teniente": ["META CONTRATAS", "WEBCONTROL"],
}

REQ_EMPRESA = [
    ("Contrato de Servicio", True, "contrato", "legal", None),
    ("Estrategias de Control SSO", True, None, "certificacion", None),
    ("Declaración Representante Legal", True, None, "legal", None),
    ("Reunión de Arranque", True, None, "certificacion", None),
    ("Programa de Trabajo SSO", True, "programa", "certificacion", 12),
    ("Copia Carta Inicio Actividades SERNAGEOMIN", True, None, "legal", None),
    ("Matriz de Riesgo", True, None, "tecnico", 12),
    ("Procedimiento de Emergencia", True, None, "tecnico", None),
    ("Certificado Ley 16.744", True, "mutual", "legal", 1),
    ("Jornada Excepcional de Trabajo", False, None, "legal", None),
]
REQ_PERSONAL = [
    ("Cédula de Identidad", True, "licencia", "legal", None),
    ("Contrato de Trabajo", True, "contrato", "legal", None),
    ("Anexo Contrato", True, "contrato", "legal", None),
    ("Certificado de Salud y Examen de Altura", True, "altura", "medico", 12),
    ("Inducción Hombre Nuevo", True, "induccion", "capacitacion", 24),
    ("Reglamento Interno", True, "rioshs", "legal", None),
    ("Certificado de Estudios", True, "estudios", "legal", None),
    ("Finiquito Anterior", False, "finiquito", "legal", None),
    ("Consentimiento Alcohol y Drogas", True, "consentimiento", "legal", 12),
    ("ODI Curso COVID", True, "odi", "capacitacion", None),
    ("Certificado de Residencia", False, "residencia", "legal", 6),
    ("IRL Mina y Chancado", True, "irlmina", "capacitacion", 12),
    ("Manejo Defensivo", True, "curso", "capacitacion", 24),
]
REQ_EQUIPO = [
    ("Permiso de Circulación", True, "circulacion", "legal", 12),
    ("SOAP", True, "soap", "legal", 12),
    ("Revisión Técnica", True, "revtec", "tecnico", 12),
    ("GPS", True, "gps", "tecnico", None),
    ("Certificado Incorporación Multiflota GPS MLP", True, "gps", "tecnico", None),
    ("Certificado de Láminas", True, None, "tecnico", None),
    ("Inspección Visual", True, "checklist", "tecnico", 6),
    ("Certificado de Mantenciones", True, "mantencion", "tecnico", 6),
    ("Certificado de Operatividad", True, "mantencion", "tecnico", 12),
    ("Certificado Barra Antivuelcos", False, "barra", "tecnico", None),
]
REQ_EMSIPOR = [
    ("Solicitud AIC Mina", True, None, "certificacion", None, "SIGA"),
    ("Fotografía Trabajador", True, None, "certificacion", None, "SIGA"),
    ("Licencia Municipal de Conducir", True, "licencia", "legal", None, "SIGA"),
    ("Hoja de Vida del Conductor", True, None, "legal", 1, "SIGA"),
    ("Psicosensométrico Riguroso", True, "psico", "medico", 24, "DIRECTIC"),
    ("Curso Manejo Defensivo y Alta Montaña", True, "curso", "capacitacion", 24, "Academia MLP"),
    ("Examen Práctico Mina", True, None, "capacitacion", None, "EMSIPOR"),
    ("Anexo Faena", True, None, "legal", None, "EMSIPOR"),
    ("Anexo Mina", True, None, "legal", None, "EMSIPOR"),
]

EJEMPLOS = [
    ("contrato", "Contrato de Trabajo", "Código del Trabajo",
     [["Empleador", "Razón social y RUT"], ["Trabajador", "Nombre y RUT"]],
     "Debe estar firmado por ambas partes."),
    ("altura", "Certificado de Salud y Examen de Altura", "DS 594 / Estándar MLP",
     [["Resultado", "APTO / NO APTO"], ["Validez", "12 meses"]],
     "Solo centros médicos homologados por la faena."),
    ("induccion", "Inducción Hombre Nuevo", "Estándar del mandante",
     [["Vigencia", "24 meses"]], None),
    ("soap", "Seguro Obligatorio SOAP", "Ley 18.490",
     [["Vigencia", "Anual"], ["Patente", "Debe coincidir"]], None),
    ("revtec", "Revisión Técnica", "MTT",
     [["Vigencia", "Anual"]], None),
    ("psico", "Examen Psicosensométrico Riguroso", "Estándar EMSIPOR",
     [["Vigencia", "2 años"]], None),
    ("licencia", "Licencia Municipal de Conducir", "Ley de Tránsito",
     [["Clase", "Según tipo de vehículo"]], None),
    ("mutual", "Certificado Ley 16.744", "Mutualidad",
     [["Vigencia", "30 días desde emisión"]], "Se renueva mensualmente."),
    ("programa", "Programa de Trabajo SSO", "Estándar del mandante",
     [["Período", "Anual"]], None),
    ("rioshs", "Reglamento Interno de Orden, Higiene y Seguridad", "DT",
     [["Registro", "Dirección del Trabajo"]], None),
    ("estudios", "Certificado de Estudios", "MINEDUC",
     [["Nivel", "Según cargo"]], None),
    ("finiquito", "Finiquito Anterior", "Código del Trabajo",
     [["Firma", "Ministro de fe"]], None),
    ("consentimiento", "Consentimiento Alcohol y Drogas", "Estándar del mandante",
     [["Vigencia", "12 meses"]], None),
    ("residencia", "Certificado de Residencia", "Junta de vecinos / notarial",
     [["Vigencia", "6 meses"]], None),
    ("odi", "ODI - Obligación de Informar", "DS 40 art. 21",
     [["Firma", "Trabajador y empleador"]], None),
    ("irlmina", "IRL Mina y Chancado", "Estándar MLP",
     [["Vigencia", "12 meses"]], None),
    ("curso", "Certificado de Curso", "Organismo capacitador",
     [["Vigencia", "Según curso"]], None),
    ("circulacion", "Permiso de Circulación", "Municipalidad",
     [["Vigencia", "Anual"]], None),
    ("gps", "Certificado GPS", "Proveedor homologado",
     [["Proveedor", "Wisetrack / MiFlota / SafeTrack"]], None),
    ("checklist", "Inspección Visual / Checklist", "Estándar faena",
     [["Vigencia", "6 meses"]], None),
    ("mantencion", "Certificado de Mantenciones", "Taller homologado",
     [["Vigencia", "6 meses"]], None),
    ("barra", "Certificado Barra Antivuelcos", "Estándar MLP (camionetas)",
     [["Instalador", "Taller certificado"]], None),
]


def run(db: Session) -> None:
    if not db.scalar(select(Faena.id).limit(1)):
        for nombre, mandante, grupo, region, color, lat, lng in FAENAS:
            f = Faena(nombre=nombre, mandante=mandante, grupo=grupo,
                      region=region, color=color, lat=lat, lng=lng)
            db.add(f)
            db.flush()
            for p in PLATAFORMAS.get(nombre, []):
                db.add(FaenaPlataforma(faena_id=f.id, nombre=p))
        db.flush()

    if not db.scalar(select(DocEjemplo.clave).limit(1)):
        for clave, nombre, ref, campos, tip in EJEMPLOS:
            db.add(DocEjemplo(clave=clave, nombre=nombre, referencia=ref,
                              campos_clave=campos, notas=[], tip=tip))
        db.flush()

    if not db.scalar(select(RequisitoTemplate.id).limit(1)):
        contador = 0

        def agregar(ambito, filas):
            nonlocal contador
            for fila in filas:
                titulo, oblig, ejemplo, tipo, vig = fila[:5]
                plataforma = fila[5] if len(fila) > 5 else None
                contador += 1
                db.add(RequisitoTemplate(
                    ambito=ambito, titulo=titulo, codigo=f"REQ-{contador:03d}",
                    tipo=tipo, obligatorio=oblig, ejemplo_clave=ejemplo,
                    vigencia_meses=vig, plataforma=plataforma,
                ))

        agregar("empresa", REQ_EMPRESA)
        agregar("personal", REQ_PERSONAL)
        agregar("equipo", REQ_EQUIPO)
        agregar("emsipor", REQ_EMSIPOR)
        db.flush()

    if not db.scalar(select(User).where(User.email == "admin@acredittia.cl")):
        db.add(User(email="admin@acredittia.cl",
                    password_hash=hash_password("Admin2026!"),
                    role="admin", company_id=None, status="approved"))

    # Empresas demo: variedad de industrias, tamaños y estados comerciales para
    # que clientes, planes y filtros de Ops se parezcan a producción.
    empresas_seed = [
        ("DEMO SpA", "76.111.222-8", "demo@acredittia.cl", "mineria", "demo@acredittia.cl", "Demo2026!", True),
        ("Constructora del Sur SpA", "77.222.333-k", "contacto@constructorasur.cl", "construccion", "admin@constructorasur.cl", "Password2026!", False),
        ("Minera Andina Operations", "78.444.555-1", "ops@mineraandina.cl", "mineria", "supervisor@mineraandina.cl", "Password2026!", False),
        ("Logística y Transportes Austral", "79.888.999-5", "fleet@ltaustral.cl", "industrial", "transporte@ltaustral.cl", "Password2026!", False),
        ("Energía Cordillera SpA", "76.345.678-9", "operaciones@energiacordillera.cl", "energia", "operaciones@energiacordillera.cl", "Password2026!", False),
        ("Servicios Industriales Norte Ltda", "77.456.789-0", "contacto@sinorte.cl", "industrial", "contacto@sinorte.cl", "Password2026!", False),
        ("Obras Civiles Patagonia SpA", "78.567.890-1", "admin@obraspatagonia.cl", "construccion", "admin@obraspatagonia.cl", "Password2026!", False),
        ("Mantenimiento Solar del Valle", "79.678.901-2", "mesa@solardelvalle.cl", "energia", "mesa@solardelvalle.cl", "Password2026!", False),
        ("Transporte Ruta 5 Ltda", "76.789.012-3", "control@ruta5.cl", "industrial", "control@ruta5.cl", "Password2026!", False),
        ("GeoPerforaciones Chile SpA", "77.890.123-4", "personas@geoperforaciones.cl", "mineria", "personas@geoperforaciones.cl", "Password2026!", False),
        ("Montajes Eléctricos Andinos", "78.901.234-5", "acreditacion@montajesandinos.cl", "energia", "acreditacion@montajesandinos.cl", "Password2026!", False),
        ("Ingeniería y Proyectos Delta", "79.012.345-6", "proyectos@deltaingenieria.cl", "otras", "proyectos@deltaingenieria.cl", "Password2026!", False),
        ("Aseo Industrial Pacífico", "76.123.456-7", "servicios@aseopacifico.cl", "industrial", "servicios@aseopacifico.cl", "Password2026!", False),
        ("Maquinarias Alto Maipo", "77.234.567-8", "flota@altomaipo.cl", "construccion", "flota@altomaipo.cl", "Password2026!", False),
        ("Consultora Seguridad Integral", "78.345.678-9", "sso@seguridadintegral.cl", "otras", "sso@seguridadintegral.cl", "Password2026!", False),
        ("Aguas y Procesos del Norte", "79.456.789-0", "operaciones@aguasprocesos.cl", "industrial", "operaciones@aguasprocesos.cl", "Password2026!", False),
    ]
    empresas = {}
    for nombre, rut, email, industria, usuario_email, password, es_demo in empresas_seed:
        empresa = db.scalar(select(Company).where(Company.rut == rut))
        if empresa is None:
            empresa = Company(nombre=nombre, rut=rut, email=email,
                              status="approved", es_demo=es_demo)
            db.add(empresa)
            db.flush()
        empresa.industria = industria
        empresas[nombre] = empresa
        if not db.scalar(select(User).where(User.email == usuario_email)):
            db.add(User(email=usuario_email, password_hash=hash_password(password),
                        role="company", company_id=empresa.id, status="approved"))
    db.commit()

    # ========================================================================
    # Datos comerciales demo para que los indicadores tengan MRR y clientes. 
    # Las funciones SQL de 08_consola_interna.sql calculan las métricas desde
    # planes y suscripciones; los snapshots no contienen cifras inventadas.
    # ========================================================================
    planes_demo = {
        "Básico": (4.0, "UF", {"usuarios": 25, "faenas": 1}),
        "Pro": (12.5, "UF", {"usuarios": 120, "faenas": 5}),
        "Enterprise": (30.0, "UF", {"usuarios": 1000, "faenas": 50}),
    }
    planes = {}
    for nombre, (precio, moneda, limites) in planes_demo.items():
        plan = db.scalar(select(Plan).where(Plan.nombre == nombre))
        if plan is None:
            plan = Plan(nombre=nombre, precio=precio, moneda=moneda,
                        periodo="mensual", limites=limites, activo=True)
            db.add(plan)
            db.flush()
        else:
            plan.limites = limites
        planes[nombre] = plan

    empresas_demo = [
        ("DEMO SpA", "Básico", "activa", 330),
        ("Constructora del Sur SpA", "Pro", "activa", 240),
        ("Minera Andina Operations", "Enterprise", "activa", 150),
        ("Logística y Transportes Austral", "Pro", "morosa", 60),
        ("Energía Cordillera SpA", "Enterprise", "activa", 410),
        ("Servicios Industriales Norte Ltda", "Pro", "activa", 290),
        ("Obras Civiles Patagonia SpA", "Básico", "trial", 18),
        ("Mantenimiento Solar del Valle", "Pro", "activa", 125),
        ("Transporte Ruta 5 Ltda", "Básico", "cancelada", 520),
        ("GeoPerforaciones Chile SpA", "Enterprise", "activa", 85),
        ("Montajes Eléctricos Andinos", "Pro", "activa", 205),
        ("Ingeniería y Proyectos Delta", "Básico", "trial", 11),
        ("Aseo Industrial Pacífico", "Básico", "activa", 75),
        ("Maquinarias Alto Maipo", "Pro", "morosa", 305),
        ("Consultora Seguridad Integral", "Básico", "activa", 190),
        ("Aguas y Procesos del Norte", "Enterprise", "activa", 365),
    ]
    suscripciones = {}
    for nombre, plan_nombre, estado, antiguedad_dias in empresas_demo:
        empresa = db.scalar(select(Company).where(Company.nombre == nombre))
        if empresa is None:
            continue
        suscripcion = db.scalar(
            select(Suscripcion).where(Suscripcion.company_id == empresa.id)
        )
        if suscripcion is None:
            creada = datetime.now(timezone.utc) - timedelta(days=antiguedad_dias)
            suscripcion = Suscripcion(
                company_id=empresa.id,
                plan_id=planes[plan_nombre].id,
                estado=estado,
                trial_hasta=(creada + timedelta(days=14)).date()
                if estado == "trial" else None,
                periodo_actual_desde=creada.date(),
                periodo_actual_hasta=(creada + timedelta(days=30)).date(),
                medio_pago_ref=(f"pm_demo_{empresa.id.hex[:10]}"
                                if estado != "trial" else None),
                created_at=creada,
                updated_at=creada,
            )
            db.add(suscripcion)
            db.flush()
        suscripciones[nombre] = suscripcion

        # Una factura por cliente deja visibles pagos al día, pendientes y fallidos.
        folio = f"DEMO-{empresa.rut.replace('-', '')}"
        if not db.scalar(select(Factura).where(Factura.folio == folio)):
            monto = float(planes[plan_nombre].precio) * 38500
            factura_estado = {
                "activa": "pagada", "trial": "pendiente",
                "morosa": "fallida", "cancelada": "anulada",
            }[estado]
            emitida = datetime.now(timezone.utc) - timedelta(days=18)
            db.add(Factura(
                suscripcion_id=suscripcion.id, company_id=empresa.id,
                folio=folio, monto=monto, moneda="CLP", estado=factura_estado,
                gateway_ref=f"gw_demo_{empresa.rut.replace('-', '')}",
                emitida_at=emitida,
                pagada_at=emitida + timedelta(days=2)
                if factura_estado == "pagada" else None,
            ))
    db.commit()

    # Integraciones y sincronizaciones: cada cliente muestra una combinación
    # distinta de conectores activos, con error y desconectados.
    integraciones_por_empresa = {
        "DEMO SpA": [("siga", "activa"), ("gdrive", "activa")],
        "Constructora del Sur SpA": [("workmate", "activa"), ("whatsapp", "activa")],
        "Minera Andina Operations": [("siga", "activa"), ("metacontratas", "con_error"), ("webcontrol", "activa")],
        "Logística y Transportes Austral": [("webcontrol", "con_error"), ("whatsapp", "desconectada")],
        "Energía Cordillera SpA": [("workmate", "activa"), ("gdrive", "activa")],
        "Servicios Industriales Norte Ltda": [("metacontratas", "activa")],
        "Obras Civiles Patagonia SpA": [("webcontrol", "desconectada")],
        "Mantenimiento Solar del Valle": [("gdrive", "activa"), ("whatsapp", "activa")],
        "Transporte Ruta 5 Ltda": [("siga", "desconectada")],
        "GeoPerforaciones Chile SpA": [("siga", "activa"), ("workmate", "activa"), ("gdrive", "con_error")],
        "Montajes Eléctricos Andinos": [("metacontratas", "activa"), ("whatsapp", "activa")],
        "Ingeniería y Proyectos Delta": [("gdrive", "desconectada")],
        "Aseo Industrial Pacífico": [("workmate", "con_error")],
        "Maquinarias Alto Maipo": [("webcontrol", "activa"), ("siga", "activa")],
        "Consultora Seguridad Integral": [("whatsapp", "activa")],
        "Aguas y Procesos del Norte": [("siga", "activa"), ("metacontratas", "activa"), ("gdrive", "activa")],
    }
    for nombre, integraciones in integraciones_por_empresa.items():
        empresa = empresas.get(nombre)
        if empresa is None:
            continue
        for tipo, estado in integraciones:
            integ = db.scalar(select(Integracion).where(
                Integracion.company_id == empresa.id, Integracion.tipo == tipo))
            if integ is None:
                ultima_sync = datetime.now(timezone.utc) - timedelta(hours=(2 + len(tipo)))
                integ = Integracion(
                    company_id=empresa.id, tipo=tipo, estado=estado,
                    credenciales_ref=f"kv/demo/{empresa.id}/{tipo}",
                    config={"frecuencia": "cada_6_horas", "ambiente": "demo",
                            "registros_por_sync": 120 + len(tipo) * 11},
                    ultima_sync_at=ultima_sync if estado != "desconectada" else None,
                )
                db.add(integ)
                db.flush()
            if not db.scalar(select(SyncLog).where(SyncLog.integracion_id == integ.id)):
                base = datetime.now(timezone.utc) - timedelta(days=2)
                db.add(SyncLog(
                    integracion_id=integ.id, company_id=empresa.id,
                    status="error" if estado == "con_error" else "exito",
                    mensaje=("Token expirado; requiere reconexión."
                             if estado == "con_error" else "Sincronización completada."),
                    registros_procesados=0 if estado == "con_error" else 120 + len(tipo) * 11,
                    started_at=base, finished_at=base + timedelta(seconds=38),
                ))
    db.commit()

    # ========================================================================
    # § OPS SEEDS — Consola Interna de Administración (/admin) Población de datos para la consola interna de administración de operaciones, telemetría y métricas del sistema.
    # =================================================================ar
    # 1. Componentes monitoreados del sistema
    componentes_data = [
        ("api", "API Backend", "FastAPI en Container Apps", 1),
        ("db", "Base de datos", "PostgreSQL 16 · primario + réplica", 2),
        ("workers", "Workers · Celery", "Colas: documentos, alertas, sync", 3),
        ("storage", "Storage de documentos", "Azure Blob Storage", 4),
        ("ia", "Verificación IA", "Lectura y validación de documentos", 5),
        ("integraciones", "Integraciones externas", "SIGA · Workmate · Metacontratas · WebControl", 6),
    ]
    for clave, nombre, desc, orden in componentes_data:
        if not db.get(OpsComponente, clave):
            db.add(OpsComponente(clave=clave, nombre=nombre, descripcion=desc, orden=orden, activo=True))
    db.flush()

    # 2. Procesos críticos programados
    jobs_data = [
        ("vencimientos", "Cálculo de vencimientos y snapshots", "programado", "30 0 * * *", "workers", 3600),
        ("reportes_programados", "Reportes programados", "programado", "5 * * * *", "workers", 1800),
        ("purga_temporales", "Purga de blobs temporales IA", "programado", "0 4 * * *", "storage", 900),
        ("ops_heartbeat", "Sondeo de componentes", "programado", "* * * * *", "api", 55),
        ("ops_disponibilidad", "Consolidación de disponibilidad", "programado", "5 0 * * *", "api", 600),
        ("metricas_snapshot", "Snapshot de métricas de negocio", "programado", "10 2 * * *", "api", 1800),
        ("ops_retencion", "Retención y poda de telemetría", "programado", "30 3 * * 0", "db", 1800),
        ("ia_revision", "Verificación IA de documentos", "continuo", None, "ia", 3600),
        ("webhooks_clientes", "Webhooks a clientes", "continuo", None, "api", 3600),
    ]
    for clave, nombre, tipo, cron, comp, timeout in jobs_data:
        if not db.get(OpsJob, clave):
            db.add(OpsJob(clave=clave, nombre=nombre, tipo=tipo, cron_expr=cron, componente=comp, timeout_s=timeout, activo=True))
    db.flush()

    # 3. Disponibilidad diaria variada de los últimos 30 días para que las
    # barras distingan operación normal, degradación e incidentes.
    hoy = date.today()
    disponibilidad_base = {
        "api": (99.98, 95), "db": (99.99, 70), "workers": (99.72, 240),
        "storage": (99.94, 160), "ia": (98.85, 620),
        "integraciones": (97.90, 840),
    }
    for indice, comp_tuple in enumerate(componentes_data):
        c_clave = comp_tuple[0]
        for i in range(30):
            d_fecha = hoy - timedelta(days=i)
            uptime, latencia = disponibilidad_base[c_clave]
            fallo = (i + indice) % 17 == 0
            degradado = (i + indice) % 9 == 0
            uptime_dia = 98.35 if fallo else (99.35 if degradado else uptime)
            checks_fallidos = 24 if fallo else (8 if degradado else 1)
            estado = "caido" if fallo else ("degradado" if degradado else "operativo")
            existe_disp = db.scalar(
                select(OpsDisponibilidadDiaria).where(
                    OpsDisponibilidadDiaria.componente == c_clave,
                    OpsDisponibilidadDiaria.fecha == d_fecha
                )
            )
            valores = {
                "estado": estado, "uptime_pct": uptime_dia,
                "latencia_p95_ms": latencia + (280 if degradado else 0),
                "checks_total": 1440, "checks_fallidos": checks_fallidos,
            }
            if existe_disp is None:
                db.add(OpsDisponibilidadDiaria(componente=c_clave,
                                               fecha=d_fecha, **valores))
            else:
                for campo, valor in valores.items():
                    setattr(existe_disp, campo, valor)
    db.flush()

    # 4. Historial de ejecuciones recientes con resultados distintos para la
    # tabla de procesos y su diagnóstico operativo.
    estados_runs = ["ok", "ok", "error", "timeout"]
    for job_indice, (clave, _, _, _, _, _) in enumerate(jobs_data):
        existentes = db.scalars(select(OpsJobRun).where(
            OpsJobRun.job_clave == clave).order_by(OpsJobRun.created_at)).all()
        ahora_utc = datetime.now(timezone.utc)
        for run_indice in range(len(existentes), 4):
            status = estados_runs[(job_indice + run_indice) % len(estados_runs)]
            inicio = ahora_utc - timedelta(hours=run_indice * 8 + 1)
            db.add(OpsJobRun(
                job_clave=clave, status=status,
                disparo="manual" if run_indice == 2 else "cron",
                params={"origen": "seed_demo", "reintento": run_indice == 3},
                started_at=inicio,
                finished_at=(inicio + timedelta(minutes=2)
                             if status != "timeout" else None),
                items_procesados=(45 + job_indice * 7
                                  if status == "ok" else 0),
                mensaje=("Ejecución exitosa completada."
                         if status == "ok" else
                         "Timeout esperando respuesta del proveedor."
                         if status == "timeout" else
                         "Error controlado durante el procesamiento."),
            ))
    db.flush()

    # 5. Incidentes y decisiones operativas: mezcla de casos resueltos y
    # abiertos para poblar la bandeja de seguimiento del administrador.
    admin_user = db.scalar(select(User).where(User.email == "admin@acredittia.cl"))
    incidentes_seed = [
        ("integraciones", "caido", "Token SIGA expirado en clientes mineros",
         "Se detectaron respuestas 401 en la sincronización de SIGA.", "resuelto"),
        ("ia", "degradado", "Decisión operativa: limitar concurrencia de IA",
         "La latencia p95 superó el umbral; se redujo la concurrencia para proteger la cola.", "monitoreando"),
        ("workers", "degradado", "Reintentos elevados en documentos",
         "La cola de documentos acumuló reintentos durante la ventana nocturna.", "resuelto"),
        ("db", "caido", "Failover preventivo de base de datos",
         "Se ejecutó cambio controlado a la réplica por mantenimiento del primario.", "resuelto"),
        ("storage", "degradado", "Decisión operativa: ampliar retención temporal",
         "Se amplió temporalmente la retención de blobs para facilitar auditoría.", "abierto"),
    ]
    for indice, (componente, severidad, titulo, descripcion, estado) in enumerate(incidentes_seed):
        if db.scalar(select(OpsIncidente).where(OpsIncidente.titulo == titulo)):
            continue
        abierto_at = datetime.now(timezone.utc) - timedelta(days=indice + 1, hours=3)
        db.add(OpsIncidente(
            componente=componente, severidad=severidad, estado=estado,
            origen="manual" if "Decisión" in titulo else "auto",
            titulo=titulo, descripcion=descripcion,
            resolucion=("Cambio aplicado y monitoreo normalizado."
                         if estado == "resuelto" else None),
            abierto_at=abierto_at,
            resuelto_at=(abierto_at + timedelta(hours=2)
                         if estado == "resuelto" else None),
            creado_por=admin_user.id if admin_user else None,
        ))
    db.flush()

    # ========================================================================
    # § SEED DE INDICADORES
    # ========================================================================
    # El mes actual se calcula con la función real de 08. Para meses anteriores
    # se cargan snapshots de demostración porque suscripciones solo conserva
    # una fila vigente por empresa y no permite reconstruir su historia.
    hoy = date.today()
    mes_actual = hoy.replace(day=1)
    valor_uf = 38500.0

    def mes_hacia_atras(mes: date, cantidad: int) -> date:
        total = mes.year * 12 + mes.month - 1 - cantidad
        return date(total // 12, total % 12 + 1, 1)

    # La serie crece hacia el mes actual para que MRR, altas, bajas y churn
    # sean visibles al abrir la consola con una base recién creada.
    planes_hist = [
        (planes["Básico"], 1_700_000),
        (planes["Pro"], 4_600_000),
        (planes["Enterprise"], 8_900_000),
    ]
    for antiguedad in range(12, 0, -1):
        mes = mes_hacia_atras(mes_actual, antiguedad)
        paso = 12 - antiguedad
        clientes = 2 + paso // 3
        usuarios = 280 + paso * 45
        mrr = 8_200_000 + paso * 620_000
        altas = 1 + (paso % 3)
        bajas = 1 if paso % 4 == 2 else 0
        churn = round(100.0 * bajas / max(clientes - altas, 1), 2)

        fila = db.get(MetricasMensuales, mes)
        valores = {
            "valor_uf": valor_uf, "mrr_clp": mrr,
            "mrr_nuevos_clp": altas * 620_000,
            "mrr_expansion_clp": 0, "mrr_contraccion_clp": 0,
            "mrr_perdido_clp": -bajas * 410_000,
            "clientes_activos": clientes, "altas": altas, "bajas": bajas,
            "churn_clientes_pct": churn,
            "churn_ingresos_pct": round(churn * 0.8, 2),
            "nrr_pct": round(100 - churn * 0.8, 2),
            "usuarios_totales": usuarios,
            "usuarios_activos": round(usuarios * 0.8),
            "cerrado": True,
        }
        if fila is None:
            db.add(MetricasMensuales(mes=mes, **valores))
        else:
            for campo, valor in valores.items():
                setattr(fila, campo, valor)
        db.flush()

        for plan, proporcion in planes_hist:
            clientes_plan = max(1, round(clientes * proporcion / 15_200_000))
            valores_plan = {
                "clientes": clientes_plan,
                "usuarios": max(1, round(usuarios * proporcion / 15_200_000)),
                "mrr_clp": round(mrr * proporcion / 15_200_000),
                "churn_clientes_pct": churn,
                "nrr_pct": round(100 - churn * 0.8, 2),
            }
            fila_plan = db.get(MetricasMensualesPlan, (mes, plan.id))
            if fila_plan is None:
                db.add(MetricasMensualesPlan(mes=mes, plan_id=plan.id,
                                             **valores_plan))
            else:
                for campo, valor in valores_plan.items():
                    setattr(fila_plan, campo, valor)

    # El snapshot actual y sus métricas por plan sí salen de las funciones SQL
    # de 08, usando las suscripciones que existen en la base.
    db.execute(text(
        "SELECT ops_snapshot_metricas(:mes, CAST(:uf AS NUMERIC), false, true)"),
        {"mes": mes_actual, "uf": valor_uf})
    db.commit()