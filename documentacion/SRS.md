# SRS — Acredittia

Especificación de requisitos de software · versión 0.21 · 05-10-2026

**Estado documental:** borrador de trabajo para revisión. No constituye aceptación de todas las propuestas ni certificación de producción.

## 1. Propósito y alcance

Definir qué debe cumplir Acredittia, qué existe actualmente, qué evidencia lo respalda y qué falta para cerrar cada requisito. Este documento es la referencia funcional; [PLAN_DE_TRABAJO.md](PLAN_DE_TRABAJO.md) organiza su implementación y [VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md) conserva la evidencia de ejecución.

El alcance inicial comprende la plataforma multiempresa de acreditación documental y, con mayor detalle, las ocho prioridades de ADMIN. La consola se centraliza en `http://localhost:3000/admin/dashboard`. Las rutas públicas administrativas de API utilizan `/api/v1/admin`.

Se incluyen autenticación, administración de empresas y usuarios, contratos, personal, equipos, documentos, alertas, calendario, reportes y operación técnica. La evaluación detallada del portal de empresa es preliminar: no se considera validado por completo porque existan sus endpoints.

No se incluyen como compromisos de esta versión nuevos proveedores de IA, conectores externos específicos, facturación real, aplicaciones móviles ni una migración completa de los nombres internos históricos. Su existencia en código o en una demo no demuestra integración productiva.

## 2. Convenciones y control del documento

### 2.1 Estados de requisitos

| Estado | Significado |
|---|---|
| IV — Implementado y validado | Cumple el comportamiento descrito dentro del alcance probado; no implica cobertura universal. |
| ISV — Implementado sin validación completa | Hay código o interfaz, pero falta evidencia suficiente del flujo completo. |
| PAR — Parcial | Una parte existe y otra está pendiente. |
| COR — Requiere corrección | Se identificó un defecto o una divergencia respecto al comportamiento esperado. |
| PEN — Pendiente | No se identificó implementación del comportamiento propuesto. |

Los estados describen el requisito completo: una comprobación HTTP 200 no basta para clasificar un CRUD o un control de seguridad como IV. Los cambios de estado deben citar una prueba o revisión y su fecha.

### 2.2 Prioridades

- **P0:** condición para exponer el sistema con datos reales; seguridad y aislamiento.
- **P1:** necesaria para cerrar la funcionalidad o contar con validación fiable.
- **P2:** mejora necesaria para completar seguimiento, métricas o experiencia.

Los criterios de aceptación expresan el objetivo a verificar. Cuando dependen de una decisión de producto, se indica `DEC-*`; hasta resolverla, la definición es propuesta y no un compromiso aprobado.

### 2.3 Identificadores y trazabilidad

`RF-*` identifica requisitos funcionales; `RNF-*`, requisitos no funcionales; `DEC-*`, decisiones pendientes; `PT-*`, paquetes de trabajo. Cada paquete del plan remite a requisitos. Los identificadores se conservan aunque cambie el nombre de una pantalla.

La versión 0.1 se basa en la revisión y validación del 29-09-2026. La versión 0.2 incorpora el cronograma proporcionado por el equipo, observaciones a sus actividades declaradas al 100% y un resumen general. No declara conformidad certificada con una norma externa. La versión 0.5 incorpora fichas uniformes y estimaciones individuales propuestas, conservando los porcentajes originales del cronograma. La versión 0.6 registra la primera entrega de código: conversión UF, registro de tareas inproc, pruebas documentales e índices mediante esquema 8. Los porcentajes se conservan hasta revisar su estimación; los estados se actualizan según la evidencia nueva. La versión 0.7 precisa las brechas de permisos, auditoría, metadatos, salud y separación de métricas mediante revisión de código; no incorpora nuevas pruebas ni cambios funcionales. Markdown es el formato maestro; PDF puede utilizarse como copia de revisión indicando versión y fecha.

### 2.4 Avance declarado, validación y origen del alcance

La versión 0.8 registra la corrección de clasificación del buscador y sus pruebas de regresión del 30-09-2026. RF-BUS-01 pasa de COR a PAR; conserva la estimación previa y las decisiones pendientes. Evidencia en EV-01.

La versión 0.9 incorpora la validación de longitud del buscador tras quitar espacios exteriores. Regresión focalizada: 32 aprobadas, 0 fallidas, 30-09-2026 (EV-01). Se conservan estados y porcentajes.

La versión 0.10 incorpora indicadores de recorte y límite por categoría en el buscador, con presentación explícita en interfaz. Evidencia de esta entrega en EV-01; RF-BUS-01 sigue PAR y conserva su estimación.

La versión 0.11 registra PT-03-01: configuración explícita de producción, semillas opt-in y bloqueo de tokens de recuperación en respuestas productivas. No acredita despliegue ni roles PostgreSQL efectivos. Estados y porcentajes conservados; EV-01.

La versión 0.12 registra PT-03-02: guarda de conexiones PostgreSQL nuevas de API/Celery en producción contra roles administrativos y propietarios de tablas. Pruebas con roles reales en BD efímera en EV-01. No cambia roles del Compose ni del entorno habitual; RF-SEG-01/RNF-SEG-01 continúan PAR.

La versión 0.13 incorpora reactivación desde Usuarios e invalidación de sesiones al revocar/cambiar estado desde ADMIN. Esquema 9 añade versión de sesión por usuario. RF-USU-01 continúa PAR; porcentajes conservados y evidencia en EV-01.

La versión 0.14 corrige la identificación de cuentas en Usuarios: ADMIN recibe nombre y correo real para gestionar permisos; la interfaz identifica por correo las cuentas sin nombre y las confirmaciones de revocación/reactivación. Evidencia en EV-01; estados y porcentajes conservados.

La versión 0.15 registra la ampliación de datos demo operacionales para las 16 empresas, la compatibilidad de rutas Ops bajo `/admin` y `/admin/ops`, la inclusión de empresas aprobadas sin usuarios en el resumen de baja actividad, la auditoría global de creación de faenas y el criterio de impacto indeterminado cuando no existe vínculo verificable con una empresa. La suite completa backend pasó 363/363 el 01-10-2026 en PostgreSQL temporal. Los requisitos relacionados continúan PAR/ISV donde aún quedan criterios de aceptación; no se cambian porcentajes ni se declara aceptación productiva.

La versión 0.16 registra la nueva sección de asignación de responsables integrada en la página de Contratos del portal de empresa. Una cuenta `company` puede elegir una cuenta existente de su misma empresa para asignarla como `contract_admin` de un contrato; la interfaz advierte que la cuenta pierde el alcance general o se mueve desde otro contrato. Se elimina la página independiente de responsables. El frontend compila con 22 rutas. No se validaron mutaciones en navegador ni se implementaron invitación completa y activación por correo; RF-CLI-08 sigue PAR y la asignación no acredita la identidad real del encargado. Evidencia EV-10.

La versión 0.17 incorpora filtro servidor por tipo y filtros específicos por categoría en el buscador global. Empresas y personas se pueden buscar por su RUT existente; las cuentas de acceso no tienen RUT propio. Los resultados no devuelven el RUT y no se requiere una migración de esquema. Se mantiene compatibilidad acotada con bases en versión 10 que conservan la columna nullable `users.rut` de la migración retirada. Pruebas focalizadas y arranque Compose registrados en EV-01; no se declara recorrido de navegador.

La versión 0.18 añade al detalle global expandible de cada empresa el evento más reciente y su actor, mostrando fecha, acción/módulo y entidad, sin email ni descripción libre. Se probó el endpoint con dos eventos y actor identificado; el frontend compiló en Docker. El contenedor web se recreó y Next informó estado `Ready`; no se completó una comprobación HTTP de la ruta tras ese reinicio.

La versión 0.19 documenta las mejoras de interfaz del buscador global: filtros de cargo y tipo de equipo cargados desde catálogos; búsqueda por filtros específicos aunque el texto esté vacío (sin filtro específico se requieren al menos dos caracteres); y ficha agregada expandible debajo de la fila seleccionada. La ficha se identifica por resultado, solo se mantiene una abierta y las respuestas tardías se descartan al cambiar la búsqueda, abrir otra fila o cerrar la ficha. La evidencia de esta actualización es la revisión del código frontend; no se registran pruebas ni recorrido de navegador nuevos.

La versión 0.20 agrega el nombre completo del usuario inicial al registro de empresa y una sección autenticada «Mi perfil» para actualizar nombre, correo y contraseña usando el endpoint existente `/auth/me`. El nombre se almacena en `users.nombre`, separado de la razón social; cambiar contraseña exige la actual y conserva la sesión indicada. No requiere migración de esquema. La cobertura automatizada y compilación quedan registradas en VALIDACION_ACTUAL.md.

La versión 0.21 oculta el acceso «Mi perfil» y bloquea la ruta `/perfil` cuando ADMIN utiliza «Ver como empresa»; el acceso directo se redirige al dashboard del contexto observado y no solicita ni modifica datos de perfil. Al salir de esa vista, el perfil propio de ADMIN vuelve a estar disponible. No cambia autorización ni contenido de los flujos propios de empresa para sus cuentas autenticadas.

Se conservan los **100% declarados en el cronograma** como cierre de la actividad en su alcance y fecha originales. Se permite registrar **«Completada con observaciones»** cuando existen ajustes posteriores o evidencia por adjuntar. Esta convención de seguimiento no certifica aceptación del cliente ni convierte una funcionalidad parcial en validada.

Se mantienen dos estados independientes:

- **Actividad del cronograma:** porcentaje declarado por el equipo, con observaciones y evidencia documental pendiente cuando corresponda.
- **Requisito del SRS:** estado técnico IV/ISV/PAR/COR/PEN, según implementación y pruebas. Conserva los pendientes aunque la actividad de integración original figure al 100%.

Una actividad de «ejecutar pruebas y registrar incidencias» puede estar terminada con pruebas fallidas. Una actividad de «integración» puede estar completada en su alcance inicial y originar después correcciones. Si un defecto impide un criterio de aceptación original, se registra la desviación y se revisa su cierre técnico; no se presenta como una mejora opcional.

El cronograma original distingue **Comprometido, Condicionado y Opcional**. Estas categorías no cambian por la prioridad técnica P0/P1/P2. Celery/Redis/Beat y las sondas de las actividades 64, 67, 72 y 74 conservan su alcance condicionado; Application Insights/p95 (86) y métricas avanzadas (89) conservan su alcance opcional. Implementación existente no equivale a aceptación o incorporación formal al compromiso.

Las ocho prioridades ADMIN fueron comunicadas por el usuario como correcciones/recomendaciones posteriores del cliente. Se relacionan con el cronograma, pero no se presume que todos sus detalles formaran parte del acuerdo inicial. Las recomendaciones técnicas surgidas de nuestra revisión también deben distinguirse de esas solicitudes. La fuente, fecha y aprobación de cada cambio deben incorporarse al seguimiento antes de alterar alcance, fechas o pesos del cronograma. El inventario del portal de empresa describe la base existente; no compromete su reconstrucción.

### 2.5 Interpretación de los porcentajes

> **Interpretación de los porcentajes:** Los porcentajes representan estimaciones de avance del trabajo y se utilizan como referencia para identificar requisitos pendientes o que requieren mejoras. No representan porcentajes de cumplimiento técnico verificado ni sustituyen los criterios de aceptación. El porcentaje debe justificarse mediante las funcionalidades implementadas, los pendientes identificados y la evidencia disponible. Un requisito o actividad con 100 % de avance puede conservar observaciones de validación, correcciones o ajustes posteriores, los cuales permanecen abiertos hasta su resolución.

Los valores de las fichas son **propuestas iniciales de gestión para revisión del equipo**, basadas en la evidencia documental disponible al 29-09-2026. No son mediciones de esfuerzo ni resultados de una nueva ejecución de pruebas. Se estiman individualmente considerando componentes existentes y brechas; no se aplica una equivalencia automática entre IV/ISV/PAR/COR/PEN y porcentaje.

El avance del requisito es independiente del porcentaje declarado de la actividad del cronograma. No se sustituyen ni se promedian: no hay pesos por requisito acordados. Se conservan los 100 % declarados y las celdas sin avance informado. Para cambiar una estimación, registrar fecha, responsable, valor anterior/nuevo, fundamento, evidencia y pendientes. Un defecto crítico puede bloquear la aceptación con un avance estimado alto.

## 3. Actores, datos y restricciones

| Actor | Alcance actual | Objetivo y restricción |
|---|---|---|
| ADMIN (`admin`) | Administración global e impersonación mediante contexto de empresa. | Consultar datos agregados y administrar la plataforma. Acceso sensible excepcional, con alcance y motivo controlados; mecanismo por definir en DEC-01. |
| Empresa (`company`) | Operación de su empresa. | Administrar únicamente sus recursos y usuarios autorizados; no acceder a otras empresas. |
| Administrador de contrato (`contract_admin`) | Un contrato asignado dentro de una empresa. | Consultar y operar solo donde lo autorice el módulo. Actualmente no tiene acceso a reportes agregados de empresa. |
| Worker | Procesamiento asíncrono y trabajos programados. | Ejecutar tareas con los privilegios necesarios y contexto de empresa cuando corresponda. |
| Beat | Programación periódica de tareas. | Programar ejecuciones; no sustituye al worker que las procesa. |
| Operador de despliegue | Migraciones y configuración. | Usar credenciales separadas del proceso que atiende peticiones. |

**Entidades principales:** empresa, usuario, contrato, trabajador/equipo, requisito, documento/archivo, revisión IA, alerta, evento de calendario, reporte, suscripción/plan, actividad de auditoría, proceso/ejecución e incidente.

La empresa es la unidad de aislamiento. Un documento o archivo debe comprobar su pertenencia antes de emitir acceso. Los identificadores enviados por el navegador no conceden permisos por sí mismos. RUT, documentos personales, credenciales, tokens y contenido de archivos no deben aparecer en resúmenes globales sin necesidad justificada.

**Restricciones actuales:** PostgreSQL y sus funciones/RLS forman parte del comportamiento; SQLite no es un sustituto equivalente. Los adaptadores locales/simulados se distinguen de los productivos. ADMIN mantiene componentes de implementación con nombres internos históricos, aunque la superficie pública sea `/admin`.

## 4. Línea base de evidencia

| Ref. | Fuente | Alcance |
|---|---|---|
| EV-01 | [Validación actual](VALIDACION_ACTUAL.md) | Servicios, navegador, API, build y resultados de pruebas. |
| EV-02 | [Router administrativo](../BASE/app/backend/app/routers/admin.py) | Dashboard, empresas, búsqueda, usuarios y auditoría. |
| EV-03 | [Router de operación administrativa](../BASE/app/backend/app/routers/admin_ops.py) | Clientes comerciales, procesos, sistemas, incidentes e indicadores. |
| EV-04 | [Autorización](../BASE/app/backend/app/deps.py) y [políticas SQL](../BASE/modelo_datos/04_rls.sql) | Roles, alcance y RLS definido. |
| EV-05 | [Navegación administrativa](../BASE/app/frontend/app/ops/layout.tsx) | Secciones públicas `/admin`. |
| EV-06 | [Pruebas ADMIN](../BASE/app/backend/tests/test_admin.py) y [fixtures](../BASE/app/backend/tests/conftest.py) | Suite actualizada y preparación aislada de datos. |
| EV-07 | [Documentos](../BASE/app/backend/app/routers/documentos.py) y [reportes](../BASE/app/backend/app/routers/reportes.py) | Descarga, motivo, exportación y registro de actividad. |
| EV-08 | [Guía de empresa](../README_CLIENTE.md) | Inventario funcional preliminar; debe contrastarse con código y pruebas. |
| EV-09 | Suite backend completa y cambios de demo/Ops del 01-10-2026 | 363 pruebas aprobadas, cero fallidas; base PostgreSQL temporal, con advertencias conocidas del entorno. |
| EV-10 | Asignación de responsables desde Contratos, build frontend del 01-10-2026 | Panel de empresa para asignar cuentas existentes dentro de su tenant a un contrato; build Next.js correcto con 22 rutas. Sin prueba de navegador/API de mutación ni flujo completo de invitación/activación. |

Resultados históricos anteriores a la primera entrega, que no deben sumarse entre sí:

- Suite completa **antes** de actualizar las rutas de pruebas: 270 aprobadas y 24 fallidas, 294 casos.
- Suite focalizada **después** del ajuste: 13 aprobadas y 6 fallidas, 19 casos de ADMIN. No se volvió a ejecutar la suite completa después de ese cambio.
- Fallos de ADMIN en esa ejecución histórica: conversión UF a `numeric` en detalle comercial (1); tarea manual no registrada en `inproc` (5).
- Otros hallazgos de esa ejecución completa histórica: expectativas de esquema 6 frente a 7, contrato de error del motivo de descarga, prueba de aislamiento que omite ese motivo y cinco claves foráneas sin índice según la comprobación existente.
- Frontend compilado correctamente y ocho secciones administrativas recorridas en navegador; las operaciones de modificación sobre los datos actuales no se ejercitaron.

**Primera entrega de código (30-09-2026):** corregidos los seis fallos ADMIN mediante conversión explícita de UF a `numeric` y registro de `worker.ops_tasks` en el arranque API. Las pruebas de motivo e aislamiento se alinean con el comportamiento vigente; `09_indices_consola.sql` incorpora cinco índices y registra esquema 8. **Regresión completa: 295 aprobadas y 0 fallidas, 484,26 s**, incluidos ADMIN 19/19 y esquema 10/10 con migración desde 7 y repetición. Límites y advertencias en EV-01. No se aplicó la migración a la base habitual ni se volvió a recorrer el navegador.

**Validación completa posterior (01-10-2026):** tras integrar compatibilidad para las rutas administrativas documentadas `/api/v1/admin/ops`, estabilizar las pruebas de tendencia en límites de trimestre/mes, incluir empresas aprobadas sin usuarios en el resumen de baja actividad, auditar la creación de faenas sin tenant y evitar atribuciones de impacto empresarial sin evidencia, la suite completa pasó **363/363, 0 fallidas, 551,56 s** (EV-09). Ejecución en contenedor del backend con PostgreSQL temporal y modelo SQL montado; no modifica la base de datos local habitual. Persisten advertencias deprecadas de `datetime.utcnow()`, longitud JWT corta en fixtures, cliente de pruebas y consultas `DISTINCT`; la suite completa no se suma a resultados históricos.

## 5. Requisitos funcionales de ADMIN

Todas las rutas de API de esta sección son relativas a `/api/v1`. Cada requisito hereda los controles de seguridad de la sección 7.

### 5.1 Dashboard global — `/admin/dashboard`

**RF-DAS-01 — Resumen global**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 90 % (propuesta inicial).
- **Fundamento del avance:** Contadores conectados y acreditación calculada; faltan universos y etiquetas acordados.
- **Comportamiento esperado:** ADMIN consulta cantidades de empresas, contratos, trabajadores y usuarios, porcentaje de acreditación y documentos pendientes, próximos a vencer y vencidos.
- **Estado actual:** EV-01/02; `GET /admin/stats` y pantalla operativos. Usuarios excluye administradores. La acreditación usa documentos obligatorios no EMSIPOR de empresas aprobadas; otros contadores pueden tener distinto universo. Empresas aprobadas sin usuarios habilitados aparecen con actividad 0 en `clientes_baja_actividad` (regresión EV-09, 01-10-2026).
- **Pendientes / mejoras:** aclarar el alcance de cada etiqueta y acordar universos de cálculo en DEC-03.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** con datos controlados, cada contador coincide con su universo documentado; denominador cero no causa error; los estados documentales se distinguen; no se incluyen archivos ni identificadores personales innecesarios.


**RF-DAS-02 — Actividad y crecimiento**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Actividad mensual y series existentes; falta precisar el resumen de adopción y su separación de las métricas comerciales. Se conserva el 80 % como estimación previa, pendiente de revisión del equipo.
- **Comportamiento esperado:** ADMIN consulta evolución de empresas, usuarios y actividad de la plataforma. MRR y crecimiento comercial se presentan exclusivamente en Métricas SaaS; crecimiento de adopción no equivale a crecimiento de ingresos.
- **Estado actual:** serie mensual de eventos en dashboard; crecimiento disponible en Métricas. Evidencia EV-01/02/05. La respuesta compartida de stats también contiene MRR; disponer de ese dato en API no demuestra que se muestre en el dashboard.
- **Pendientes / mejoras:** Precisar crecimiento de adopción según DEC-03 y contrastar sus series. Mantener indicadores comerciales fuera de la presentación del dashboard; revisar los consumidores del endpoint compartido antes de modificar su respuesta.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** CA-01: período y universo visibles. CA-02: meses sin actividad representados y valores consistentes entre vistas para la misma definición. CA-03: el dashboard distingue altas/actividad de ingresos y no presenta MRR ni crecimiento comercial. Depende de RF-MET-01 y DEC-03.


### 5.2 Gestión global de empresas — `/admin/empresas`

**RF-EMP-01 — Listado y ficha agregada**

- **Estado técnico:** IV.
- **Prioridad:** P1.
- **Avance estimado:** 100 % (propuesta inicial).
- **Fundamento del avance:** Listado y ficha agregada implementados y recorridos en navegador dentro del alcance de lectura.
- **Comportamiento esperado:** listar empresas con estado, plan, usuarios, contratos, trabajadores, nivel de uso y última actividad; abrir detalle agregado.
- **Estado actual:** EV-01/02; `GET /admin/companies` y `GET /admin/companies/{id}`. Listado y detalle expandible bajo la fila de empresa; el detalle incluye la fecha, acción/módulo, entidad y actor del último evento. RUT/email y descripción libre del evento no se incluyen en esta respuesta operativa.
- **Pendientes / mejoras:** Mantener regresión de permisos, ausencia de plan/actividad y carga completa de páginas. Sin defecto confirmado en el recorrido de lectura probado.
- **Validación:** Listado y ficha dentro del alcance de lectura recorridos en navegador; prueba API del último evento/actor aprobada (`test_admin.py`, 20/20 al 04-10-2026), build web Docker correcto y Next informó `Ready` tras recrear el contenedor. No se completó una comprobación HTTP de la ruta después de ese reinicio. Casos límite y regresión de mantenimiento pendientes.
- **Criterio de aceptación:** la carga mediante `paginarTodo` recupera todas las páginas de API (no implica paginación visual); empresa sin plan o actividad tiene representación explícita; ficha corresponde a la fila elegida; ni listado ni detalle incluyen archivos personales. Una consulta sin ADMIN se rechaza.
- **Límite:** el uso refleja eventos, no tiempo conectado. No equivale al endpoint comercial `/admin/clientes/{id}` de RF-MET-03.


**RF-EMP-02 — Aprobar/rechazar solicitudes**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 85 % (propuesta inicial).
- **Fundamento del avance:** Endpoints, botones y pruebas básicas existentes; faltan transición, auditoría y validación visual integral.
- **Comportamiento esperado:** Aprobar/rechazar solicitudes. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** endpoints, botones y pruebas básicas implementados; falta definir/verificar transiciones y auditoría completa; no se modificaron solicitudes en la comprobación del sistema actual.
- **Pendientes / mejoras:** Endpoints, botones y pruebas básicas existentes; faltan transición, auditoría y validación visual integral. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** sobre fixtures, aprobar habilita el flujo previsto; rechazar registra motivo; una transición no permitida se rechaza; actor y cambio se auditan. Usuario de empresa no puede aprobarse a sí mismo.
- **Dependencia:** RF-AUD-01. Revisar reglas existentes antes de cambiarlas.


### 5.3 Buscador global — `/admin/busqueda`

**RF-BUS-01 — Búsqueda por categoría**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Búsqueda disponible en cinco categorías, filtro de tipo y filtros específicos aplicados en servidor; personas se buscan por RUT. El frontend expone filtros de cargo y tipo de equipo desde catálogos, permite buscar con texto vacío cuando hay filtros específicos y presenta la ficha agregada bajo la fila elegida. Se conserva el 80 % como estimación previa; permisos por categoría y aceptación integral pendientes.
- **Comportamiento esperado:** Búsqueda por categoría. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** `GET /admin/search` acepta `tipo` para consultar empresa, contrato, trabajador/persona, equipo o usuario. Aplica filtros por estado, empresa, cargo, conductor, tipo de equipo, patente, marca, modelo, año, rol y cuenta demo según la categoría. Busca por RUT de empresa y trabajador; las cuentas de acceso no tienen RUT. En la interfaz, los filtros de cargo y tipo de equipo se alimentan de catálogos; se inicia búsqueda con filtros específicos aunque el texto esté vacío y, sin filtros específicos, se exigen al menos dos caracteres. La ficha agregada se expande en la fila concreta seleccionada, muestra resumen y último evento con actor, y solo permite una ficha abierta a la vez. Al cambiar búsqueda/fila o cerrar la ficha, se invalida la solicitud anterior para descartar respuestas tardías. Los usuarios sin empresa siguen excluidos por el join; su alcance depende de DEC-02. EV-01/02.
- **Pendientes / mejoras:** resolver alcance de usuarios globales en DEC-02; validar en navegador la presentación de límites, filtros, expansión/cierre y cambios rápidos de selección; permisos por categoría en RF-BUS-02.
- **Validación:** Parcial: regresión por nombre/cargo con equipos y trabajadores de dos empresas, límites 1/25 y rechazo de empresa/sin sesión en `test_admin_busqueda.py`, 30-09-2026; resultado en EV-01. No acredita permisos granulares ni recorrido en navegador.
- **Validación (04-10-2026):** filtro por categoría, RUT de trabajador, ausencia de RUT en resultados y filtros específicos de empresa, contrato, persona, equipo y usuario: `test_admin_busqueda.py`; compatibilidad del esquema vigente y heredado 10: `test_esquema.py`. Suite focalizada: 34 aprobadas, 0 fallidas; regresión ampliada de administración: 58 aprobadas, 0 fallidas. Compose inició API y web con la base en versión 10; health de esquema devolvió 200. No se recorrió el navegador.
- **Interfaz del buscador (04-10-2026):** revisión del código confirma filtros de cargo/tipo de equipo cargados desde catálogos, búsqueda con texto vacío cuando hay filtros específicos, ficha agregada bajo cada fila y control de una sola ficha abierta. La invalidación por búsqueda, fila y cierre impide aplicar respuestas tardías. Esta actualización documental no añade evidencia de ejecución: el recorrido de navegador queda pendiente en EV-01.
- **Criterio de aceptación:** un equipo no aparece como trabajador; resultados conservan categoría y empresa correctas; búsqueda vacía/corta/larga se valida; los límites no se presentan como un total exhaustivo si no lo son; apertura de ficha vuelve a comprobar permisos.

- **Validación de entradas (30-09-2026):** se rechazan con 422 consultas ausentes, vacías, de un carácter, de solo espacios o de más de 100 caracteres. Tras `strip`, menos de dos caracteres produce `BUSQUEDA_INVALIDA`; el máximo de 100 se aplica al parámetro original. Se prueban límites válidos 2/100 y normalización de espacios. Suite buscador + ADMIN: 32/32; EV-01.

- **Límites de resultados (30-09-2026):** API devuelve `limite_por_categoria` y `hay_mas`, consultando un elemento adicional por categoría y ordenando por nombre/ID. `total` conserva el número de elementos devueltos por compatibilidad; no es un total global. La interfaz muestra «Resultados mostrados», el límite y un aviso para refinar si hay más coincidencias. No se incorpora paginación del buscador. Pruebas y límites de validación en EV-01.


**RF-BUS-02 — Restricciones por información**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 45 % (propuesta inicial).
- **Fundamento del avance:** Rol ADMIN y minimización existentes; falta autorización efectiva por categoría.
- **Comportamiento esperado:** El buscador autoriza cada categoría y su detalle en servidor según capacidades del actor; las etiquetas de permisos devueltas no sustituyen los controles efectivos.
- **Estado actual:** se exige ADMIN y se minimiza la respuesta. Las etiquetas `admin.*.read` no se evalúan como permisos independientes.
- **Pendientes / mejoras:** aplicar en backend la matriz acordada en DEC-01/02.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** un actor sin permiso de categoría no obtiene sus resultados ni su detalle al invocar directamente la API; respuesta no contiene tokens, contraseñas, RUT ni contenido documental. Los permisos se comprueban en cada petición.


### 5.4 Métricas SaaS — `/admin/metricas`

**RF-MET-01 — Definiciones y evolución**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Series e indicadores implementados; faltan definiciones, consistencia de datos y vista de baja actividad.
- **Comportamiento esperado:** ADMIN consulta indicadores de adopción y comerciales en Métricas SaaS con definición, fuente, período y unidad; las cuentas habilitadas se distinguen de usuarios con actividad efectiva.
- **Estado actual:** clientes activos, usuarios habilitados, DAU/WAU, revisiones IA, actividad mensual, MRR y otras series. EV-01/02/03.
- **Pendientes / mejoras:** aprobar diccionario de métricas, revisar semillas/snapshots, normalizar planes `Básico`/`Basico` sin perder relaciones. Mostrar clientes de baja actividad ya calculados.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** cada indicador declara definición, fuente, período y unidad; casos conocidos producen valores esperados; ausencia de snapshot se diferencia de cero; revisiones procesadas no se etiquetan como documentos únicos si se cuentan intentos repetidos. Las series de MRR y crecimiento comercial se presentan en Métricas SaaS. Usuarios habilitados, usuarios con eventos y sesiones vigentes tienen etiquetas y universos diferenciados.
- **Dependencia:** DEC-03/04.


**RF-MET-02 — Sesiones y tiempo de uso**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** Hay estimaciones mediante tokens/eventos; falta resolver alcance y explicar limitaciones.
- **Comportamiento esperado:** ADMIN consulta sesiones vigentes y tiempo estimado con sus límites; solo se presenta tiempo efectivo de uso si existe telemetría acordada y validada según DEC-05.
- **Estado actual:** sesiones vigentes a partir de refresh tokens y duración/uso estimados. No hay medición completa de inicio, actividad e inactividad. La rotación de tokens no equivale a una nueva sesión humana.
- **Pendientes / mejoras:** decidir si mantener estimación o medir sesiones lógicas en DEC-05. Presentar claramente la medida disponible.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** toda estimación se etiqueta y explica; un token expirado no cuenta como vigente. Si se aprueba telemetría real: la rotación no duplica sesiones; cierre, expiración e inactividad obedecen reglas explícitas; dos sesiones simultáneas son distinguibles.


**RF-MET-03 — Detalle comercial y conversión UF**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 85 % (propuesta inicial).
- **Fundamento del avance:** Detalle comercial y conversión UF implementados; defecto SQL corregido y cálculo mensual contrastado. Se conserva el 85 % como estimación previa; faltan metadatos y cobertura adicional.
- **Comportamiento esperado:** ADMIN consulta el detalle comercial y su MRR convertido a CLP con la regla, valor UF y período identificables.
- **Estado actual:** La llamada convierte UF explícitamente a numeric. La prueba comprueba el MRR exacto de 12,5 UF mensuales y empresa inexistente; la suite ADMIN pasa. La respuesta aún no identifica fecha/fuente del valor UF.
- **Pendientes / mejoras:** Identificar fecha/fuente del valor UF y completar casos de período anual, otras monedas y denegación específica del detalle.
- **Validación:** Parcial: defecto corregido y caso mensual/404 aprobados el 30-09-2026 (EV-01, test_cliente_detalle_y_404). No se cierra todo el requisito.
- **Criterio de aceptación:** una suscripción en UF devuelve detalle sin error y MRR según valor UF/período/moneda documentados; se identifica la fecha/fuente del valor aplicado. Se prueba también empresa inexistente y acceso no autorizado.


### 5.5 Alertas y salud — `/admin/salud`, `/admin/sistemas`

**RF-SAL-01 — Riesgos por empresa**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Riesgos documentales y bandeja existentes; faltan inactividad, totales completos y casos sin datos.
- **Comportamiento esperado:** Riesgos por empresa. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** baja acreditación (<70%), contratos con al menos 3 pendientes/vencidos, vencidos por empresa, morosidad y bandeja. Listado de contratos limitado a 25 y alertas a 50 en stats. El cálculo de baja actividad excluye empresas con cero usuarios habilitados mediante if int(f.usuarios); no excluye necesariamente a empresas con usuarios habilitados sin eventos. La bandeja representa la lista recibida, con límite de 50, y usa su longitud como cantidad visible.
- **Pendientes / mejoras:** Incluir explícitamente empresas sin usuarios habilitados y distinguirlas de empresas sin actividad reciente. Definir totales, paginación y filtros de la bandeja; no etiquetar longitud de una muestra como total global. Acordar umbrales/ventana en DEC-04 y tratar separadamente empresas sin documentos.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** casos justo por debajo/en/encima del umbral se clasifican correctamente; cliente sin datos se distingue de cliente sano; totales globales no se derivan de listas truncadas; ventana de inactividad visible. Probar una empresa aprobada sin usuarios habilitados y otra con usuarios habilitados sin eventos: ninguna se omite silenciosamente y cada una tiene clasificación explícita. Con más de 50 alertas, el total corresponde a todos los resultados autorizados y se puede recuperar el resto mediante el mecanismo de navegación acordado.


**RF-SAL-02 — Estado operacional verificable**

- **Estado técnico:** COR.
- **Prioridad:** P1.
- **Avance estimado:** 55 % (propuesta inicial).
- **Fundamento del avance:** Panel, heartbeat y caducidad existen; sondas insuficientes para acreditar disponibilidad real.
- **Comportamiento esperado:** Estado operacional verificable. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** existen heartbeat, panel y caducidad de lectura/TTL; falta validar esa caducidad ante fallos; la sonda de API no consulta realmente la API y la de workers usa profundidad de cola. Worker/Beat no tienen healthcheck de proceso habilitado en Compose. El panel marca impacto empresarial como `indeterminado` y deja la lista de empresas afectadas vacía cuando no hay una relación verificable; estado operativo informa alcance `ninguno` (EV-09).
- **Pendientes / mejoras:** Panel, heartbeat y caducidad existen; sondas insuficientes para acreditar disponibilidad real. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** API inaccesible se detecta aunque el worker siga funcionando; cola vacía no certifica worker activo; heartbeat vencido muestra estado no verificable o caído según regla documentada; latencia sin fuente no se presenta como medida real.
- **Dependencia:** RNF-OPE-01; tiempos objetivo por decidir en DEC-07.


**RF-SAL-03 — Procesos e incidentes**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Catálogo, acciones e incidentes implementados; el arranque API ya registra la tarea manual y los 19 casos ADMIN pasan. Se conserva la estimación del 80 % hasta completar los recorridos pendientes.
- **Comportamiento esperado:** ADMIN consulta procesos, ejecuta trabajos manuales, pausa/reanuda los permitidos y gestiona incidentes con actor y resultado trazables.
- **Estado actual:** Corregido el registro de ops_ejecutar_run mediante importación de worker.ops_tasks en main.py. Ejecuciones inproc llegan a estado final; pasan pausa, conflicto de ejecución, snapshots y auditoría de la suite ADMIN. La pantalla de salud declara que informa alcance global del componente y no mapea afectación específica por empresa; no se confirmó que marque individualmente a todas las empresas aprobadas como afectadas.
- **Pendientes / mejoras:** Validar el recorrido real API→Redis→worker Celery, errores de ejecución y mutaciones en navegador. Precisar reintentos/historial según cronograma y DEC-06 para afectación por empresa.
- **Validación:** Parcial: ADMIN 19/19 en entorno aislado con inproc, 30-09-2026, EV-01. No acredita el recorrido distribuido Celery.
- **Criterio de aceptación:** ejecución llega a estado final y conserva actor; una ejecución incompatible concurrente se rechaza; pausa requiere motivo; proceso continuo no se pausa como cron; cierre de incidente requiere resolución; acciones quedan auditadas. Sin vínculo verificable incidente→empresa, presentar impacto global/no determinado; no atribuir afectación individual automáticamente a todas las empresas aprobadas. Si DEC-06 incorpora el mapeo, registrar y probar las empresas realmente asociadas.
- **Alcance:** validar modo local `inproc` y recorrido Celery por separado. La afectación específica por empresa no está implementada; no inferirla del estado global. DEC-06 define su alcance futuro.


### 5.6 Usuarios, roles y permisos — `/admin/usuarios`

**RF-USU-01 — Ciclo de vida desde la consola**

**Identificación de cuentas (30-09-2026):** listado y respuestas de modificación de usuarios exponen correo real únicamente bajo autorización ADMIN. La interfaz muestra nombre y correo, o «Sin nombre registrado» junto al correo, y permite filtrar por ambos. Las confirmaciones de revocación/reactivación incluyen correo. Este dato es necesario para identificar al destinatario de los permisos; no se modifica la minimización del buscador global.

- **Registro y perfil (05-10-2026):** el registro solicita el nombre completo del usuario que crea la cuenta, distinto de la razón social, y lo persiste en `users.nombre`. La sección autenticada «Mi perfil» permite cambiar nombre, correo y contraseña; el cambio de contraseña exige la actual. Usa `/auth/me`, sin cambio de esquema.
- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 65 % (propuesta inicial).
- **Fundamento del avance:** Listado, edición, revocación y botón de reactivación implementados; se conserva 65 % hasta completar altas, navegación y validación visual.
- **Comportamiento esperado:** Ciclo de vida desde la consola. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** botón Reactivar para cuentas revocadas, con confirmación y bloqueo durante la petición; usa PATCH administrativo con `activo=true`. Conserva rol/alcance y exige nuevo login: revocar o cambiar activo desde ADMIN incrementa `auth_version` y revoca refresh tokens. La autenticación rechaza JWT de versiones previas. Esquema 9, probado en base temporal; pendiente aplicar al entorno habitual. Se solicitan 100 usuarios sin paginación visible.
- **Pendientes / mejoras:** completar altas y navegación de más de 100 usuarios; validar reactivación en navegador y auditoría integral. Extender invalidación uniforme a los demás mecanismos de desactivación/cambio de credenciales; esta entrega cubre operaciones ADMIN. Reactivar no aprueba solicitudes pendientes o rechazadas.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** crear/invitar según el flujo existente, listar más de 100 usuarios sin omisiones, revocar y reactivar con autorización; no exponer contraseñas/tokens; cuentas revocadas no acceden a API ni renuevan sesión. Reutilizar reglas de empresa cuando correspondan.

- **Evidencia de reactivación (30-09-2026):** `test_admin_reactivacion.py` verifica revocación por POST y PATCH, bloqueo durante desactivación, rechazo de JWT/refresh anteriores tras reactivar, nuevo login/refresh funcionales y denegación sin ADMIN. Migración 8→9 e idempotencia en `test_esquema.py`; build frontend y resultados en EV-01.


**RF-USU-02 — Coherencia de alcance**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Backend valida alcance; falta edición coherente en interfaz y guardas acordadas.
- **Comportamiento esperado:** Coherencia de alcance. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** roles `admin`, `company`, `contract_admin`; backend valida contrato perteneciente a empresa. Los selects separados pueden enviar combinaciones inválidas que el backend rechaza; no se demostró persistencia de alcance inconsistente.
- **Pendientes / mejoras:** Backend valida alcance; falta edición coherente en interfaz y guardas acordadas. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** guardar rol/empresa/contrato como combinación válida; rechazo no deja cambios parciales; el usuario recibe su alcance efectivo vigente en la siguiente petición; no puede adquirir permisos de otra empresa manipulando headers o cuerpo. Guardas contra pérdida del último administrador según DEC-01.


### 5.7 Auditoría — `/admin/auditoria`

**RF-AUD-01 — Cambios administrativos**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 55 % (propuesta inicial).
- **Fundamento del avance:** Actividad registrada parcialmente; faltan valores anteriores/nuevos y actores sin empresa.
- **Comportamiento esperado:** Registrar cambios administrativos y de catálogos con actor, objeto, operación, alcance, fecha y resultado, incluyendo administradores sin empresa y distinguiendo eliminación, desactivación y actualización.
- **Estado actual:** actividad de negocio y cambios de usuarios registrados parcialmente. La creación de faenas globales ahora inserta un evento persistente `admin_catalogo` con actor, entidad y empresa `Plataforma`, y `/admin/audit` incluye eventos sin tenant mediante `outer join` (regresión EV-09). Cambios de permisos todavía no guardan valores anteriores/nuevos de forma integral. En contratos.py, el borrado físico registra tipo `actualizacion` con descripción de eliminación. Estas brechas de semántica y cobertura siguen abiertas.
- **Pendientes / mejoras:** Inventariar operaciones de plataformas, plantillas y demás catálogos; incorporar las que solo generan logs. Corregir semántica de eliminación sin confundir borrado lógico con físico; añadir valores anterior/nuevo y cubrir otras acciones globales sin tenant.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** CA-01: altas, cambios de permisos y desactivación/reactivación conservan actor, destinatario, fecha UTC, resultado y alcance anterior/nuevo. CA-02: el catálogo acordado de operaciones administrativas genera eventos persistentes consultables, incluidos actores sin empresa. CA-03: eliminar un contrato se identifica como eliminación, y desactivar una plantilla como desactivación, mediante operación/código inequívoco; la descripción no es el único discriminador. CA-04: no se registran secretos y se aplican los controles de RNF-PRV-01.


**RF-AUD-02 — Historial de autenticación**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 25 % (propuesta inicial).
- **Fundamento del avance:** Último acceso y tokens aportan una base; falta historial completo de autenticación.
- **Comportamiento esperado:** Conservar un historial consultable de autenticación, cierre y revocación sin sobrescribir eventos anteriores al actualizar last_login_at.
- **Estado actual:** `last_login_at` y refresh tokens; no hay historial explícito completo de ingresos/salidas.
- **Pendientes / mejoras:** Último acceso y tokens aportan una base; falta historial completo de autenticación. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** registrar ingreso exitoso, fallo de autenticación sin revelar existencia de cuenta al solicitante, cierre y revocación, con correlación de sesión y resultado; no registrar tokens o contraseñas. Retención y acceso al historial dependen de DEC-08.


**RF-AUD-03 — Acceso sensible y exportaciones**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** URL documental con motivo y actividad de exportación existentes; faltan uniformidad y acceso excepcional.
- **Comportamiento esperado:** Acceso sensible y exportaciones. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** emisión de URL documental exige motivo de 12–240 caracteres y registra actor/fecha/archivo. Reportes y exportaciones tienen controles y actividad, pero no una justificación uniforme. EV-07. GET /documentos/{doc_id} aplica pertenencia/alcance mediante _get_doc, pero no exige motivo ni registra la lectura de metadatos en el handler revisado. La ausencia de auditoría no equivale a ausencia de autorización.
- **Pendientes / mejoras:** Clasificar metadatos sensibles en DEC-08 y fijar permisos/motivos según DEC-01. Auditar sus lecturas cuando corresponda; completar justificación de exportaciones y acceso excepcional. Conservar el contrato de motivo DEC-09 y la prueba cruzada aprobada.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** autorización y pertenencia se validan antes de emitir URL; acceso excepcional ADMIN registra quién, cuándo, a qué y por qué. Descarga/exportación denegada no emite URL. Auditoría diferencia solicitud de URL de transferencia efectiva; si se requiere acreditar descarga real, integrar eventos del almacenamiento según DEC-08. Para los metadatos clasificados como sensibles en DEC-08: acceso autorizado y motivo cuando la matriz lo exija, registro de actor/fecha/recurso/resultado y rechazo sin datos para actores no autorizados. No se exige indiscriminadamente motivo para toda consulta ordinaria.


### 5.8 Seguridad y aislamiento funcional

**RF-SEG-01 — Aislamiento por empresa/contrato**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 65 % (propuesta inicial).
- **Fundamento del avance:** Filtros, dependencias y RLS definidos; faltan roles reales y pruebas cruzadas completas.
- **Comportamiento esperado:** Aislamiento por empresa/contrato. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** filtros de aplicación, dependencias y políticas RLS. Parte de las pruebas de aislamiento pasa, pero API/worker del Compose actual usan superusuario PostgreSQL, evitando RLS. Las políticas revisadas en 04_rls.sql se basan en empresa/ADMIN; el alcance contractual se comprueba principalmente en la API. No se identificó una política RLS independiente por contrato en los scripts revisados.
- **Pendientes / mejoras:** Separar roles de BD y completar pruebas por empresa/contrato. Resolver en DEC-10 si se añade defensa contractual en RLS y cómo propagar su contexto a API/worker; no presentar esa capa como implementada.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** con empresas A/B y dos contratos de A, probar listado, detalle, modificación, borrado, archivos y exportación; actor de B no accede a A y administrador de un contrato no accede al otro. Aplicación conecta sin superusuario ni BYPASSRLS. Pruebas usan credenciales equivalentes a despliegue. Si DEC-10 incorpora RLS contractual, comprobar también mediante SQL directo con el rol de aplicación que A1 no puede leer ni modificar A2, incluso sin filtros explícitos de API.
- **Nota:** para recursos ajenos se mantiene la respuesta de no existencia donde el contrato actual lo establece; no filtrar metadatos en mensajes de error.


**RF-SEG-02 — Mínimo privilegio y acceso excepcional ADMIN**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 30 % (propuesta inicial).
- **Fundamento del avance:** Agregados minimizados existentes; falta flujo de privilegio excepcional limitado.
- **Comportamiento esperado:** ADMIN opera con permisos por capacidad y alcance; el acceso sensible excepcional requiere autorización y motivo, sin que seleccionar una empresa conceda por sí mismo acceso ilimitado.
- **Estado actual:** agregados minimizados, pero ADMIN puede seleccionar contexto de empresa y conserva privilegio global. No hay un flujo excepcional completo.
- **Pendientes / mejoras:** Agregados minimizados existentes; falta flujo de privilegio excepcional limitado. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** acceso sensible exige permiso específico, motivo y alcance temporal/recurso según DEC-01; toda concesión y utilización se audita; la autorización se verifica en servidor; el dashboard no necesita descargar documentos personales.


**RF-SEG-03 — Autenticación y despliegue sin credenciales demo**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 50 % (propuesta inicial).
- **Fundamento del avance:** Login, refresh y rechazo por rol comprobados; añadidos controles de configuración y semillas opt-in. Se conserva el 50 % previo hasta validar despliegue y recuperación real.
- **Comportamiento esperado:** Autenticación y despliegue sin credenciales demo. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** `APP_ENV=production` rechaza JWT dev-* o menor de 32 bytes sin espacios exteriores, semillas demo, tokens de recuperación en respuestas, RLS desactivado y migraciones al arranque. Semillas y exposición de token quedan desactivadas por defecto; Compose local activa solo semillas explícitamente. El handler comprueba además que no sea producción antes de devolver `_dev_token`. Errores de configuración ocultan valores de entrada.
- **Pendientes / mejoras:** Separar roles BD reales, aprovisionar administrador/catálogos productivos sin semillas demo, gestionar secretos y cuentas existentes y validar entrega de correo. El Compose y su overlay ngrok siguen siendo de demostración; el modo seguro requiere `APP_ENV=production` explícito. No se aplicaron cambios al entorno habitual.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** despliegue público rechaza configuración de secreto de desarrollo, no crea cuentas con claves conocidas y no devuelve tokens de recuperación en respuestas; semillas demo requieren activación explícita; flujo de recuperación productivo se valida con el canal acordado.

- **Evidencia PT-03-01:** pruebas de configuración inválida, arranque sin semillas, guardas de siembra y respuesta de recuperación opaca en `test_config_seguridad.py`; regresión de autenticación/aislamiento en EV-01, 30-09-2026. Es validación aislada, no prueba de despliegue público.

## 6. Portal de empresa: inventario inicial de requisitos

Esta sección requiere profundización posterior. Las fuentes principales son EV-08, routers de empresa y suites existentes. Todos los flujos heredan RF-SEG-01; ADMIN excepcional requiere RF-SEG-02. Los criterios siguientes son mínimos de trabajo, no una afirmación de cumplimiento completo.

**RF-CLI-01 — Registro, login, recuperación y perfil**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Registro, login, recuperación y perfil; router `auth.py`, `test_auth.py`; login/lectura comprobados. Implementar entrega real del correo de recuperación pendiente en auth.py; validar revocación y recorrido completo.
- **Comportamiento esperado:** Registro, login, recuperación y perfil.
- **Estado actual:** Registro, login, recuperación y perfil; router `auth.py`, `test_auth.py`; login/lectura comprobados. Implementar entrega real del correo de recuperación pendiente en auth.py; validar revocación y recorrido completo.
- **Pendientes / mejoras:** Implementar entrega real del correo de recuperación pendiente en auth.py; validar revocación y recorrido completo.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Registro pasa por aprobación; credenciales inválidas y cuentas desactivadas se rechazan; recuperación y cambio de clave revocan lo previsto; completar prueba del canal real de entrega.

**RF-CLI-02 — Contratos y requisitos**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 90 % (propuesta inicial).
- **Fundamento del avance:** Contratos y requisitos; routers `contratos.py`, `contrato_requisitos.py`, `test_contratos.py`. Validar alta/edición visual, fechas inválidas y reglas del checklist.
- **Comportamiento esperado:** Contratos y requisitos.
- **Estado actual:** Contratos y requisitos; routers `contratos.py`, `contrato_requisitos.py`, `test_contratos.py`.
- **Pendientes / mejoras:** Validar alta/edición visual, fechas inválidas y reglas del checklist.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** CRUD respeta pertenencia y alcance, fechas válidas y reglas de checklist; comprobar el recorrido visual de alta/edición y datos inválidos.

**RF-CLI-03 — Personal/equipos y expedientes**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 90 % (propuesta inicial).
- **Fundamento del avance:** Personal/equipos y expedientes; `sujetos.py`, `test_sujetos.py`. Validar formularios, tipos y aislamiento de personal y equipos en interfaz.
- **Comportamiento esperado:** Personal/equipos y expedientes.
- **Estado actual:** Personal/equipos y expedientes; `sujetos.py`, `test_sujetos.py`.
- **Pendientes / mejoras:** Validar formularios, tipos y aislamiento de personal y equipos en interfaz.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Tipos y validaciones correctos, detalle del sujeto elegido, mutaciones aisladas; no mezclar trabajador con equipo; cubrir interfaz además de API.

**RF-CLI-04 — Carga documental y revisión IA**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Carga documental y revisión IA; `documentos.py`, `ia.py`, `test_documentos.py`. Verificar almacenamiento, límites y URLs; distinguir IA simulada de integración real.
- **Comportamiento esperado:** Carga documental y revisión IA.
- **Estado actual:** Carga documental y revisión IA; `documentos.py`, `ia.py`, `test_documentos.py`.
- **Pendientes / mejoras:** Verificar almacenamiento, límites y URLs; distinguir IA simulada de integración real.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Validar extensión/tamaño, confirmar solo archivo propio, controlar motivo y firma/caducidad de descarga, estados de revisión coherentes. Modo simulado claramente identificado; integración real pendiente de validar.

**RF-CLI-05 — Alertas y dashboard de empresa**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 85 % (propuesta inicial).
- **Fundamento del avance:** Alertas y dashboard de empresa; `alertas.py`, `dashboard.py`, `test_operacion.py`. Contrastar KPI, filtros y transiciones con datos de empresa y contrato.
- **Comportamiento esperado:** Alertas y dashboard de empresa.
- **Estado actual:** Alertas y dashboard de empresa; `alertas.py`, `dashboard.py`, `test_operacion.py`.
- **Pendientes / mejoras:** Contrastar KPI, filtros y transiciones con datos de empresa y contrato.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** KPI coincide con datos del actor; filtros y transiciones de alertas correctos; administrador de contrato no recibe agregados ajenos.

**RF-CLI-06 — Calendario mensual y eventos manuales**

- **Estado técnico:** ISV.
- **Prioridad:** P2.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Calendario mensual y eventos manuales; `calendario.py`, página `/calendario`. Verificar zona horaria, permisos y vencimientos proyectados.
- **Comportamiento esperado:** Calendario mensual y eventos manuales.
- **Estado actual:** Calendario mensual y eventos manuales; `calendario.py`, página `/calendario`.
- **Pendientes / mejoras:** Verificar zona horaria, permisos y vencimientos proyectados.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Alta/edición/borrado de eventos propios, filtro de fechas/categorías; vencimientos proyectados no se modifican como eventos manuales; comprobar zona horaria y alcance de contrato.

**RF-CLI-07 — Reportes/exportación**

- **Estado técnico:** ISV.
- **Prioridad:** P1.
- **Avance estimado:** 90 % (propuesta inicial).
- **Fundamento del avance:** Reportes/exportación; `reportes.py`, `test_reportes.py`. Completar recorrido de generación, fallos y descarga por actor.
- **Comportamiento esperado:** Reportes/exportación.
- **Estado actual:** Reportes/exportación; `reportes.py`, `test_reportes.py`.
- **Pendientes / mejoras:** Completar recorrido de generación, fallos y descarga por actor.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Job finaliza o informa fallo, formato y filtros correctos, descarga autorizada/temporal; administrador de contrato no obtiene reporte global de empresa.

**RF-CLI-08 — Perfil y usuarios de empresa**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta de seguimiento al 01-10-2026; pendiente de revisión del equipo).
- **Fundamento del avance:** Perfil y APIs para usuarios existentes; `company.py`, `test_operacion.py`. Se agregó panel en Contratos para asignar cuentas existentes de la misma empresa como responsables `contract_admin`. El build frontend pasó; invitación con envío/canje de activación y validación visual/operacional siguen pendientes.
- **Comportamiento esperado:** Perfil y usuarios de empresa.
- **Estado actual:** `/contratos` incluye el panel `Responsables de contrato`, visible a cuentas `company`. Consulta contratos y usuarios del tenant por las APIs existentes y permite asignar o liberar el alcance de `contract_admin`; el servidor valida pertenencia del contrato a la empresa. Convertir una cuenta `company` a `contract_admin` le quita acceso general. El cambio de vista compiló, pero no se recorrió con mutaciones reales. La invitación backend crea usuario y token de activación, pero no envía el token ni existe un flujo frontend completo para canjearlo.
- **Pendientes / mejoras:** Crear sección de usuarios/invitaciones o completar el flujo desde Contratos; enviar invitación por un canal configurado, permitir establecer contraseña mediante token de un solo uso y expirar/revocar tokens. Validar gestión, auditoría, permisos y asignación en navegador/API; identificar responsable real sin tratar una cuenta demo como persona verificada.
- **Validación:** Parcial. EV-10 acredita build frontend y revisión de integración. No acredita envío/canje de activación, mutaciones desde navegador, prueba de permisos cruzados ni aceptación del cliente.
- **Criterio de aceptación:** Invitar con nombre/correo individual; asignar `company` o `contract_admin` con contrato perteneciente a la empresa; enviar y canjear activación de un solo uso; auditar actor/fecha/cambio; permitir revocar o reasignar sin perder al último usuario `company` activo. Probar que una empresa no enumera ni modifica cuentas de otra y que `contract_admin` queda limitado al contrato asignado.

**RF-CLI-09 — Integraciones, credenciales y notificaciones**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 45 % (propuesta inicial).
- **Fundamento del avance:** Integraciones, credenciales y notificaciones; routers/servicios existentes, `test_vault.py`. Inventariar conectores y completar canales reales acordados; distinguir configuración, simulación e integración.
- **Comportamiento esperado:** Integraciones, credenciales y notificaciones.
- **Estado actual:** Integraciones, credenciales y notificaciones; routers/servicios existentes, `test_vault.py`.
- **Pendientes / mejoras:** Inventariar conectores y completar canales reales acordados; distinguir configuración, simulación e integración.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Documentar por conector si es simulado/configurado/real; verificar cifrado, rol de lectura de secretos, reintentos y errores sin exponer credenciales. No declarar integración productiva solo por seeds.

## 7. Requisitos no funcionales

**RNF-SEG-01 — Seguridad de infraestructura**

**Entrega PT-03-02 (30-09-2026):** API y Celery registran una guarda en las conexiones nuevas en producción. Rechaza superusuario, BYPASSRLS, CREATEDB, CREATEROLE y propiedad de tablas de public, incluidas membresías. La espera de BD propaga el rechazo sin reintentar como si fuera indisponibilidad. El comando de migración no instala esta guarda. No sustituye comprobaciones de políticas RLS ni aprovisiona identidades; el Compose sigue usando superusuario en desarrollo.

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 55 % (propuesta inicial).
- **Fundamento del avance:** Compose usa superusuario; políticas existen. Validar con roles reales y pruebas negativas de consulta directa. Depende de RF-SEG-01/03.
- **Comportamiento esperado:** Separar migración, API y worker; RLS efectivo; secretos externos a código/configuración pública; privilegio mínimo sobre credenciales.
- **Estado actual:** Compose usa superusuario; políticas existen. Validar con roles reales y pruebas negativas de consulta directa. Depende de RF-SEG-01/03.
- **Pendientes / mejoras:** Separar credenciales de migración/API/worker, verificar NOBYPASSRLS y proteger secretos. Definir en DEC-10 el contexto y políticas contractuales; probar reutilización de conexiones sin arrastre de alcance.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Separar migración, API y worker; RLS efectivo; secretos externos a código/configuración pública; privilegio mínimo sobre credenciales. Compose usa superusuario; políticas existen. Validar con roles reales y pruebas negativas de consulta directa. Depende de RF-SEG-01/03.

**RNF-PRV-01 — Privacidad**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 50 % (propuesta inicial).
- **Fundamento del avance:** Existen respuestas agregadas minimizadas, pero falta controlar PII incrustada en descripciones y comprobar todos los consumidores; se conserva el 50 % como estimación de gestión previa.
- **Comportamiento esperado:** Minimizar datos personales en respuesta y logs; redactar secretos; definir retención y acceso a auditoría.
- **Estado actual:** La minimización es parcial. company.py incluye emails en descripciones de invitación y modificación de usuarios; admin.py devuelve descripciones en actividad/auditoría. Esto acredita presencia de PII, no una fuga entre empresas o a actores no autorizados. Retención y campos necesarios pendientes de DEC-08.
- **Pendientes / mejoras:** Clasificar campos y destinatarios; minimizar o redactar PII innecesaria en textos libres, feeds, logs y exportaciones. Revisar registros históricos y definir tratamiento/retención sin modificar indiscriminadamente la trazabilidad existente.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** CA-01: cada vista y exportación expone únicamente los datos necesarios según rol. CA-02: descripciones con email/RUT/secretos de prueba no revelan información prohibida al consumidor, tampoco incrustada en texto libre. CA-03: acceso al registro y retención siguen DEC-08. CA-04: el tratamiento de registros históricos se documenta y respeta su integridad. No se presume una obligación legal específica.

**RNF-REP-01 — Reproducibilidad**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** Frontend tiene lockfile, pero Docker instala sin copiarlo; backend usa rangos abiertos. Build limpio debe usar dependencias fijadas y registro de versiones; evaluar aviso npm sobre Next.js antes de despliegue.
- **Comportamiento esperado:** Construcciones reproducibles y control de dependencias.
- **Estado actual:** Frontend tiene lockfile, pero Docker instala sin copiarlo; backend usa rangos abiertos. Build limpio debe usar dependencias fijadas y registro de versiones; evaluar aviso npm sobre Next.js antes de despliegue.
- **Pendientes / mejoras:** Frontend tiene lockfile, pero Docker instala sin copiarlo; backend usa rangos abiertos. Build limpio debe usar dependencias fijadas y registro de versiones; evaluar aviso npm sobre Next.js antes de despliegue.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Construcciones reproducibles y control de dependencias. Frontend tiene lockfile, pero Docker instala sin copiarlo; backend usa rangos abiertos. Build limpio debe usar dependencias fijadas y registro de versiones; evaluar aviso npm sobre Next.js antes de despliegue.

**RNF-VAL-01 — Validación repetible**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Existe suite aislada con PostgreSQL; corregidos los fallos conocidos de ADMIN, esquema y parámetros documentales. Se conserva 75 %; quedan extensiones reales y automatización.
- **Comportamiento esperado:** Suite actualizada, aislada y repetible; no debilitar aserciones para ocultar defectos.
- **Estado actual:** Pruebas alineadas con esquema 8; se conservan controles de autorización y se verifica importe UF exacto. Nueva prueba de actualización 7→8 e idempotencia. Consultar resultado de regresión completa en EV-01.
- **Pendientes / mejoras:** Validar con citext/pg_trgm reales y automatizar ejecución con versión de código, entorno e informe identificables; cubrir los escenarios funcionales todavía abiertos.
- **Validación:** Parcial: resultados de ejecución en EV-01; los límites del fixture y la cobertura funcional permanecen abiertos.
- **Criterio de aceptación:** La suite se ejecuta de forma aislada y repetible sobre la versión entregada; las pruebas del alcance aceptado pasan sin debilitar aserciones; se verifican extensiones reales y se conserva informe por caso con versión y entorno.

**RNF-PER-01 — Rendimiento**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 40 % (propuesta inicial).
- **Fundamento del avance:** Revisar consultas por fila y listas truncadas. Objetivo de latencia/concurrencia pendiente DEC-07; no se declara SLA sin medición.
- **Comportamiento esperado:** Listados paginados, totales coherentes y tiempos medidos con volumen representativo.
- **Estado actual:** Revisar consultas por fila y listas truncadas. Objetivo de latencia/concurrencia pendiente DEC-07; no se declara SLA sin medición.
- **Pendientes / mejoras:** Revisar consultas por fila y listas truncadas. Objetivo de latencia/concurrencia pendiente DEC-07; no se declara SLA sin medición.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Listados paginados, totales coherentes y tiempos medidos con volumen representativo. Revisar consultas por fila y listas truncadas. Objetivo de latencia/concurrencia pendiente DEC-07; no se declara SLA sin medición.

**RNF-OPE-01 — Operación observable**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** `/health` y esquema operativos; sondas parciales. Probar caída API, worker y BD en entorno aislado; registrar recuperación.
- **Comportamiento esperado:** Salud distingue proceso vivo, BD disponible y capacidad de ejecutar tareas; fallos/reintentos observables.
- **Estado actual:** `/health` y esquema operativos; sondas parciales. Probar caída API, worker y BD en entorno aislado; registrar recuperación.
- **Pendientes / mejoras:** `/health` y esquema operativos; sondas parciales. Probar caída API, worker y BD en entorno aislado; registrar recuperación.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Salud distingue proceso vivo, BD disponible y capacidad de ejecutar tareas; fallos/reintentos observables. `/health` y esquema operativos; sondas parciales. Probar caída API, worker y BD en entorno aislado; registrar recuperación.

**RNF-REC-01 — Respaldo y restauración**

- **Estado técnico:** PEN.
- **Prioridad:** P1.
- **Avance estimado:** 0 % (propuesta inicial).
- **Fundamento del avance:** No hay componentes de recuperación acreditados; 0 % provisional del alcance documentado, revisable ante evidencia adicional.
- **Comportamiento esperado:** Respaldo y restauración de BD, archivos y claves coordinados.
- **Estado actual:** No se identificó implementación de respaldo/restauración ni evidencia de restauración ejecutada en la revisión. Un volumen persistente no acredita recuperación; puede existir operación externa no aportada.
- **Pendientes / mejoras:** No hay evidencia de restauración ejecutada en esta revisión. Definir RPO/RTO en DEC-07 y demostrar recuperación de un archivo cifrado/relacionado con su registro.
- **Validación:** No realizada: no se aportó restauración ejecutada.
- **Criterio de aceptación:** Respaldo y restauración de BD, archivos y claves coordinados. No hay evidencia de restauración ejecutada en esta revisión. Definir RPO/RTO en DEC-07 y demostrar recuperación de un archivo cifrado/relacionado con su registro.

**RNF-UX-01 — Experiencia de usuario**

- **Estado técnico:** ISV.
- **Prioridad:** P2.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Navegación de escritorio comprobada parcialmente; revisión responsive/accesibilidad pendiente, sin declarar conformidad formal.
- **Comportamiento esperado:** Formularios con errores legibles, navegación por teclado, etiquetas, estados de carga/vacío/error y adaptación móvil.
- **Estado actual:** Navegación de escritorio comprobada parcialmente; revisión responsive/accesibilidad pendiente, sin declarar conformidad formal.
- **Pendientes / mejoras:** Navegación de escritorio comprobada parcialmente; revisión responsive/accesibilidad pendiente, sin declarar conformidad formal.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Formularios con errores legibles, navegación por teclado, etiquetas, estados de carga/vacío/error y adaptación móvil. Navegación de escritorio comprobada parcialmente; revisión responsive/accesibilidad pendiente, sin declarar conformidad formal.

## 8. Diccionario inicial de métricas

| Término | Interpretación actual | Aclaración requerida |
|---|---|---|
| Empresa aprobada | Estado de cuenta `approved`. | No equivale necesariamente a cliente pagador o activo. |
| Cliente activo | Empresa aprobada con suscripción activa o trial en stats. | Acordar tratamiento de otros estados. |
| Usuario habilitado | Cuenta con `activo=true`, excluyendo ADMIN en ciertos contadores. | No equivale a actividad reciente. |
| DAU / WAU | Usuarios distintos con eventos de actividad en la ventana. | Acordar zona horaria, inclusión de ADMIN y eventos automáticos. |
| Acreditación global | Documentos obligatorios correctos / total elegible, excluyendo EMSIPOR y sobre empresas aprobadas. | Mostrar universo y diferencia frente a promedio simple por empresa. |
| Pendiente / por vencer / vencido | Estados `falta`, `porvenc`, `venc`. | En riesgo contractual se agrupan falta y vencido: etiquetarlo. |
| Documento procesado | Actualmente se cuentan revisiones IA. | Decidir si se quiere documento único, versión o ejecución. |
| Sesión vigente | Refresh token no revocado y no expirado. | No mide presencia online ni sesión humana única. |
| Tiempo de uso | Intervalo agregado entre eventos; duración basada en ciclo de tokens. | Estimación con limitaciones, no tiempo efectivo de interacción. |
| MRR | Ingreso mensual recurrente calculado por reglas comerciales y snapshots. | Fuente/fecha UF, descuentos y datos demo deben documentarse. |

## 9. Decisiones pendientes

Responsables propuestos: responsable de producto para reglas de negocio; responsable técnico para arquitectura; responsable de operación para objetivos de servicio. Los nombres y fechas se asignarán al iniciar cada entrega.

| ID | Decisión | Propuesta inicial, no aprobada | Bloquea |
|---|---|---|---|
| DEC-01 | Permisos ADMIN y acceso excepcional. | Agregados por defecto; permiso sensible separado, motivo y duración acotada; definir guardas del último ADMIN. | RF-BUS-02, RF-USU-02, RF-SEG-02, auditoría asociada. |
| DEC-02 | Alcance del buscador. | Mantener cinco categorías; incluir administradores solo con permiso correspondiente; ficha sin documentos. | RF-BUS-01/02. |
| DEC-03 | Universo/período de métricas. | Separar habilitado de activo; explicar denominadores y zona horaria. Dashboard: actividad/adopción; Métricas SaaS: MRR y crecimiento comercial. Esta distribución se incorpora en v0.7; universos pendientes. | Dashboard y RF-MET-01. |
| DEC-04 | Riesgos e inactividad. | Usar 70%, 3 documentos y 30 días como base de discusión; definir sin datos y umbrales configurables si se necesitan. | RF-SAL-01 y baja actividad. |
| DEC-05 | Medición de sesión. | Mantener estimaciones visibles en primera entrega; telemetría real como entrega posterior si se requiere. | Alcance final RF-MET-02. |
| DEC-06 | Incidentes por empresa. | Mantener global claramente etiquetado hasta contar con vínculo real de afectación. | Ampliación de salud por cliente. |
| DEC-07 | Rendimiento, disponibilidad y recuperación. | Medir línea base antes de fijar percentiles, carga, tiempos de detección, RPO y RTO. | Aceptación cuantitativa de RNF-PER/OPE/REC. |
| DEC-08 | Auditoría y privacidad. | Clasificar metadatos sensibles, PII necesaria por destinatario y textos libres; acordar retención, motivos por operación, tratamiento histórico y necesidad de acreditar transferencia real. | RNF-PRV-01, RF-AUD-02/03. |
| DEC-09 | Error de motivo documental inválido. | Compatibilidad técnica conservada en la primera entrega: 422 si falta el parámetro o su longitud original está fuera de 12–240; 400/MOTIVO_REQUERIDO si, tras strip, queda por debajo de 12. Pruebas de ambos casos aprobadas; unificación futura requiere decisión de producto. | No bloquea las pruebas del contrato vigente; uniformidad futura pendiente. |
| DEC-10 | Defensa contractual en base de datos. | Decidir si RLS debe limitar también por contrato; definir contexto confiable por actor, tablas cubiertas, agregados de empresa y permisos de worker/ADMIN. El aislamiento contractual funcional sigue siendo obligatorio. | Diseño de RF-SEG-01 y RNF-SEG-01; no bloquea corregir controles actuales de API. |

## 10. Escenarios mínimos de aceptación transversal

| Escenario | Preparación y acción | Resultado esperado | Requisitos |
|---|---|---|---|
| AT-01 | Sin sesión, abrir dashboard e invocar API administrativa. | Login en navegador; rechazo de API; ningún dato privado. | RF-SEG-03. |
| AT-02 | Empresa B solicita documento de A con motivo válido y luego intenta exportar recursos ajenos. | Rechazo por autorización/pertenencia, sin URL ni contenido. | RF-SEG-01, RF-AUD-03. |
| AT-03 | Administrador del contrato A1 consulta/modifica A2. | No obtiene datos ni produce cambios. | RF-USU-02, RF-SEG-01. |
| AT-04 | ADMIN cambia permisos de un administrador sin empresa. | Evento con actor, destinatario, valores anterior/nuevo y fecha visible en auditoría. | RF-AUD-01. |
| AT-05 | Búsqueda con un trabajador y un equipo de nombres similares. | Categorías correctas y filtros de permisos aplicados. | RF-BUS-01/02. |
| AT-06 | Ejecutar proceso manual en `inproc` y otro en Celery. | Ambos alcanzan estado final; error real se informa y audita. | RF-SAL-03. |
| AT-07 | Suscripción UF con valor/período conocidos. | Conversión exacta según regla y sin error de firma SQL. | RF-MET-03. |
| AT-08 | Empresa con más de 100 usuarios y más de 25 contratos de riesgo. | Navegación completa y totales no limitados a la primera página. | RF-USU-01, RF-SAL-01. |
| AT-09 | API detenida mientras worker sigue activo. | Monitor no presenta API operativa sin comprobarla. | RF-SAL-02. |
| AT-10 | Build y pruebas en entorno limpio con datos desechables. | Resultado reproducible, informe por caso y ningún cambio en datos actuales. | RNF-REP-01, RNF-VAL-01. |

## 11. Cierre y mantenimiento

Un requisito se cierra cuando sus criterios pasan, los permisos y errores se verifican, se aporta evidencia y se actualiza este documento. Las dependencias/decisiones deben estar resueltas. Para requisitos de seguridad se exige prueba negativa; para métricas, datos de resultado conocido; para interfaz, recorrido con estados normal/vacío/error cuando corresponda.

Cambiar el SRS antes de ampliar alcance; mantener decisiones y motivos. Una prueba fallida no se elimina para mejorar el porcentaje. El plan puede reordenarse sin cambiar los identificadores de requisitos. La primera entrega registra correcciones y pruebas en EV-01. Las siguientes revisiones deben incorporar evidencia nueva sin borrar los resultados históricos.

## 12. Observaciones al avance declarado en el cronograma

Fuente: cronograma de 110 actividades facilitado por el equipo en esta conversación. Las actividades 1–37 tienen 100% declarado; desde la 38 las celdas de avance alcanzado están vacías. **Vacío significa avance no informado, no necesariamente 0%.** No se recalculan pesos, fechas ni porcentajes en esta revisión.

La siguiente tabla conserva el cierre declarado de las actividades técnicas y de planificación. Sus observaciones complementan los pendientes y criterios de cada requisito, sin sustituirlos.

| Actividad | Estado de seguimiento conservado | Requisitos / relación | Observación y acción de seguimiento |
|---|---|---|---|
| 3 — Recepción de documentación y base | 100% declarado; evidencia parcial | Línea base EV-02 a EV-08 | Los archivos existen. Adjuntar inventario/constancia de recepción para acreditar alcance y fecha; recibir la base no implica validarla. |
| 5 — Alcances y límites | 100% declarado, con observaciones | Sección 1 y DEC-01 a DEC-10 | Conservar acuerdo inicial; anexar su versión validada. Diferenciar recomendaciones posteriores y decisiones aún abiertas del alcance original. |
| 6 — Inicio del informe de propuesta | 100% declarado; evidencia por adjuntar | Entregable de gestión, no requisito funcional | La actividad compromete el inicio, no el cierre del informe completo. Adjuntar borrador o registro de elaboración. |
| 8 — Planificación del proyecto | 100% declarado, con observaciones | Este cronograma y PLAN_DE_TRABAJO.md | La tabla aportada acredita existencia del cronograma. El plan técnico es complementario; falta enlazar cambios aprobados sin sustituir automáticamente fechas/pesos originales. |
| 11 — Organización de repositorios, documentos y accesos | 100% declarado, con observaciones | RNF-REP-01, RNF-VAL-01 | Hay documentos y configuración. Adjuntar inventario de repositorios, responsables y accesos; no incluir secretos en la documentación. |
| 13 — Ejecución local de frontend, backend y PostgreSQL | 100% declarado; funcionamiento local corroborado | RNF-OPE-01, RNF-REP-01 | Servicios y build comprobados el 29-09-2026. Esto acredita operación local actual, no fecha original ni preparación productiva. Dependencias reproducibles quedan como ajuste. |
| 15 — Revisión de compatibilidad | 100% declarado, con observaciones | RNF-VAL-01, RF-MET-03, RF-SAL-03 | Mantener revisión como realizada; adjuntar resultados originales. Los errores UF/inproc se gestionan como incidencias, sin afirmar compatibilidad total. |
| 16 — Correcciones de informe/presentación | 100% declarado; evidencia por adjuntar | Entregable de gestión | Adjuntar versión corregida y comentarios atendidos. No verificable mediante código. |
| 20 — Identificación de brechas y riesgos | 100% declarado, con observaciones | EV-01, sección 9, RNF-VAL-01 | Cierre válido para una fecha de corte. Incorporar hallazgos nuevos al registro vivo y conservar la evidencia del análisis original. |
| 23 — Alcance priorizado, aceptación y backlog | 100% declarado, con observaciones | Secciones 5–10 y paquetes PT-* | Adjuntar backlog y conformidad original. Este SRS sigue siendo borrador: no demuestra por sí mismo validación previa del cliente. |
| 24 — Rama y estrategia de integración | 100% declarado; evidencia por adjuntar | RNF-REP-01, RNF-VAL-01 | En la copia revisada no se detectó repositorio Git. Adjuntar referencia de repositorio/rama y estrategia; no concluir que no existen en otro lugar. |
| 28 — Migraciones PostgreSQL y ORM | 100% declarado, con observaciones | RNF-VAL-01, RNF-PER-01, RF-MET-03 | Esquema 7 observado en la validación inicial; primera entrega añade esquema 8 con cinco índices y corrige firma SQL UF, probado en base temporal. Conservar trazabilidad de la corrección y aplicar migración al actualizar el entorno habitual. |
| 29 — Router administrativo y dependencias | 100% declarado, con observaciones | RF-MET-03, RF-SAL-03, RNF-VAL-01 | Router integrado bajo `/api/v1/admin`. Conversión UF y registro de tarea manual inproc corregidos en la primera entrega; recorrido distribuido Celery pendiente. |
| 30 — Ruta y componentes frontend de demostración | 100% declarado; navegación actual corroborada | EV-05, RF-DAS-01, RF-EMP-01 | La entrega originalmente nombrada `/ops` evolucionó a `/admin`. Registrar la centralización como cambio posterior; conservar funciones de sistemas y procesos. |
| 32 — Autenticación y acceso administrativo | 100% declarado para configuración básica, con observaciones | RF-SEG-01/02/03, RF-USU-02, RF-BUS-02 | Login y rechazo por rol corroborados en casos probados. RLS real, privilegio mínimo, credenciales seguras y permisos granulares permanecen parciales. Contrastar estos pendientes con el alcance original antes de clasificar ampliaciones. |
| 36 — Pruebas iniciales y registro de incidencias | 100% declarado; ejecución actual corroborada | RNF-VAL-01, EV-01 | Se ejecutaron pruebas y documentaron fallos. Mantener la actividad terminada; corrección y regresión son trabajo posterior. La evidencia actual no acredita por sí sola las fechas del 21–23 de septiembre. |

Para las demás actividades declaradas al 100% se mantienen las siguientes observaciones de gestión, sin atribuirles estados técnicos del SRS:

| Actividades | Observación |
|---|---|
| Reuniones de equipo: 1, 4, 7, 10, 12, 17, 19, 21, 25, 27, 31, 33, 35 y 37 | 100% declarado. Adjuntar acta, asistencia o acuerdos; una reunión celebrada no demuestra cierre de las acciones acordadas. |
| Reuniones con Alloxentric: 2, 9, 18, 26 y 34 | 100% declarado. Adjuntar acuerdos y decisiones, especialmente confirmación de objetivos de la actividad 9 y cambios de alcance posteriores. |
| Hitos 14 y 22 | 100% declarado. Adjuntar informe, presentación y constancia de entrega/revisión; distinguir entrega de aprobación. |

### 12.1 Seguimiento de actividades posteriores y solicitudes del cliente

| Actividades del cronograma | Relación con el SRS | Observación para actualizar avance |
|---|---|---|
| 39, 41, 44, 45 y 48 — Usuarios/clientes | RF-EMP-01/02, RF-USU-01/02, RF-MET-01/03 | Existe desarrollo adelantado y consultas probadas; conversión UF corregida; metadatos comerciales y validación de mutaciones pendientes. No asignar 100% conjunto por tener pantallas. |
| 52, 54, 57, 60 y 65 — Procesos e incidentes | RF-SAL-03, RF-AUD-01, RNF-VAL-01 | Listado y ciclo de incidentes tienen implementación; ejecución manual inproc corregida y probada; recorrido Celery pendiente. Precisar también aceptación del reintento y de la vista de historial indicada en el cronograma. |
| 64, 67, 72 y 74 — Infraestructura/monitoreo condicionado | RF-SAL-02/03, RNF-OPE-01, RF-CLI-09 | Infraestructura local y heartbeat existentes; validar sondas, detección, recuperación y cierre automático. Mantener condición de alcance y explicitar dependencia externa. |
| 71, 75, 79, 82 y 87 — Métricas comprometidas | RF-MET-01/03, RF-DAS-02 | Fuentes, reglas UF, MRR/ARR, altas/bajas/churn y snapshots requieren aceptación con datos conocidos. Mostrar el indicador no prueba su exactitud. |
| 86 y 89 — Métricas opcionales | RF-SAL-02, RF-MET-01, DEC-03/07 | No convertir p95/Application Insights, expansión/contracción, NRR por plan o LTV/CAC en obligación por aparecer en una pantalla. Registrar decisión antes de incorporarlos a la entrega comprometida. |
| 93, 95, 99 y 107 — Integración, seguridad, estabilización y aceptación | RF-SEG-*, RF-AUD-*, RNF-VAL-01 y criterios de sección 10 | Validación final pendiente. Los porcentajes previos no sustituyen pruebas de extremo a extremo ni conformidad del cliente. |
| 100 y 103 — Documentación/manual/demo | Secciones 1–11, EV-08, RNF-REP-01 | Documentación ya iniciada. Completar guía reproducible, manual y datos demo; no considerar terminados por la existencia del SRS. |
| Ocho prioridades ADMIN posteriores | RF-DAS/EMP/BUS/MET/SAL/USU/AUD/SEG | Origen comunicado: correcciones/recomendaciones del cliente. Relacionar cada detalle con actividad original o cambio; registrar fecha/fuente y aceptación. No reasignar automáticamente los pesos del cronograma. |

### 12.2 Trazabilidad de requisitos y origen

La asociación siguiente es un **análisis de correspondencia**, no una prueba de que el cronograma incluyera todos los detalles de cada requisito. «Cliente» significa solicitud posterior comunicada por el usuario; su fecha y aceptación documental están pendientes de incorporar. «Ajuste técnico» identifica un hallazgo o recomendación de la revisión. Un requisito puede tener más de un origen.

| Requisitos | Actividades relacionadas | Origen y observación de alcance | Evidencia para cerrar |
|---|---|---|---|
| RF-DAS-01, RF-DAS-02 | 39, 41, 82 | Cliente: dashboard global. El cronograma aporta resúmenes/gráficos; no especifica todos los contadores nuevos. | Contadores contrastados, universo visible y crecimiento consistente con Métricas. |
| RF-EMP-01, RF-EMP-02 | 44, 45, 48 | Cronograma: listado/detalle de clientes. Cliente: gestión global de empresas; confirmar alcance de aprobación/rechazo dentro de esa actividad. | Ficha agregada y ciclo de solicitudes probados con permisos y auditoría. |
| RF-BUS-01, RF-BUS-02 | 48, 95 como validación transversal | Cliente: buscador global. No aparece como desarrollo explícito en el cronograma; no absorberlo sin registrar el cambio. | Categorías correctas y denegación efectiva por permiso, incluida consulta directa de API. |
| RF-MET-01 | 39, 41, 71, 75, 79, 82, 87; 89 opcional | Cronograma y cliente: métricas. Separar las métricas financieras comprometidas de las opcionales y del seguimiento de adopción añadido. | Diccionario aprobado, fixtures financieros y series coherentes. |
| RF-MET-02 | 39, 41 como relación parcial | Cliente: sesiones y tiempo de uso. Telemetría real no está explícita en esas actividades; depende de DEC-05. | Estimaciones correctamente identificadas o medición real según alcance acordado. |
| RF-MET-03 | 44, 71, 87, 99 | Ajuste técnico dentro de funciones comerciales existentes: corregir firma SQL de conversión UF. | Prueba de detalle comercial y cálculo esperado aprobados. |
| RF-SAL-01 | 60, 74 como relación parcial | Cliente: salud de clientes. Riesgo documental/inactividad no equivale a incidentes técnicos del cronograma. | Casos límite de acreditación/inactividad, totales completos y datos sin actividad. |
| RF-SAL-02 | 67, 72, 74 condicionadas; 86 opcional | Cronograma condicionado: sondas. Ajuste técnico: no mostrar salud sin evidencia. p95/Application Insights sigue siendo opcional. | Simulación controlada de caídas y recuperación, con dependencia externa identificada. |
| RF-SAL-03 | 52, 54, 57, 60, 65; 64 condicionada | Cronograma: procesos e incidentes. Ajuste técnico: tarea manual `inproc`. Precisar reintentos y vista de historial, además de listado/ejecución. | Ejecución final, historial, pausa/reanudación, duplicados e incidentes comprobados. |
| RF-USU-01 | 39, 41, 45, 48 como relación parcial | Cliente: administración global de usuarios. Resumen de usuarios del cronograma no implica por sí mismo crear/reactivar cuentas. | Flujos completos, paginación y cuentas revocadas sin acceso. |
| RF-USU-02 | 32, 48, 95 | Cronograma: acceso/permisos; cliente: alcance por empresa/contrato. Confirmar detalle de la matriz. | Combinaciones válidas y pruebas cruzadas por empresa/contrato. |
| RF-AUD-01, RF-AUD-02, RF-AUD-03 | 95, 99; relación con 32 y 48 | Cronograma menciona pruebas de auditoría; cliente precisa qué debe registrarse. Una actividad de pruebas no compromete automáticamente toda ampliación del registro. | Eventos con actor/fecha/objeto, cambios anteriores/nuevos y registros sin empresa visibles. |
| RF-SEG-01, RNF-SEG-01 | 28, 32, 48, 95 | Cronograma: modelos, acceso y seguridad. Ajuste técnico: RLS efectivo en despliegue, no solo en fixtures. | Pruebas con roles sin superusuario y recursos ajenos rechazados. |
| RF-SEG-02 | 32, 95 como relación parcial | Cliente: mínimo privilegio ADMIN. Mecanismo excepcional concreto por acordar, no se presume aprobado. | Matriz y motivo/alcance excepcional verificados en servidor. |
| RF-SEG-03 | 11, 13, 32, 95, 100 | Base existente y ajuste técnico de configuración segura. Distinguir instalación local de despliegue público. | Sin semillas/secretos conocidos ni tokens de recuperación expuestos en modo público. |
| RF-CLI-01 a RF-CLI-09 | 3, 11, 15, 93, 95 | Base recibida: inventario y regresión de módulos afectados. No es compromiso automático de desarrollar nuevamente el portal de empresa. | Desglose del alcance afectado y evidencia por flujo; registrar como cambio cualquier ampliación. |
| RNF-PRV-01 | 87, 95 | Cronograma: confidencialidad/seguridad; cliente: minimizar exposición. Retención y acceso a registros por definir. | Revisión de respuestas, logs/exportaciones y decisión DEC-08. |
| RNF-REP-01 | 11, 13, 24, 100 | Cronograma y ajuste técnico de reproducibilidad. | Instalación limpia repetible y versiones registradas. |
| RNF-VAL-01 | 36, 48, 65, 87, 93, 95, 99 | Cronograma: pruebas en distintas etapas. Conservar cierre de pruebas iniciales y separar corrección/regresión. | Informe vigente por caso y evidencia de criterios del alcance entregado. |
| RNF-PER-01 | 67, 86 como relación parcial | Recomendación técnica. Sondas/p95 no equivalen a pruebas de carga; objetivos pendientes DEC-07. | Volumen, latencia y límites acordados y medidos. |
| RNF-OPE-01 | 64, 67, 72, 74 | Cronograma condicionado: operación y monitoreo. | Funcionamiento, fallos y recuperación comprobados en el entorno disponible. |
| RNF-REC-01 | 100 como relación parcial | Recomendación técnica: respaldo/restauración no figura como actividad explícita. Confirmar alcance y objetivos antes de comprometer entrega. | Restauración documentada y RPO/RTO acordados si se incorpora. |
| RNF-UX-01 | 30, 45, 57, 82, 93 como relación parcial | Integración visual del cronograma; revisión de accesibilidad/responsive propuesta técnicamente. | Recorridos y estados de interfaz; estándar de accesibilidad solo si se acuerda. |

### 12.3 Registro de observaciones y condiciones de cierre

Para conservar un 100% con observaciones, registrar: número de actividad, alcance que se considera completado, evidencia disponible, observación abierta, requisito afectado y tarea de seguimiento. Las observaciones no caducan porque la actividad histórica esté cerrada.

| Clase de observación | Tratamiento | Ejemplo actual |
|---|---|---|
| Documental | Mantener avance declarado y solicitar/adjuntar soporte. | Acta de reunión, rama remota o conformidad original. |
| Corrección de implementación | Abrir incidencia ligada al criterio afectado y verificar después de corregir. | Conversión UF o registro de tarea manual. |
| Validación incompleta | Mantener ISV/PAR y programar prueba faltante. | Mutaciones administrativas no ejercitadas en navegador. |
| Cambio solicitado por cliente | Registrar fuente, alcance, decisión e impacto antes de modificar compromisos. | Buscador global o medición real de sesiones. |
| Mejora técnica propuesta | Mantener como propuesta hasta acordar incorporación; explicar dependencia si impide un despliegue seguro. | Restauración formal o pruebas de carga con objetivos nuevos. |

**Regla de cierre:** una observación solo se marca resuelta con evidencia o una decisión explícita sobre su alcance. No convertir un defecto en «fuera de alcance» por conveniencia; contrastarlo con el criterio original. Los 100% conservados son una convención de seguimiento autorizada por el equipo, no una afirmación de que todas las observaciones estén resueltas.

## 13. Cuadro de resumen del estado general del proyecto

**Corte documental: 01-10-2026; línea base inicial del 29-09-2026.** Los estados siguientes resumen evidencia y pendientes, no porcentajes nuevos ni aceptación contractual. «Operativo» se limita a los recorridos comprobados; no significa listo para producción.

| Área | Estado general | Qué se reconoce como realizado | Observación / pendiente principal | Seguimiento |
|---|---|---|---|---|
| Gestión y actividades iniciales | 100% declarado hasta actividad 37, con observaciones | Cronograma e hitos reportados por el equipo. | Adjuntar actas/entregables y acuerdos; separar cierre de actividad de validación del producto. | Sección 12. |
| Entorno local | Operativo en el alcance comprobado | Seis servicios levantados; API, esquema y frontend accesibles; build correcto. | Reproducibilidad, credenciales y configuración productiva pendientes. | RNF-REP-01, RNF-OPE-01; PT-03/09. |
| Consola ADMIN centralizada | Integrada y navegable | Ocho secciones bajo `/admin`, login y detalle agregado probados. | No se validaron todas las mutaciones ni estados de error desde navegador. | EV-01/05; PT-05/08. |
| Dashboard global | Parcial | Contadores, acreditación, documentos y actividad. | Precisar universos y crecimiento de adopción; reservar MRR/crecimiento comercial a Métricas SaaS. | RF-DAS-01/02; PT-07. |
| Gestión de empresas | Lectura validada; ciclo completo por validar | Listado y ficha agregada operativos. | Validar aprobación/rechazo; distinguir ficha agregada del detalle comercial, cuya conversión UF ya fue corregida. | RF-EMP-01/02, RF-MET-03; PT-02/08. |
| Buscador global | Parcial; clasificación corregida | Búsqueda conectada a API; filtro de trabajadores antes del límite. | Permisos por categoría, usuarios sin empresa y validación integral pendientes. | RF-BUS-01/02; PT-04/05. |
| Métricas SaaS | Parcial; defecto UF corregido | Series e indicadores visibles. | Fecha/fuente UF, definiciones, datos demo y medición estimada de sesiones. | RF-MET-01/02/03; PT-02/07. |
| Salud de clientes | Parcial | Riesgos de acreditación, vencimientos y alertas. | Empresas sin usuarios habilitados, totales/paginación de bandeja e impacto por empresa no determinado. | RF-SAL-01; PT-06. |
| Sistemas, procesos e incidentes | Integrado, con correcciones pendientes | Panel, catálogo, heartbeat y funciones de incidentes; aliases `/admin` y `/admin/ops` cubiertos por regresión. El impacto por empresa no se atribuye sin vínculo verificable. | Tarea manual inproc corregida y probada; faltan recorrido Celery y sondas de salud real. | RF-SAL-02/03; PT-02/06; EV-09. |
| Usuarios y permisos | Parcial; reactivación implementada | Listado, roles/alcance, revocación, reactivación y último acceso; sesiones anteriores invalidadas en cambios ADMIN. | Creación global, paginación, edición consistente del alcance y recorrido visual. Migración a esquema 9 pendiente en entorno habitual. | RF-USU-01/02; PT-04/05. |
| Auditoría | Parcial | Registro y vista de actividad; creación de faenas globales ahora genera evento consultable; solicitudes de descarga con motivo. | Historial de autenticación, cobertura de otros catálogos/operaciones de eliminación, valores anteriores/nuevos, PII en descripciones y lecturas de metadatos sensibles. | RF-AUD-01/02/03; PT-04; EV-09. |
| Seguridad y aislamiento | Parcial; cierre técnico prioritario | Controles de aplicación y políticas RLS definidas. | Roles sin superusuario, mínimo privilegio, secretos y pruebas negativas; decisión de RLS contractual DEC-10. | RF-SEG-01/02/03, RNF-SEG-01; PT-03/04. |
| Portal de empresa | Implementado en parte y con validación parcial | Consultas y suites existentes; en Contratos se integró panel para asignar cuentas existentes como responsables de contrato (build EV-10). | Invitaciones nuevas y activación por correo siguen incompletas; falta probar las mutaciones y validar a los responsables reales. No implica nueva obligación de reconstrucción del portal. | RF-CLI-01 a RF-CLI-09; EV-10; PT-08. |
| Datos demo para verificación | Población local ampliada | Seed idempotente cubre 16 empresas con contratos, trabajadores, equipos, documentos, alertas y eventos; unicidad de nombres y patentes comprobada. | Son datos sintéticos de demostración, no evidencia de uso real ni población productiva. | RNF-VAL-01; EV-09. |
| Pruebas y calidad | Suite backend aprobada; aceptación integral pendiente | 363 aprobadas/0 fallidas el 01-10-2026 en PostgreSQL temporal; EV-09. | No sumar ejecuciones históricas. Extensiones reales, automatización limpia y recorridos de navegador/Celery distribuido pendientes. | RNF-VAL-01, EV-01/09; PT-01/02/09. |
| Documentación y alcance | En elaboración, con base disponible | SRS v0.16, plan técnico y registro de validación; registra panel de responsables y límites de invitación/activación. | Incorporar fuentes/aceptación de cambios y completar trazabilidad antes de revisar compromisos. | DEC-01 a DEC-10; actividades 23/100/103/107; EV-10. |
| Entrega productiva y aceptación final | Pendiente de validar | Base local funcional disponible. | Seguridad, regresión completa, recuperación y aceptación del cliente todavía no acreditadas. | RNF-REC-01, RNF-VAL-01; PT-09 y actividad 107. |

**Avance del cronograma informado:** 26,73% real acumulado en la actividad 37. Se conserva como dato de gestión suministrado; no se interpreta como porcentaje de requisitos validados. No se modifica el 100% declarado de las actividades iniciales ni se asigna avance a celdas vacías. Las correcciones pendientes siguen abiertas en el SRS y en el plan de trabajo. La suite backend completa aprobada el 01-10-2026 acredita la regresión ejecutada, no sustituye criterios de aceptación, despliegue productivo ni aceptación del cliente.
