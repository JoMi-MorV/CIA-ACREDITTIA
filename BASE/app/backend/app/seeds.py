"""Datos semilla idempotentes: catálogos, admin y empresa demo."""
from datetime import date, datetime, timedelta, timezone  # Manejo de fechas y deltas en el seed de ops/métricas
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from .models import (
    Company, DocEjemplo, Faena, FaenaPlataforma, RequisitoTemplate, User,
    Plan, Suscripcion,  # Datos comerciales usados por los indicadores Ops
)
from .models_ops import (  # Bloque completo para la consola interna de operaciones
    OpsComponente,
    OpsDisponibilidadDiaria,
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

    if not db.scalar(select(User).where(User.email == "demo@acredittia.cl")):
        demo = Company(nombre="DEMO SpA", rut="76.111.222-8",
                       email="demo@acredittia.cl", status="approved")
        db.add(demo)
        db.flush()
        db.add(User(email="demo@acredittia.cl",
                    password_hash=hash_password("Demo2026!"),
                    role="company", company_id=demo.id, status="approved"))
    
    if not db.scalar(select(User).where(User.email == "contacto@constructorasur.cl")):
        comp1 = Company(nombre="Constructora del Sur SpA", rut="77.222.333-k",
                        email="contacto@constructorasur.cl", status="approved")
        db.add(comp1)
        db.flush()
        db.add(User(email="admin@constructorasur.cl",
                    password_hash=hash_password("Password2026!"),
                    role="company", company_id=comp1.id, status="approved"))

    if not db.scalar(select(User).where(User.email == "ops@mineraandina.cl")):
        comp2 = Company(nombre="Minera Andina Operations", rut="78.444.555-1",
                        email="ops@mineraandina.cl", status="approved")
        db.add(comp2)
        db.flush()
        db.add(User(email="supervisor@mineraandina.cl",
                    password_hash=hash_password("Password2026!"),
                    role="company", company_id=comp2.id, status="approved"))

    if not db.scalar(select(User).where(User.email == "fleet@ltaustral.cl")):
        comp3 = Company(nombre="Logística y Transportes Austral", rut="79.888.999-5",
                        email="fleet@ltaustral.cl", status="approved")
        db.add(comp3)
        db.flush()
        db.add(User(email="transporte@ltaustral.cl",
                    password_hash=hash_password("Password2026!"),
                    role="company", company_id=comp3.id, status="approved"))
    db.commit()

    # ========================================================================
    # Datos comerciales demo para que los indicadores tengan MRR y clientes. 
    # Las funciones SQL de 08_consola_interna.sql calculan las métricas desde
    # planes y suscripciones; los snapshots no contienen cifras inventadas.
    # ========================================================================
    planes_demo = {
        "Básico": (4.0, "UF"),
        "Pro": (12.5, "UF"),
        "Enterprise": (30.0, "UF"),
    }
    planes = {}
    for nombre, (precio, moneda) in planes_demo.items():
        plan = db.scalar(select(Plan).where(Plan.nombre == nombre))
        if plan is None:
            plan = Plan(nombre=nombre, precio=precio, moneda=moneda,
                        periodo="mensual", activo=True)
            db.add(plan)
            db.flush()
        planes[nombre] = plan

    empresas_demo = [
        ("DEMO SpA", "Básico", 330),
        ("Constructora del Sur SpA", "Pro", 240),
        ("Minera Andina Operations", "Enterprise", 150),
        ("Logística y Transportes Austral", "Pro", 60),
    ]
    for nombre, plan_nombre, antiguedad_dias in empresas_demo:
        empresa = db.scalar(select(Company).where(Company.nombre == nombre))
        if empresa is None:
            continue
        suscripcion = db.scalar(
            select(Suscripcion).where(Suscripcion.company_id == empresa.id)
        )
        if suscripcion is None:
            creada = datetime.now(timezone.utc) - timedelta(days=antiguedad_dias)
            db.add(Suscripcion(
                company_id=empresa.id,
                plan_id=planes[plan_nombre].id,
                estado="activa",
                periodo_actual_desde=creada.date(),
                periodo_actual_hasta=(creada + timedelta(days=30)).date(),
                created_at=creada,
                updated_at=creada,
            ))
    db.commit()

    # ========================================================================
    # § OPS SEEDS — Consola Interna de Administración (/admin/ops) Población de datos para la consola interna de administración de operaciones, telemetría y métricas del sistema.
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

    # 3. Disponibilidad diaria de los últimos 30 días para que las barras luzcan operativas
    hoy = date.today()
    for comp_tuple in componentes_data:
        c_clave = comp_tuple[0]
        for i in range(30):
            d_fecha = hoy - timedelta(days=i)
            # Evitamos duplicados si ya existe
            existe_disp = db.scalar(
                select(OpsDisponibilidadDiaria).where(
                    OpsDisponibilidadDiaria.componente == c_clave,
                    OpsDisponibilidadDiaria.fecha == d_fecha
                )
            )
            if not existe_disp:
                db.add(OpsDisponibilidadDiaria(
                    componente=c_clave,
                    fecha=d_fecha,
                    estado="operativo",
                    uptime_pct=99.95,
                    latencia_p95_ms=120,
                    checks_total=1440,
                    checks_fallidos=0
                ))
    db.flush()

    # 4. Historial de ejecuciones recientes de procesos (para la tabla de procesos)
    for clave, _, _, _, _, _ in jobs_data:
        # Añadimos un run exitoso reciente por cada job si no tiene
        ultimo_run = db.scalar(
            select(OpsJobRun).where(OpsJobRun.job_clave == clave).order_by(OpsJobRun.created_at.desc())
        )
        if not ultimo_run:
            ahora_utc = datetime.now(timezone.utc)
            db.add(OpsJobRun(
                job_clave=clave,
                status="ok",
                disparo="cron",
                params={},
                started_at=ahora_utc - timedelta(minutes=15),
                finished_at=ahora_utc - timedelta(minutes=14),
                items_procesados=45,
                mensaje="Ejecución exitosa completada sin incidentes."
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