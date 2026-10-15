# SRS — Acredittia

Especificación de requisitos de software · versión 0.58 · 15-10-2026

**Estado documental:** validado en backend con PostgreSQL temporal y lista de pendientes documental/operativa. No constituye certificación de producción ni cierre legal de DEC-08.

> **Evidencia actual validada (14-10-2026):** `python -m pytest -q` en `BASE/app/backend` ejecutó la suite completa con resultado verificado de 399 pruebas aprobadas, 0 fallidas. Queda un warning residual externo del stack FastAPI/Starlette (`starlette.testclient` + `httpx` deprecado), sin impacto funcional sobre la ejecución ni sobre los criterios de negocio.

> **BLOQUEO P0 — NO PASAR A PRODUCCIÓN CON DATOS REALES SIN CERRAR DEC-08.** Antes de autorizar el go-live, debe existir evidencia documentada de la revisión legal y contractual de privacidad y auditoría, de la aprobación de los plazos definitivos de retención y de la asignación de responsables. La evidencia debe identificar revisor/instancia, fecha, alcance, decisiones y aprobaciones; además, debe confirmar que los controles acordados están implementados y validados. La propuesta actual de plazos no constituye aprobación. Hasta entonces, DEC-08 permanece abierta y el paso a producción con datos reales queda bloqueado.

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

La versión 0.22 precisa RF-EMP-02 como aprobación/rechazo de solicitudes de registro de empresas. Se registra como IV el flujo de registro pendiente y aprobación manual por ADMIN, tras el cual la empresa y su primer usuario quedan aprobados y el usuario conserva el rol `company`, según verificación manual informada el 07-10-2026. La validación del rechazo y de transiciones fuera del flujo normal queda identificada por separado; no se presume cubierta por esa verificación.

La versión 0.23 amplía RF-BUS-01: la búsqueda acepta varios términos parciales y exige que cada uno coincida con campos del mismo resultado o de su empresa asociada. Añade un panel plegable de referencias seleccionables para empresas, cargos, contratos, tipos y marcas de equipo, sin exponer datos personales. La regresión backend y el build web se documentan en VALIDACION_ACTUAL.md; la revisión visual en navegador queda pendiente.

La versión 0.24 hace del explorador la forma principal de armar la búsqueda: se retiran los selectores desplegables de categoría de resultado y tipo de equipo. Las referencias del explorador se activan o desactivan, se muestran como chips dentro de la barra y se combinan con texto libre; todos los términos activos se aplican a la vez. Se registra además la confirmación del usuario del proyecto de que los resultados revisados no muestran datos sensibles. La validación visual de esta interacción queda pendiente.

La versión 0.25 registra la decisión de incorporar telemetría real de tiempo activo para RF-MET-02, por su importancia para la administración del negocio y el cálculo de duración promedio. El criterio funcional acordado cuenta actividad solo con sesión autenticada, pestaña visible e interacción reciente; pausa después de cinco minutos sin actividad. La implementación, diseño de persistencia, frecuencia de señal, retención y definición del denominador de la duración promedio quedan pendientes; no se presenta la métrica actual como telemetría real.

La versión 0.26 registra DEC-06 como acordada: las incidencias deben aportar trazabilidad útil para investigar qué ocurrió y dónde, incluyendo componente/proceso, operación, momento, resultado/error e identificador de correlación cuando estén disponibles. La afectación se asocia a una empresa solo con evidencia verificable; si se desconoce, se presenta como global o indeterminada, sin atribución inferida. La minimización, acceso y retención de esos datos siguen sujetos a DEC-08. La implementación y validación del recorrido operacional permanecen pendientes.

La versión 0.27 registra para DEC-07 la decisión de medir primero una línea base de carga, latencia, disponibilidad, detección de fallos y recuperación. No se fija aún un porcentaje de disponibilidad objetivo ni se declara un SLA; ambos se propondrán y aprobarán después de revisar mediciones representativas y capacidad de operación.

La versión 0.28 registra la propuesta acordada para DEC-08: minimizar los datos de auditoría, restringir y auditar su consulta, exigir motivo solo para operaciones sensibles, y aplicar retenciones iniciales diferenciadas de 12 meses para auditoría, 90 días para logs técnicos y 90 días para telemetría identificable, conservando agregados hasta 12 meses. Se excluyen secretos, URLs firmadas y contenidos documentales. Una URL emitida no prueba una transferencia completada. Los plazos quedan sujetos a revisión legal/contractual antes de producción; implementación y tratamiento histórico siguen pendientes.

La versión 0.29 eleva la revisión legal y contractual de DEC-08 a bloqueo P0 de go-live con datos reales. Se requiere evidencia de revisión, aprobaciones, responsables, decisión final de retención e implementación/validación de los controles; la propuesta de plazos no cuenta como aprobación.

La versión 0.30 cierra DEC-09: se conserva el comportamiento vigente de validación del motivo documental por compatibilidad. La falta del parámetro o la longitud original fuera de 12–240 responde HTTP 422; si la longitud inicial pasa, pero al quitar espacios el motivo queda bajo 12 caracteres, responde HTTP 400 con `MOTIVO_REQUERIDO`. No se unifican los errores ni se cambia la API en esta decisión.

La versión 0.31 registra DEC-10: la autorización y el aislamiento en la API, junto con credenciales PostgreSQL de mínimo privilegio, son obligatorios. RLS por contrato se considera una defensa adicional condicionada a que el contexto contractual se propague de forma confiable y sus políticas puedan probarse; no es un requisito automático separado de la decisión técnica. La implementación y validación de controles siguen pendientes.

La versión 0.32 cierra DEC-01 y DEC-02. ADMIN mantiene operaciones ordinarias y acceso agregado; datos sensibles requieren permiso específico, motivo, alcance temporal/recurso y auditoría de concesión, uso y revocación. No se puede desactivar, revocar ni degradar al último ADMIN activo. El buscador conserva cinco categorías, excluye administradores de plataforma y usuarios sin empresa —que se gestionan en sus vistas específicas— y no muestra documentos ni contenido documental en las fichas. La aplicación y validación de permisos en servidor siguen pendientes.

La versión 0.33 registra el criterio acordado para DEC-03: separar solicitudes de registro como embudo, empresas aprobadas como adopción y clientes activos como empresas aprobadas con suscripción activa o trial; distinguir además cuentas habilitadas de usuarios con actividad. Cada indicador debe exponer definición, período, universo, denominador cuando aplique y zona horaria. MRR y crecimiento comercial permanecen en Métricas SaaS. Aún debe detallarse la semántica de DAU/WAU, inclusión de actividad ADMIN/automática y tratamientos de estados comerciales menos comunes.

La versión 0.34 registra DEC-04: umbrales iniciales y revisables de acreditación bajo 70%, al menos tres documentos requeridos faltantes/vencidos por contrato e inactividad humana registrada durante 30 días en empresas aprobadas con usuarios habilitados. Empresas sin usuarios, sin documentos evaluables o con datos insuficientes se clasifican explícitamente como tales y no como sanas ni con riesgo cero. Estos eventos no miden duración de uso; la telemetría sigue sujeta a DEC-05.

La versión 0.35 registra para DEC-05 una señal de actividad cada 60 segundos, enviada solo mientras se cumplan las condiciones acordadas de sesión autenticada, pestaña visible e interacción reciente. Se mantiene la pausa tras cinco minutos sin actividad. Persistencia/agregación, denominador y ventana del promedio, tratamiento de sesiones simultáneas e implementación siguen pendientes.

La versión 0.36 acuerda persistir un registro por sesión lógica y agregados diarios por empresa/usuario, sin almacenar cada heartbeat como evento individual. Los registros de sesión y agregados por usuario son identificables y siguen la retención propuesta de 90 días; solo los agregados no identificables por empresa podrían conservarse hasta 12 meses, sujeto a la revisión P0 de DEC-08. La implementación, denominador/ventana del promedio y tratamiento de sesiones simultáneas siguen pendientes.

La versión 0.37 acuerda como métrica principal de tiempo el promedio de minutos activos por usuario único con actividad medida en el período (minutos activos acumulados ÷ usuarios únicos activos). No se añade duración promedio por sesión. El período exacto y la forma de resolver sesiones simultáneas siguen pendientes; la métrica heredada basada en refresh tokens permanece identificada como estimación y no sustituye esta medida.

La versión 0.38 precisa DEC-03: DAU/WAU cuenta usuarios únicos de empresas con actividad humana, excluye ADMIN de plataforma y eventos automáticos, y usa `America/Santiago` para los límites de día y semana. El tratamiento de empresas con pagos atrasados para el indicador de clientes activos queda pendiente de validación con el cliente; no se registra como decisión aprobada.

La versión 0.39 precisa el alcance de las exportaciones ADMIN: pueden abarcar datos estructurados de empresas, contratos, personas y equipos, e incluir los archivos documentales asociados, sujetos a autorización, alcance y auditoría; formato, composición y reglas de selección siguen pendientes. También acuerda reemplazar la eliminación normal de contratos por estados diferenciados de desactivación temporal y finalización. Ambos se conservan en una sección histórica de solo lectura y pueden restaurarse a operativos, manteniendo datos, relaciones e historial. Implementación y validación pendientes.

La versión 0.40 incorpora como propuesta pendiente de aprobación del cliente el flujo para solicitar la vinculación de una cuenta existente a otra empresa. La solicitud debe incluir justificación de `company` o `contract_admin` y quedar bloqueada sin cambiar membresía, `company_id` ni permisos hasta autorización explícita de ADMIN; toda decisión debe auditarse. La estructura actual admite un solo `company_id` y un solo `contrato_id` por usuario, por lo que falta que el cliente defina si la aprobación autorizaría una transferencia de empresa o si se requiere soportar membresías múltiples; no se habilitará acceso multiempresa por esta propuesta sin esa definición y el correspondiente diseño/validación.

La versión 0.41 concreta DEC-11: exportación como ZIP con archivos CSV para datos estructurados y documentos asociados organizados por carpetas. Al exportar una empresa, contrato, persona o equipo, se incluyen por defecto las relaciones asociadas y se permite desmarcar categorías. Toda exportación exige motivo. El ZIP se ofrece para descarga inmediata y no se conserva después de una transferencia completada; las generaciones fallidas o incompletas deben limpiarse, y un nuevo intento requiere generar nuevamente. No se exportan contraseñas, tokens, secretos ni credenciales. Autorización por recurso, auditoría de solicitud/generación/resultado y comprobación de transferencia siguen sujetas a implementación y validación.

La versión 0.42 precisa DEC-12: contratos desactivados o finalizados se conservan en el histórico de solo lectura, excluidos de totales y alertas operacionales actuales, y no generan nuevas alertas/notificaciones mientras estén allí. Al restaurarlos explícitamente a operativo, se reanuda el seguimiento correspondiente. Sus datos, relaciones e historial se preservan. Implementación y validación pendientes.

La versión 0.43 registra para DEC-13 la alternativa recomendada, aún pendiente de aprobación del cliente: transferencia de la cuenta, sin membresía simultánea. Tras autorización ADMIN, se retiraría el acceso a la empresa de origen y no se heredarían permisos de contratos en destino; estos requerirían asignación explícita. La solicitud no cambia empresa ni permisos mientras espera. Implementación y validación pendientes.

La versión 0.44 precisa DEC-13: además de la autorización de ADMIN, la persona titular de la cuenta debe aceptar la invitación; puede rechazarla. La transferencia solo se ejecutaría después de ambas aprobaciones, sin cambiar empresa, membresía ni permisos mientras falte alguna. Un rechazo no transfiere la cuenta. Esta propuesta sigue pendiente de aprobación del cliente; implementación y validación pendientes.

La versión 0.45 fija en 14 días la vigencia de la invitación de transferencia DEC-13. Si al cumplirse el plazo falta la aceptación de la persona titular o la autorización de ADMIN, la invitación expira y no se transfiere la cuenta ni cambian sus permisos. La propuesta sigue pendiente de aprobación del cliente; implementación y validación pendientes.

La versión 0.46 precisa DEC-11: no se fijan límites funcionales de filas ni tamaño; se intentará exportar todo el alcance autorizado. Si una exportación falla, se cancela completa y se elimina el paquete incompleto; no hay reintento automático, pero se ofrece iniciar uno nuevo manualmente. El flujo aún requiere definir la estructura detallada del ZIP y validar su viabilidad técnica ante volúmenes grandes.

La versión 0.47 aclara DEC-03: `past_due` y los estados comerciales restantes se muestran por separado y no cuentan como clientes activos; solo suscripciones activas o trial califican. DEC-05 permite seleccionar día, últimos 7 días, últimos 30 días o mes calendario; los minutos de sesiones simultáneas se suman, aunque superen el tiempo de reloj, y el denominador sigue siendo usuarios únicos. DEC-12 conserva corriendo las fechas históricas y, al restaurar, recalcula el estado vigente sin reproducir avisos atrasados; `company` y ADMIN gestionan transiciones con motivo obligatorio, mientras `contract_admin` solo consulta el histórico. DEC-13 requiere primero aceptación del titular y luego decisión ADMIN; ambas deben completarse dentro de los 14 días desde el envío. Implementación, aprobación del cliente para DEC-13 y validación siguen pendientes.

La versión 0.48 concreta la estructura de DEC-11: un CSV por tipo de entidad dentro de `/datos`; los archivos documentales se organizan en `/archivos/<tipo>/<id>/`, con nombre original saneado y su ruta registrada en el CSV correspondiente. La estructura evita duplicar físicamente un archivo asociado a varias entidades. Implementación y validación pendientes.

La versión 0.49 precisa los períodos de DEC-05: los intervalos día, últimos 7 días y últimos 30 días usan días calendario inclusivos en `America/Santiago` (hoy; hoy y los 6 días previos; hoy y los 29 días previos). Mes calendario también usa esa zona horaria. La decisión no acredita implementación ni validación.

La versión 0.50 completa la secuencia de DEC-13: el titular acepta primero la invitación; luego ADMIN revisa y decide. Ambos pasos deben completarse dentro de los 14 días desde el envío; rechazo o expiración no transfieren la cuenta ni cambian empresa o permisos. Esta alternativa sigue pendiente de aprobación del cliente. También sincroniza en los documentos relacionados las reglas acordadas para DEC-03, DEC-05 y DEC-12.

La versión 0.51 registra la implementación inicial del ciclo reversible de contratos DEC-12: estado de ciclo separado del estado operacional, motivos y auditoría, histórico y restauración con recálculo de vencimientos. También registra diálogos compartidos para confirmaciones, captura de motivos y errores. La compilación web pasó; la validación backend focalizada no pudo ejecutarse en el entorno Python 3.13/Windows por la ausencia de `pgserver`. No se declara aceptación integral ni cierre de RF-CLI-02.

La versión 0.52 incorpora validación backend focalizada posterior: 247/247 pruebas en ocho suites, incluida la migración de esquema, con PostgreSQL temporal en contenedor Python 3.12. Se verifican permisos de transición, lectura histórica, auditoría, bloqueo de mutaciones en contratos archivados y recálculo de alertas al restaurar. Dos pruebas focalizadas se repitieron tras los últimos ajustes y aprobaron; se superponen con la regresión y no se suman. También se corrigió el contador de alertas activas. No se ejecutó la suite backend completa ni se migró la base habitual; la aceptación integral y el cierre de RF-CLI-02 siguen pendientes.

La versión 0.53 registra ajustes de la consola ADMIN: Empresas (cuentas) presenta industria y estado de cuenta; Salud de clientes agrupa indicadores de actividad/adopción y permite desplegar el detalle; el buscador despliega sus resultados por botones de categoría y conserva filtros de referencia; y los cambios de rol/empresa/contrato requieren confirmación contextual y motivo, con auditoría de valores anteriores/nuevos e invalidación de sesiones. Se incorporan ayudas informativas en los indicadores y gráficos y se aclara el retorno a la consola interna durante la impersonación. La interfaz mejorada no cierra las brechas de validación de cálculos, permisos granulares, auditoría integral ni seguridad de producción. No se implementó una sección general de Ajustes para precios o supuestos financieros. Evidencia y límites en `VALIDACION_ACTUAL.md`.

La versión 0.54 incorpora una revisión documental y de código de las ocho prioridades ADMIN realizada el 13-10-2026. La estimación de avance funcional es 67% como promedio simple de las ocho prioridades, con estimaciones por prioridad de 75%, 90%, 55%, 60%, 70%, 70%, 50% y 62%, respectivamente. Estos porcentajes son una estimación de cobertura, no cumplimiento validado ni preparación para producción; no se ejecutaron pruebas ni recorrido de navegador en esta revisión. Los bloqueos P0 de permisos granulares, auditoría, aislamiento/mínimo privilegio y DEC-08 permanecen abiertos. Detalle y fundamento en `RESUMEN_REQUISITOS_ADMIN.md`, `GAP_ANALYSIS.md` y `VALIDACION_ACTUAL.md`.

La versión 0.55 registra la incorporación de la página `/reportes` al portal de empresa, conectada con las APIs existentes de generación, descarga, exportación y programación. Incluye filtros de contrato/período, historial paginado con actualización de estados, descarga, alta/edición/pausa/eliminación de programaciones y descripción de formatos. La matriz se exporta mediante el endpoint de vistas y admite Excel/CSV; los demás tipos disponibles admiten PDF/Excel. El build del frontend pasó el 14-10-2026; no se hizo recorrido visual ni validación de los flujos contra una instancia API. `contract_admin` no ve la entrada y la API rechaza el acceso a reportes consolidados. RF-CLI-07 continúa ISV hasta validar los flujos y sus permisos de extremo a extremo.

La versión 0.56 actualiza la entrega de Reportes: todos los tipos disponibles, incluida la matriz de cumplimiento, ofrecen PDF y CSV en generación, exportación y programación. El PDF incorpora marca, metadatos del período/alcance, recuento de registros, tablas paginadas con encabezados repetidos y numeración de página. La interfaz trata el CSV como tal aunque el almacenamiento conserva compatibilidad con el enum histórico `excel`. El build frontend fue aprobado; la suite backend se validó posteriormente con PostgreSQL temporal en Docker y quedó operativa.

La versión 0.57 incorpora la validación real del backend con PostgreSQL efímero y la estabilización del entorno de pruebas: la suite completa pasó 399/399, 0 fallidas, con 1 warning residual de compatibilidad del stack FastAPI/Starlette (`httpx` + `TestClient`). Los ajustes de entorno y la compatibilidad de formato `excel` se incorporan como correcciones de infraestructura y compatibilidad del sistema, no como cambio de requisitos funcionales. El estado técnico de la base sigue siendo válido para la propia ejecución de la suite, pero la decisión de go-live con datos reales sigue bloqueada por DEC-08 y los requisitos de seguridad/legal de producción.

La versión 0.58 registra, al 15-10-2026 13:14:45 -03:00, la sección `/gestion-cuentas`, la visibilidad de responsables de contrato y del perfil de empresa para ADMIN durante impersonación, y la protección contra convertir una cuenta `company` a `contract_admin` desde las rutas de gestión de empresa. La UI solo ofrece cuentas `contract_admin` como responsables; la API rechaza la conversión con `ADMIN_EMPRESA_NO_CONVERTIBLE`. Las cuentas `contract_admin` existentes pueden reasignarse entre contratos. La invitación/aceptación de cuentas existentes y el envío/canje por email siguen pendientes; la validación visual posterior al último filtro no se completó. Evidencia: `VALIDACION_ACTUAL.md`.

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

**Corte de estimación ADMIN — 13-10-2026:** la revisión de código y documentación asigna estimaciones funcionales de cobertura por prioridad, resumidas en `RESUMEN_REQUISITOS_ADMIN.md`. El 67% global es el promedio simple de las ocho cifras, con igual peso para cada prioridad; no se definieron ponderaciones por criticidad o esfuerzo. No es porcentaje de pruebas aprobadas, cumplimiento contractual, preparación productiva ni una medida objetiva de seguridad. La revisión no ejecutó tests ni validó visualmente las pantallas. Las estimaciones iniciales individuales de requisitos que aparecen abajo se conservan como antecedentes y no se deben combinar con este corte.

## 3. Actores, datos y restricciones

| Actor | Alcance actual | Objetivo y restricción |
|---|---|---|
| ADMIN (`admin`) | Administración global e impersonación mediante contexto de empresa. | Operaciones administrativas ordinarias y consultas agregadas. Datos sensibles requieren autorización excepcional con permiso específico, motivo, alcance temporal/recurso y auditoría según DEC-01; la interfaz no sustituye autorización del servidor. |
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
| EV-11 | Validación final backend 14-10-2026 | `python -m pytest -q` en `BASE/app/backend` = 399 aprobadas, 0 fallidas; 1 warning residual de compatibilidad del stack `starlette.testclient` + `httpx`. No se declara producción ni cierre de DEC-08. |

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
- **Pendientes / mejoras:** aplicar las definiciones acordadas en DEC-03; contrastar etiquetas, universos y períodos con datos de prueba. Validar con el cliente el tratamiento de pagos atrasados y otros estados no estándar de suscripciones/trials.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** con datos controlados, cada contador coincide con su universo documentado; denominador cero no causa error; los estados documentales se distinguen; no se incluyen archivos ni identificadores personales innecesarios.


**RF-DAS-02 — Actividad y crecimiento**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Actividad mensual y series existentes; falta precisar el resumen de adopción y su separación de las métricas comerciales. Se conserva el 80 % como estimación previa, pendiente de revisión del equipo.
- **Comportamiento esperado:** ADMIN consulta evolución de empresas, usuarios y actividad de la plataforma. MRR y crecimiento comercial se presentan exclusivamente en Métricas SaaS; crecimiento de adopción no equivale a crecimiento de ingresos.
- **Estado actual:** serie mensual de eventos en dashboard; crecimiento disponible en Métricas. Evidencia EV-01/02/05. La respuesta compartida de stats también contiene MRR; disponer de ese dato en API no demuestra que se muestre en el dashboard.
- **Pendientes / mejoras:** Implementar las series de registro, aprobación y actividad según DEC-03 y contrastarlas con datos conocidos. Mantener indicadores comerciales fuera de la presentación del dashboard; revisar los consumidores del endpoint compartido antes de modificar su respuesta.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** CA-01: período, universo, definición y denominador cuando aplique, visibles junto a zona horaria. CA-02: meses sin actividad representados y valores consistentes entre vistas para la misma definición. CA-03: solicitudes registradas, empresas aprobadas y clientes activos son series/contadores distintos; el dashboard distingue altas y actividad de ingresos y no presenta MRR ni crecimiento comercial. Depende de RF-MET-01 y DEC-03.


### 5.2 Gestión global de empresas — `/admin/empresas`

**RF-EMP-01 — Listado y ficha agregada**

- **Estado técnico:** IV.
- **Prioridad:** P1.
- **Avance estimado:** 100 % (propuesta inicial).
- **Fundamento del avance:** Listado y ficha agregada implementados y recorridos en navegador dentro del alcance de lectura.
- **Comportamiento esperado:** listar empresas con estado, plan, usuarios, contratos, trabajadores, nivel de uso y última actividad; abrir detalle agregado.
- **Estado actual:** EV-01/02; `GET /admin/companies` y `GET /admin/companies/{id}`. La tabla «Empresas (cuentas)» muestra industria y estado de cuenta —al día, en riesgo, moroso o no aplica— además de sus agregados; el detalle expandible incluye cuentas/perfiles y responsables por contrato. RUT/email y descripción libre del evento no se incluyen en esta respuesta operativa.
- **Pendientes / mejoras:** Mantener regresión de permisos, ausencia de plan/actividad y carga completa de páginas. Sin defecto confirmado en el recorrido de lectura probado.
- **Validación:** Listado y ficha dentro del alcance de lectura recorridos en navegador; prueba API del último evento/actor aprobada (`test_admin.py`, 20/20 al 04-10-2026), build web Docker correcto y Next informó `Ready` tras recrear el contenedor. No se completó una comprobación HTTP de la ruta después de ese reinicio. Casos límite y regresión de mantenimiento pendientes.
- **Criterio de aceptación:** la carga mediante `paginarTodo` recupera todas las páginas de API (no implica paginación visual); empresa sin plan o actividad tiene representación explícita; ficha corresponde a la fila elegida; ni listado ni detalle incluyen archivos personales. Una consulta sin ADMIN se rechaza.
- **Límite:** el uso refleja eventos, no tiempo conectado. No equivale al endpoint comercial `/admin/clientes/{id}` de RF-MET-03.


**RF-EMP-02 — Aprobar o rechazar solicitudes de registro de empresas**

- **Estado técnico:** IV para el flujo de registro y aprobación verificado manualmente; el rechazo y las transiciones fuera del flujo normal requieren validación específica.
- **Prioridad:** P1.
- **Avance estimado:** 100 % para el flujo normal de creación y aprobación (estimación revisable; no equivale a cobertura completa de rechazo o casos límite).
- **Fundamento del avance:** Se verificó manualmente que el registro crea la empresa y su primer usuario en estado pendiente; tras la autorización de ADMIN, la cuenta queda aprobada con rol `company`. Los endpoints de rechazo existen, pero esa ruta no forma parte de la validación manual informada.
- **Comportamiento esperado:** Una persona registra una empresa y su usuario inicial. La empresa y la cuenta quedan pendientes de revisión y no se habilitan para operar antes de la aprobación. ADMIN puede aprobar o rechazar la solicitud; al aprobar, la empresa y su primer usuario pasan a estado aprobado y el usuario opera con rol `company`. El rechazo debe conservar el motivo.
- **Estado actual:** `POST /auth/register` crea empresa y usuario inicial pendientes; el usuario se crea con rol `company`. `POST /admin/companies/{company_id}/approve` cambia el estado de la empresa y de sus usuarios a `approved`, guarda actor y fecha de aprobación y registra un evento de tipo `actualizacion`, con la descripción `Cuenta approved por administrador , verificado por mi parte`. El usuario del proyecto confirmó manualmente el flujo de creación pendiente, aprobación y descripción del evento de auditoría el 07-10-2026. Existe `POST /admin/companies/{company_id}/reject`, que recibe motivo y guarda el estado rechazado, pero no se aportó verificación manual de ese recorrido.
- **Pendientes / mejoras:** Probar el rechazo y que el motivo sea visible donde corresponda; definir y validar qué sucede al aprobar o rechazar una empresa ya aprobada/rechazada; completar regresión de autorización y errores. La auditoría del evento de aprobación normal quedó verificada con el tipo y descripción indicados; no implica que estén validados otros resultados o transiciones.
- **Validación:** Aprobación y evento de auditoría asociado: verificación manual informada por el usuario del proyecto el 07-10-2026; detalle en `VALIDACION_ACTUAL.md`. Rechazo, transiciones repetidas y recorrido negativo: pendientes de validación específica.
- **Criterio de aceptación:** el registro deja empresa y usuario inicial pendientes; antes de aprobar no se habilita el acceso operativo; ADMIN aprueba y ambos estados quedan aprobados, manteniendo el rol `company`; ADMIN puede rechazar con motivo; un actor sin ADMIN no puede aprobar/rechazar; actor, fecha y resultado quedan auditados. Las reglas para re-procesar una solicitud ya resuelta deben definirse y comprobarse antes de cerrar esos casos.
- **Dependencia:** RF-AUD-01. Revisar reglas existentes antes de cambiarlas.


### 5.3 Buscador global — `/admin/busqueda`

**RF-BUS-01 — Búsqueda por categoría**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Búsqueda disponible en cinco categorías; personas se buscan por RUT. La barra acepta términos parciales separados por espacios y referencias activas, y exige que cada término coincida con algún campo del mismo resultado o de su empresa asociada. El explorador reemplaza los selectores desplegables y presenta las referencias activas como chips removibles. Se conserva el 80 % como estimación previa; permisos por categoría y aceptación integral pendientes.
- **Comportamiento esperado:** Búsqueda por categoría. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** `GET /admin/search` puede consultar empresa, contrato, trabajador/persona, equipo o usuario; la interfaz presenta un botón por categoría que despliega su lista y permite seleccionar resultados. El panel de referencias permite filtrar por valores de catálogo; los chips activos se pueden retirar. Cada término parcial separado por espacios, incluyendo las referencias activas del explorador y el texto libre, debe coincidir en algún campo del mismo resultado; para contratos, personas, equipos y usuarios también se consideran datos de la empresa asociada. La API conserva filtros de servidor para integraciones que los utilicen. Busca por RUT de empresa y trabajador; las cuentas de acceso no tienen RUT. El panel plegable «Explorar y seleccionar datos para buscar» ofrece hasta 100 empresas, cargos, contratos y marcas de equipo, además de los tipos oficiales de equipo. No incluye datos personales en el catálogo. La ficha agregada se expande en la fila concreta seleccionada, muestra resumen y último evento con actor, y solo permite una ficha abierta a la vez; no muestra documentos ni contenido documental. Al cambiar búsqueda/fila o cerrar la ficha, se invalida la solicitud anterior para descartar respuestas tardías. Conforme a DEC-02, se excluyen administradores de plataforma y usuarios sin empresa; estos últimos se gestionan en sus vistas específicas. EV-01/02.
- **Pendientes / mejoras:** validar en navegador la selección/deselección de chips, presentación de límites, resultados, expansión/cierre y cambios rápidos de búsqueda; implementar permisos por categoría en servidor conforme a RF-BUS-02/DEC-01 y validar exclusiones de DEC-02.
- **Validación:** Parcial: regresión por nombre/cargo con equipos y trabajadores de dos empresas, límites 1/25 y rechazo de empresa/sin sesión en `test_admin_busqueda.py`, 30-09-2026; resultado en EV-01. No acredita permisos granulares ni recorrido en navegador.
- **Validación (04-10-2026):** filtro por categoría, RUT de trabajador, ausencia de RUT en resultados y filtros específicos de empresa, contrato, persona, equipo y usuario: `test_admin_busqueda.py`; compatibilidad del esquema vigente y heredado 10: `test_esquema.py`. Suite focalizada: 34 aprobadas, 0 fallidas; regresión ampliada de administración: 58 aprobadas, 0 fallidas. Compose inició API y web con la base en versión 10; health de esquema devolvió 200. No se recorrió el navegador.
- **Interfaz del buscador (04-10-2026):** revisión del código confirma filtros de cargo/tipo de equipo cargados desde catálogos, búsqueda con texto vacío cuando hay filtros específicos, ficha agregada bajo cada fila y control de una sola ficha abierta. La invalidación por búsqueda, fila y cierre impide aplicar respuestas tardías. Esta actualización documental no añade evidencia de ejecución: el recorrido de navegador queda pendiente en EV-01.
- **Mejora de búsqueda y referencias (07-10-2026):** la búsqueda combina términos parciales de campos diferentes, incluyendo la empresa asociada. El panel plegable de referencias presenta empresas, cargos, contratos, tipos y marcas de equipo, con un máximo de 100 valores para las categorías dinámicas; al seleccionar un valor se incorpora a la barra. La prueba backend verifica el catálogo y la combinación de marca, patente, tipo y nombre de empresa. El build frontend comprueba compilación y tipos; el recorrido visual en navegador queda pendiente.
- **Explorador como filtros seleccionables (07-10-2026):** se retiraron los selectores desplegables de categoría de resultado y tipo de equipo. Las referencias del panel se activan/desactivan y aparecen como chips removibles dentro de la barra, combinadas con el texto libre. El usuario confirmó que los resultados revisados no muestran datos sensibles. Prueba del contrato del catálogo y build web en EV-01; recorrido visual manual pendiente.
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
- **Pendientes / mejoras:** implementar en backend la matriz de permisos por operación, categoría y alcance; aplicar las restricciones de búsqueda y acceso excepcional de DEC-01/02.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** un actor sin permiso de categoría no obtiene sus resultados ni su detalle al invocar directamente la API; respuesta no contiene tokens, contraseñas, RUT ni contenido documental. Los permisos se comprueban en cada petición.


### 5.4 Métricas SaaS — `/admin/metricas`

**RF-MET-01 — Definiciones y evolución**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta inicial).
- **Fundamento del avance:** Series e indicadores implementados; la baja actividad y el desglose de uso/adopción se presentan ahora en Salud de clientes. Siguen pendientes definiciones, consistencia y validación de datos.
- **Comportamiento esperado:** ADMIN consulta indicadores de adopción y comerciales en Métricas SaaS con definición, fuente, período y unidad; las cuentas habilitadas se distinguen de usuarios con actividad efectiva.
- **Estado actual:** clientes activos, usuarios habilitados, DAU/WAU, revisiones IA, actividad mensual, MRR y otras series; la presentación de baja actividad, uso/adopción y distribución de usuarios por plan/industria se encuentra en Salud de clientes. Las tarjetas/gráficos incorporan ayudas informativas sobre definición y lectura. EV-01/02/03.
- **Pendientes / mejoras:** revisar semillas/snapshots, normalizar planes `Básico`/`Basico` sin perder relaciones y validar cálculos con datos conocidos. Los estados de suscripción que no sean activos/trial se muestran separados y no califican como clientes activos: `past_due` se identifica como pago atrasado; otros estados se agrupan como «otro estado/no activo».
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** cada indicador declara definición, fuente, período y unidad; casos conocidos producen valores esperados; ausencia de snapshot se diferencia de cero; revisiones procesadas no se etiquetan como documentos únicos si se cuentan intentos repetidos. Las series de MRR y crecimiento comercial se presentan en Métricas SaaS. Usuarios habilitados, usuarios con eventos y sesiones vigentes tienen etiquetas y universos diferenciados. Solo empresas aprobadas con suscripción activa o trial cuentan como clientes activos; `past_due` y los demás estados se presentan aparte como pago atrasado u «otro estado/no activo».
- **Dependencia:** DEC-03/04.


**RF-MET-02 — Sesiones y tiempo de uso**

- **Estado técnico:** PAR.
- **Prioridad:** P2.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** Hay estimaciones mediante tokens/eventos; se decidió incorporar telemetría real de tiempo activo, pero falta implementarla y validarla.
- **Comportamiento esperado:** ADMIN consulta sesiones vigentes y duración de actividad medida mediante telemetría real, diferenciándola de estimaciones históricas. Se cuenta tiempo solo cuando la sesión está autenticada, la pestaña visible y hay interacción reciente; se pausa tras cinco minutos sin actividad.
- **Estado actual:** sesiones vigentes a partir de refresh tokens y duración/uso estimados. No hay medición completa de inicio, actividad e inactividad. La rotación de tokens no equivale a una nueva sesión humana.
- **Pendientes / mejoras:** implementar señal cada 60 segundos y validación de sesión en servidor; persistir una fila por sesión lógica y agregados diarios por empresa/usuario, sin almacenar cada ping; definir expiración técnica y automatizar retención conforme a DEC-08 (90 días para detalle identificable; hasta 12 meses solo para agregados no identificables por empresa). El período se selecciona entre día calendario de hoy, últimos 7 días calendario (hoy y 6 previos), últimos 30 días calendario (hoy y 29 previos) o mes calendario, todo en `America/Santiago`. Se suman minutos de sesiones concurrentes, aun cuando excedan el tiempo transcurrido de reloj; el denominador es usuarios únicos activos en la ventana. Falta implementación y validación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** un token expirado o revocado no cuenta como sesión autenticada; el tiempo solo acumula durante sesión autenticada, pestaña visible e interacción reciente, y se pausa tras cinco minutos sin actividad; las señales perdidas no prolongan artificialmente la duración; la rotación no duplica sesiones. La métrica principal es minutos activos medidos divididos por usuarios únicos con actividad medida en el período seleccionable (día calendario de hoy, últimos 7 días calendario —hoy y 6 previos—, últimos 30 días calendario —hoy y 29 previos— o mes calendario), con límites en `America/Santiago`, presentando período, universo y denominador. Los minutos de sesiones concurrentes se suman incluso si superan el tiempo de reloj; comprobarlo con una misma cuenta en dos sesiones solapadas. La medida actual basada en tokens/eventos se mantiene etiquetada como estimación hasta validar la nueva telemetría.


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
- **Estado actual:** hay indicadores de baja acreditación (<70%), contratos con al menos 3 documentos pendientes/vencidos, vencidos por empresa, morosidad y bandeja. La vista agrupa la información por categoría, permite desplegar el detalle y contiene uso/adopción, clientes con baja actividad y usuarios por plan/industria, con ayudas informativas. El listado de contratos está limitado a 25 y alertas a 50 en stats. El cálculo de baja actividad y los umbrales de DEC-04 aún requieren validación integral.
- **Pendientes / mejoras:** Incluir explícitamente empresas sin usuarios habilitados y distinguirlas de empresas con usuarios sin actividad humana registrada en 30 días. Aplicar los umbrales iniciales de DEC-04 y clasificar aparte empresas sin documentos evaluables o con datos insuficientes. Definir totales, paginación y filtros de la bandeja; no etiquetar longitud de una muestra como total global.
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
- **Pendientes / mejoras:** Validar el recorrido real API→Redis→worker Celery, errores de ejecución y mutaciones en navegador. Implementar trazabilidad investigable del incidente (componente/proceso, operación, timestamps, resultado/error e identificador de correlación cuando estén disponibles) y asociación verificable a empresa, respetando minimización, acceso y retención de DEC-08.
- **Validación:** Parcial: ADMIN 19/19 en entorno aislado con inproc, 30-09-2026, EV-01. No acredita el recorrido distribuido Celery.
- **Criterio de aceptación:** ejecución llega a estado final y conserva actor; una ejecución incompatible concurrente se rechaza; pausa requiere motivo; proceso continuo no se pausa como cron; cierre de incidente requiere resolución; acciones quedan auditadas. Cada incidencia conserva suficiente contexto para investigar qué ocurrió y dónde: componente/proceso, operación, momento, resultado/error e identificador de correlación cuando estén disponibles, sin almacenar secretos o datos personales innecesarios. El impacto se asocia a empresa solo con evidencia verificable; si no se conoce, se indica global/indeterminado y no se atribuye automáticamente a todas las empresas. Probar la consulta y correlación del historial con los permisos y retención definidos en DEC-08.
- **Alcance:** validar modo local `inproc` y recorrido Celery por separado. La trazabilidad correlacionable y asociación empresarial verificable acordadas en DEC-06 todavía no están implementadas; hasta entonces no inferir impacto individual a partir del estado global.


### 5.6 Usuarios, roles y permisos — `/admin/usuarios`

**RF-USU-01 — Ciclo de vida desde la consola**

**Identificación de cuentas (30-09-2026):** listado y respuestas de modificación de usuarios exponen correo real únicamente bajo autorización ADMIN. La interfaz muestra nombre y correo, o «Sin nombre registrado» junto al correo, y permite filtrar por ambos. Las confirmaciones de revocación/reactivación incluyen correo. Este dato es necesario para identificar al destinatario de los permisos; no se modifica la minimización del buscador global.

- **Registro y perfil (05-10-2026):** el registro solicita el nombre completo del usuario que crea la cuenta, distinto de la razón social, y lo persiste en `users.nombre`. La sección autenticada «Mi perfil» permite cambiar nombre, correo y contraseña; el cambio de contraseña exige la actual. Usa `/auth/me`, sin cambio de esquema.
- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 65 % (propuesta inicial).
- **Fundamento del avance:** Listado, edición, revocación y botón de reactivación implementados; se conserva 65 % hasta completar altas, navegación y validación visual.
- **Comportamiento esperado:** Ciclo de vida desde la consola. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** botón Reactivar para cuentas revocadas, con confirmación y bloqueo durante la petición; usa PATCH administrativo con `activo=true`. Conserva rol/alcance y exige nuevo login: revocar o cambiar activo desde ADMIN incrementa `auth_version` y revoca refresh tokens. La autenticación rechaza JWT de versiones previas. `auth_version` se incorporó en la migración de esquema 9 y se probó en base temporal; la API actualmente requiere esquema 11. La versión efectiva de cada entorno debe comprobarse durante su despliegue. Se solicitan 100 usuarios sin paginación visible.
- **Pendientes / mejoras:** completar altas y navegación de más de 100 usuarios; validar reactivación en navegador y auditoría integral. Extender invalidación uniforme a los demás mecanismos de desactivación/cambio de credenciales; esta entrega cubre operaciones ADMIN. Reactivar no aprueba solicitudes pendientes o rechazadas.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** crear/invitar según el flujo existente, listar más de 100 usuarios sin omisiones, revocar y reactivar con autorización; no exponer contraseñas/tokens; cuentas revocadas no acceden a API ni renuevan sesión. Reutilizar reglas de empresa cuando correspondan.

- **Evidencia de reactivación (30-09-2026):** `test_admin_reactivacion.py` verifica revocación por POST y PATCH, bloqueo durante desactivación, rechazo de JWT/refresh anteriores tras reactivar, nuevo login/refresh funcionales y denegación sin ADMIN. Migración 8→9 e idempotencia en `test_esquema.py`; build frontend y resultados en EV-01.


**RF-USU-02 — Coherencia de alcance**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 80 % (propuesta inicial).
- **Fundamento del avance:** Backend valida alcance y la interfaz confirma los cambios sensibles; falta cerrar la matriz de autorización y validar todas las combinaciones y guardas acordadas.
- **Comportamiento esperado:** Coherencia de alcance. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** roles `admin`, `company`, `contract_admin`; backend valida contrato perteneciente a empresa. La consola presenta confirmación contextual para cambios de rol, empresa o contrato, exige motivo de al menos 12 caracteres y registra actor, motivo y valores anteriores/nuevos; el cambio invalida las sesiones del usuario. Los selects separados pueden enviar combinaciones inválidas que el backend rechaza; no se demostró persistencia de alcance inconsistente.
- **Pendientes / mejoras:** probar combinaciones rol/empresa/contrato, ausencia de cambios parciales ante error, guardas del último ADMIN y denegación por API. La confirmación y el motivo en la interfaz no sustituyen autorización del servidor ni validación integral.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** guardar rol/empresa/contrato como combinación válida; rechazo no deja cambios parciales; el usuario recibe su alcance efectivo vigente en la siguiente petición; no puede adquirir permisos de otra empresa manipulando headers o cuerpo. Guardas contra pérdida del último administrador según DEC-01.


### 5.7 Auditoría — `/admin/auditoria`

**RF-AUD-01 — Cambios administrativos**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 55 % (propuesta inicial).
- **Fundamento del avance:** Actividad registrada parcialmente; la consola de permisos ya captura valores anteriores/nuevos, pero otras operaciones y actores sin empresa requieren cobertura.
- **Comportamiento esperado:** Registrar cambios administrativos y de catálogos con actor, objeto, operación, alcance, fecha y resultado, incluyendo administradores sin empresa y distinguiendo eliminación, desactivación y actualización.
- **Estado actual:** actividad de negocio y cambios administrativos registrados parcialmente. La creación de faenas globales inserta un evento persistente `admin_catalogo` con actor, entidad y empresa `Plataforma`, y `/admin/audit` incluye eventos sin tenant mediante `outer join` (regresión EV-09). La consola de accesos registra motivo y valores anteriores/nuevos para cambios de rol/empresa/contrato; otras operaciones todavía no tienen cobertura integral. En contratos.py, el borrado físico registra tipo `actualizacion` con descripción de eliminación. Estas brechas de semántica y cobertura siguen abiertas.
- **Pendientes / mejoras:** Inventariar operaciones de plataformas, plantillas y demás catálogos; incorporar las que solo generan logs. Corregir semántica de eliminación sin confundir borrado lógico con físico; completar valores anterior/nuevo y cubrir otras acciones globales sin tenant.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** CA-01: altas, cambios de permisos y desactivación/reactivación conservan actor, destinatario, fecha UTC, resultado y alcance anterior/nuevo. CA-02: el catálogo acordado de operaciones administrativas genera eventos persistentes consultables, incluidos actores sin empresa. CA-03: las transiciones de contrato se registran inequívocamente como desactivación, finalización o restauración; si existe una eliminación física autorizada por un proceso independiente, no se confunde con esos estados. La descripción no es el único discriminador. CA-04: no se registran secretos y se aplican los controles de RNF-PRV-01.


**RF-AUD-02 — Historial de autenticación**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 25 % (propuesta inicial).
- **Fundamento del avance:** Último acceso y tokens aportan una base; falta historial completo de autenticación.
- **Comportamiento esperado:** Conservar un historial consultable de autenticación, cierre y revocación sin sobrescribir eventos anteriores al actualizar last_login_at.
- **Estado actual:** `last_login_at` y refresh tokens; no hay historial explícito completo de ingresos/salidas.
- **Pendientes / mejoras:** Último acceso y tokens aportan una base; falta historial completo de autenticación. Completar la validación del criterio de aceptación.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** registrar ingreso exitoso, fallo de autenticación sin revelar existencia de cuenta al solicitante, cierre y revocación, con correlación de sesión y resultado; no registrar tokens o contraseñas. Aplicar retención y acceso conforme a la propuesta de DEC-08, una vez revisada y materializada.


**RF-AUD-03 — Acceso sensible y exportaciones**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 60 % (propuesta inicial).
- **Fundamento del avance:** URL documental con motivo y actividad de exportación existentes; faltan uniformidad y acceso excepcional.
- **Comportamiento esperado:** Controlar acceso sensible y exportación de datos de negocio de una empresa, contrato, persona o equipo, incluyendo los archivos documentales asociados cuando formen parte de la exportación solicitada. Cumplir autorización y alcance en servidor y registrar la operación.
- **Estado actual:** emisión de URL documental exige motivo de 12–240 caracteres y registra actor/fecha/archivo. Reportes y exportaciones tienen controles y actividad, pero no una justificación uniforme ni un flujo integral de exportación de datos de negocio y archivos asociados. EV-07. GET /documentos/{doc_id} aplica pertenencia/alcance mediante _get_doc, pero no exige motivo ni registra la lectura de metadatos en el handler revisado. La ausencia de auditoría no equivale a ausencia de autorización.
- **Pendientes / mejoras:** Implementar ZIP con un CSV por tipo de entidad bajo `/datos` y archivos documentales bajo `/archivos/<tipo>/<id>/`; sanear los nombres originales y registrar la ruta de cada archivo en el CSV correspondiente. Las relaciones se incluyen por defecto con opción de desmarcar categorías; motivo obligatorio y transferencia inmediata sin conservar el archivo después de completar la descarga. No se establecen topes funcionales de filas ni tamaño: incluir todo el alcance autorizado. Si la generación falla, cancelar el paquete completo, borrar lo incompleto e informar el error; no reintentar automáticamente, pero permitir que el actor inicie un nuevo intento. Validar la viabilidad técnica ante volúmenes grandes; validar autorización y alcance de cada registro y archivo, y auditar solicitud, generación, resultado y transferencia según evidencia disponible. Clasificar metadatos sensibles en DEC-08 y fijar permisos por recurso según DEC-01. Conservar el contrato de motivo DEC-09 y la prueba cruzada aprobada.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** autorización y pertenencia se validan antes de generar exportación y para cada registro/archivo incluido; toda exportación exige motivo. El ZIP contiene un CSV por tipo de entidad bajo `/datos`, con IDs/relaciones y rutas documentales; los archivos se organizan bajo `/archivos/<tipo>/<id>/` con nombre original saneado, sin duplicar físicamente el mismo archivo. No incluye contraseñas, tokens, secretos ni credenciales. No hay topes funcionales de filas ni tamaño: se intenta incluir todo el alcance autorizado. Si falla la generación, cancelar la exportación completa, borrar el paquete incompleto e informar el error; no reintentar automáticamente y permitir un nuevo intento iniciado por el actor. La descarga es inmediata; no conservar el ZIP después de transferencia completada. Una solicitud denegada no entrega URL, archivo ni datos parciales. Auditar actor, momento, alcance/categorías, motivo y resultados de solicitud/generación/transferencia. Diferenciar generación de transferencia efectiva y usar evidencia confiable del almacenamiento cuando esté disponible. Probar fallos, limpieza, denegación cruzada y ausencia de datos fuera de alcance; evaluar viabilidad para volúmenes grandes.


### 5.8 Seguridad y aislamiento funcional

**RF-SEG-01 — Aislamiento por empresa/contrato**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 65 % (propuesta inicial).
- **Fundamento del avance:** Filtros, dependencias y RLS definidos; faltan roles reales y pruebas cruzadas completas.
- **Comportamiento esperado:** Aislamiento por empresa/contrato. Cumplir las condiciones detalladas en el criterio de aceptación.
- **Estado actual:** filtros de aplicación, dependencias y políticas RLS. Parte de las pruebas de aislamiento pasa, pero API/worker del Compose actual usan superusuario PostgreSQL, evitando RLS. Las políticas revisadas en 04_rls.sql se basan en empresa/ADMIN; el alcance contractual se comprueba principalmente en la API. No se identificó una política RLS independiente por contrato en los scripts revisados.
- **Pendientes / mejoras:** Separar roles de BD y completar pruebas por empresa/contrato. Aplicar la decisión DEC-10: autorización de API y credenciales de mínimo privilegio obligatorias; evaluar RLS contractual como defensa adicional solo si el contexto puede propagarse de forma confiable y probarse con API, workers, ADMIN y agregados. No presentar esa capa como implementada sin evidencia.
- **Validación:** Parcial: consultar evidencia de la sección 4; no se acredita el cierre de todos los criterios.
- **Criterio de aceptación:** con empresas A/B y dos contratos de A, probar listado, detalle, modificación, borrado, archivos y exportación; actor de B no accede a A y administrador de un contrato no accede al otro. La API autoriza cada operación en servidor y aplicación/worker conectan con credenciales de mínimo privilegio, sin superusuario ni BYPASSRLS. Pruebas usan credenciales equivalentes a despliegue. Si se adopta RLS contractual, comprobar también mediante SQL directo con el rol de aplicación que A1 no puede leer ni modificar A2, incluso sin filtros explícitos de API, así como aislamiento entre transacciones/conexiones reutilizadas y el alcance de workers, ADMIN y agregados.
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
- **Comportamiento esperado:** Gestionar contratos y sus requisitos sin perder trabajadores, equipos, documentos ni historial relacionado. La eliminación física no forma parte del flujo ordinario: se puede desactivar temporalmente o finalizar un contrato, consultarlo en una sección histórica de solo lectura y restaurarlo a operativo.
- **Estado actual:** Contratos y requisitos; routers `contratos.py`, `contrato_requisitos.py`, `test_contratos.py`. La revisión documental identifica un borrado físico de contrato cuya semántica de auditoría actual se registra como actualización.
- **Pendientes / mejoras:** Reemplazar la acción normal de eliminación física por desactivación temporal/finalización; implementar listado histórico de solo lectura y restauración que preserve datos, relaciones e historial. Aplicar exclusión del histórico en totales y alertas operacionales y pausar alertas/notificaciones hasta restauración explícita. Las fechas originales siguen corriendo; al restaurar, recalcular el estado vigente y emitir solo las alertas/notificaciones aún aplicables, sin reproducir individualmente avisos atrasados. `company` puede gestionar sus contratos y ADMIN actuar globalmente; `contract_admin` solo consulta el histórico dentro de su alcance. Exigir motivo en cada desactivación, finalización y restauración; validar alta/edición visual, fechas inválidas y reglas del checklist.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** operaciones de creación/edición respetan pertenencia y alcance, fechas válidas y reglas de checklist; comprobar recorrido visual de alta/edición y datos inválidos. Desactivar/finalizar no elimina físicamente ni desvincula registros relacionados; el contrato histórico es de solo lectura, se excluye de totales/alertas operacionales y no genera alertas/notificaciones nuevas. Las fechas no se desplazan; al restaurar se recalcula el estado actual y solo se emiten avisos aún vigentes, sin reproducir una cola de notificaciones omitidas. `company` solo gestiona sus contratos, ADMIN puede hacerlo globalmente y `contract_admin` tiene consulta de solo lectura dentro de su alcance. Cada transición exige motivo y audita actor, fecha, motivo y estado anterior/nuevo. Probar que usuarios sin alcance no pueden cambiar el estado ni acceder a la ficha.

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
- **Fundamento del avance:** API, cliente frontend y página `/reportes`; `reportes.py`, `test_reportes.py`. La interfaz integra generación, historial, descarga y programación; completar el recorrido de generación, fallos y descarga por actor.
- **Comportamiento esperado:** Reportes/exportación.
- **Estado actual:** La página `/reportes` ofrece los seis tipos de informe —incluida la matriz de cumplimiento— en PDF y CSV. Incluye filtro de contrato/período, historial paginado con estados, descarga de resultados listos y alta/edición/pausa/activación/eliminación de programaciones. Los PDF incluyen marca, metadatos, recuento, tabla multipágina con encabezados repetidos y pie con número de página. El build frontend pasó el 14-10-2026; no se realizó recorrido de navegador ni validación contra una API activa. CSV se serializa como formato lógico CSV y se persiste usando el enum histórico `excel` con un parámetro de formato.
- **Pendientes / mejoras:** Validar generación, fallos, permisos y descarga por actor; probar programaciones y exportaciones en entorno con API, worker y almacenamiento configurados; comprobar PDF y CSV con datos reales de prueba y volúmenes que produzcan varias páginas.
- **Validación:** Parcial. Build frontend aprobado el 14-10-2026. La ejecución backend más reciente no llegó a recolectar pruebas por falta de `pgserver`; el PDF tampoco se probó en runtime local porque ReportLab no está instalado. No se acredita el flujo completo.
- **Criterio de aceptación:** Job finaliza o informa fallo, formato y filtros correctos, descarga autorizada/temporal; administrador de contrato no obtiene reporte global de empresa.

**RF-CLI-08 — Perfil y usuarios de empresa**

- **Estado técnico:** PAR.
- **Prioridad:** P1.
- **Avance estimado:** 75 % (propuesta de seguimiento al 01-10-2026; pendiente de revisión del equipo).
- **Fundamento del avance:** Perfil y APIs para usuarios existentes; `company.py`, `test_auth.py` y `test_tenants.py`. `/gestion-cuentas` permite administrar las cuentas asociadas; `/contratos` permite asignar responsables `contract_admin`. Una cuenta `company` no puede degradarse a un contrato desde la gestión de empresa: la UI la excluye del selector y el API rechaza la conversión. ADMIN impersonando ve el perfil de empresa y el panel de responsables. Build y 71 pruebas de autenticación/tenant pasaron el 15-10-2026. La invitación y aceptación de cuentas existentes, el envío/canje del token de activación y la verificación visual posterior al último filtro siguen pendientes. La vinculación de una cuenta a otra empresa es una propuesta separada pendiente de aprobación del cliente.
- **Comportamiento esperado:** Perfil y usuarios de empresa.
- **Estado actual:** `/contratos` incluye el panel `Responsables de contrato`, visible a cuentas `company` y ADMIN con `X-Company-Id` durante «Ver como empresa». Consulta contratos y usuarios del tenant; la UI ofrece solo cuentas `contract_admin` para asignar y permite reasignar encargados entre contratos. La API rechaza convertir una cuenta `company` a `contract_admin` (`ADMIN_EMPRESA_NO_CONVERTIBLE`), preservando su acceso general. `/perfil` muestra el perfil de la empresa durante impersonación y permite editar nombre/correo; RUT y estado son de solo lectura. `/gestion-cuentas` lista, pagina y administra usuarios del tenant. El backend de invitación sigue creando cuentas nuevas y guarda un token de activación sin enviarlo; no constituye el flujo de invitación/aceptación de una cuenta existente.
- **Pendientes / mejoras:** Crear sección de usuarios/invitaciones o completar el flujo desde Contratos; enviar invitación por un canal configurado, permitir establecer contraseña mediante token de un solo uso y expirar/revocar tokens. Por separado, queda pendiente de aprobación del cliente la propuesta de solicitud justificada para vincular una cuenta existente a otra empresa. Requiere aceptación o rechazo de la persona titular y autorización ADMIN; no debe cambiar empresa ni permisos hasta contar con ambas aprobaciones. La invitación expira a los 14 días si falta cualquiera de ellas; al expirar no se realiza la transferencia. La alternativa recomendada es transferir la cuenta, no permitir membresía simultánea: al completarse la transferencia se retiraría el acceso de origen y los permisos de contratos en destino se asignarían expresamente, sin heredar los anteriores. Validar gestión, auditoría, permisos y asignación en navegador/API; identificar responsable real sin tratar una cuenta demo como persona verificada.
- **Validación:** Parcial. Build frontend correcto; `tests/test_auth.py` y `tests/test_tenants.py` pasaron 71/71 el 15-10-2026. ADMIN impersonando pudo ver en navegador el panel de responsables y el perfil de empresa antes del filtro final. No se acredita la invitación/aceptación de cuentas existentes, envío/canje de activación ni la verificación visual final del filtro de elegibilidad.
- **Criterio de aceptación:** Invitar con nombre/correo individual; asignar `company` o `contract_admin` con contrato perteneciente a la empresa; enviar y canjear activación de un solo uso; auditar actor/fecha/cambio; permitir revocar o reasignar sin perder al último usuario `company` activo. Probar que una empresa no enumera ni modifica cuentas de otra y que `contract_admin` queda limitado al contrato asignado. La propuesta de vinculación entre empresas no es criterio aprobado: si el cliente la aprueba, probar aceptación/rechazo del titular y autorización ADMIN, con vencimiento a los 14 días si falta cualquiera, garantizando que empresa y permisos no cambien hasta completar ambas aprobaciones y que el acceso de origen se retire sin heredar permisos de contratos en destino.

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
- **Comportamiento esperado:** Separar migración, API y worker; aplicar eficazmente las políticas RLS definidas para el alcance vigente; mantener secretos fuera de código/configuración pública y credenciales de mínimo privilegio. El aislamiento contractual adicional mediante RLS sigue la condición acordada en DEC-10.
- **Estado actual:** Compose usa superusuario; políticas existen. Validar con roles reales y pruebas negativas de consulta directa. Depende de RF-SEG-01/03.
- **Pendientes / mejoras:** Separar credenciales de migración/API/worker, verificar NOBYPASSRLS y proteger secretos. Aplicar la autorización contractual en API y probarla. Si se adopta RLS contractual según DEC-10, establecer y probar contexto confiable sin arrastre de alcance entre transacciones/conexiones.
- **Validación:** Parcial: revisión e inventario de la línea base; falta acreditar el flujo completo con los criterios indicados.
- **Criterio de aceptación:** Separar migración, API y worker; políticas RLS vigentes efectivas; secretos externos a código/configuración pública; credenciales de mínimo privilegio. Compose usa superusuario; políticas existen. Validar con roles reales y pruebas negativas de consulta directa. La autorización de contrato en API es obligatoria; si se adopta RLS contractual conforme a DEC-10, validar además su contexto seguro con pruebas directas y flujos de worker/ADMIN/agregados. Depende de RF-SEG-01/03.

**RNF-PRV-01 — Privacidad**

- **Estado técnico:** PAR.
- **Prioridad:** P0.
- **Avance estimado:** 50 % (propuesta inicial).
- **Fundamento del avance:** Existen respuestas agregadas minimizadas, pero falta controlar PII incrustada en descripciones y comprobar todos los consumidores; se conserva el 50 % como estimación de gestión previa.
- **Comportamiento esperado:** Minimizar datos personales en respuesta y logs; redactar secretos; definir retención y acceso a auditoría.
- **Estado actual:** La minimización es parcial. company.py incluye emails en descripciones de invitación y modificación de usuarios; admin.py devuelve descripciones en actividad/auditoría. Esto acredita presencia de PII, no una fuga entre empresas o a actores no autorizados. DEC-08 propone los campos y plazos iniciales; faltan revisión legal/contractual, implementación y tratamiento histórico.
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
- **Comportamiento esperado:** Respaldo y restauración de BD, archivos y claves coordinados. Es un mecanismo operativo de recuperación, distinto de la exportación de datos solicitada por usuarios; no reemplaza autorización/auditoría de exportaciones ni el ciclo de vida histórico del contrato.
- **Estado actual:** No se identificó implementación de respaldo/restauración ni evidencia de restauración ejecutada en la revisión. Un volumen persistente no acredita recuperación; puede existir operación externa no aportada. La decisión de preservar contratos finalizados/desactivados en el sistema no constituye un respaldo recuperable.
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
| Cliente activo | Empresa aprobada con suscripción activa o trial en stats. | `past_due` se muestra como pago atrasado y no cuenta como activa; los demás estados no activos se muestran como «otro estado/no activo». |
| Usuario habilitado | Cuenta con `activo=true`, excluyendo ADMIN en ciertos contadores. | No equivale a actividad reciente. |
| DAU / WAU | Usuarios únicos pertenecientes a empresas con actividad humana en la ventana; excluye ADMIN de plataforma y eventos automáticos. Los límites de día/semana usan `America/Santiago`. | Aplicar y validar con datos conocidos; exponer ventana, universo y zona horaria. |
| Acreditación global | Documentos obligatorios correctos / total elegible, excluyendo EMSIPOR y sobre empresas aprobadas. | Mostrar universo y diferencia frente a promedio simple por empresa. |
| Pendiente / por vencer / vencido | Estados `falta`, `porvenc`, `venc`. | En riesgo contractual se agrupan falta y vencido: etiquetarlo. |
| Documento procesado | Actualmente se cuentan revisiones IA. | Decidir si se quiere documento único, versión o ejecución. |
| Sesión vigente | Refresh token no revocado y no expirado. | No mide presencia online ni sesión humana única. |
| Tiempo de uso | Se acordó medir tiempo activo bajo sesión autenticada, pestaña visible e interacción reciente, con pausa tras cinco minutos inactivo. Métrica principal: minutos activos medidos / usuarios únicos con actividad medida en el período seleccionable (día calendario local, últimos 7 días calendario, últimos 30 días calendario o mes calendario en `America/Santiago`); sesiones simultáneas se suman aunque excedan el tiempo de reloj; se excluye ADMIN de plataforma según DEC-03. | Telemetría real aún no implementada; faltan persistencia/retención DEC-05/08 y validación. La duración heredada basada en tokens/eventos sigue siendo estimación. |
| MRR | Ingreso mensual recurrente calculado por reglas comerciales y snapshots. | Fuente/fecha UF, descuentos y datos demo deben documentarse. |

## 9. Decisiones pendientes

Responsables propuestos: responsable de producto para reglas de negocio; responsable técnico para arquitectura; responsable de operación para objetivos de servicio. Los nombres y fechas se asignarán al iniciar cada entrega.

| ID | Decisión | Propuesta inicial, no aprobada | Bloquea |
|---|---|---|---|
| DEC-01 | Permisos ADMIN y acceso excepcional. | **Decisión acordada (07-10-2026):** ADMIN realiza operaciones administrativas ordinarias y consulta datos agregados. Para datos sensibles se exige permiso específico, motivo y alcance limitado al recurso y al tiempo; se auditan concesión, uso y revocación. El sistema impide desactivar, revocar o degradar al último ADMIN activo. Implementación, matriz detallada por operación y validación en servidor pendientes. | RF-BUS-02, RF-USU-02, RF-SEG-02 y RF-AUD-03; no impide implementar rutas ordinarias que respeten el principio. |
| DEC-02 | Alcance del buscador. | **Decisión confirmada (07-10-2026):** conservar cinco categorías —empresas, contratos, personas, equipos y usuarios—; excluir administradores de plataforma y usuarios sin empresa de los resultados, gestionándolos en sus vistas específicas; las fichas no muestran documentos ni contenido documental. Implementar y probar autorización por categoría/detalle en servidor conforme a RF-BUS-02. | RF-BUS-01/02; no bloquea mejoras de interfaz que respeten el alcance. |
| DEC-03 | Universo/período de métricas. | **Criterio acordado (07-10-2026):** separar solicitudes de registro (embudo, incluye pendientes y rechazadas), empresas aprobadas en el período (adopción) y clientes activos (empresa aprobada con suscripción activa o trial); aprobación no significa cliente pagador/activo. `past_due` se muestra por separado como pago atrasado; los estados restantes distintos de activo/trial se muestran como «otro estado/no activo»; ninguno cuenta como cliente activo. Separar cuentas habilitadas de usuarios con actividad. DAU/WAU cuenta usuarios únicos de empresas con actividad humana, excluye ADMIN de plataforma y eventos automáticos, y usa `America/Santiago` para los límites de día/semana. Mostrar definición, período, universo, denominador cuando aplique y zona horaria; Dashboard para adopción/actividad, Métricas SaaS para MRR y crecimiento comercial. Cálculos por validar. | Dashboard y RF-MET-01; no bloquear mejoras de interfaz ni instrumentación. |
| DEC-04 | Umbrales de riesgo e inactividad. | **Decisión acordada (07-10-2026; umbrales iniciales y revisables):** riesgo de baja acreditación si una empresa aprobada queda bajo 70%, solo si tiene documentos obligatorios evaluables; riesgo contractual si un contrato tiene 3 o más documentos requeridos faltantes o vencidos; inactividad si una empresa aprobada con usuarios habilitados no registra actividad humana en 30 días, excluyendo eventos automáticos. Empresas sin usuarios, sin documentos evaluables o sin datos suficientes se clasifican explícitamente como “sin usuarios”/“sin datos”, no como sanas ni riesgo cero. La inactividad basada en eventos no representa duración de uso ni reemplaza DEC-05. Implementación y validación con casos límite pendientes. | RF-SAL-01; definición e implementación de alertas. |
| DEC-05 | Medición de sesión. | **Criterios funcionales acordados:** tiempo activo solo con sesión autenticada, pestaña visible e interacción reciente; heartbeat cada 60 segundos bajo esas condiciones y pausa tras cinco minutos inactivo. Persistir un registro por sesión lógica y agregados diarios por empresa/usuario; no guardar cada ping. Detalle de sesión y agregados por usuario son identificables: retención propuesta de 90 días; agregados no identificables por empresa hasta 12 meses, sujeto a aprobación legal/contractual DEC-08. Métrica principal: minutos activos medidos divididos por usuarios únicos con actividad medida. Período seleccionable: día calendario de hoy, últimos 7 días calendario (hoy y 6 previos), últimos 30 días calendario (hoy y 29 previos) o mes calendario, todos en `America/Santiago`. Sumar minutos de sesiones simultáneas, aunque excedan el tiempo transcurrido; denominador de usuarios únicos. Implementación y validación pendientes. La población de usuarios de empresas excluye ADMIN de plataforma según DEC-03. | Implementación y cierre de RF-MET-02; retención final sujeta a DEC-08. |
| DEC-06 | Trazabilidad de incidentes y atribución de impacto. | **Decisión acordada:** conservar contexto suficiente para investigar qué ocurrió y dónde —componente/proceso, operación, momento, resultado/error e identificador de correlación cuando existan—. Asociar impacto a una empresa solo con evidencia verificable; si se desconoce, mostrar alcance global/indeterminado sin inferir clientes afectados. Aplicar minimización, acceso y retención según DEC-08. Implementación y validación pendientes. | RF-SAL-03, RF-AUD-01/03, RNF-PRV-01; relación de afectación empresarial. |
| DEC-07 | Rendimiento, disponibilidad y recuperación. | **Decisión acordada:** medir una línea base representativa de carga, latencia, disponibilidad, detección de fallos y recuperación antes de fijar objetivos cuantitativos. No se define todavía un porcentaje de disponibilidad ni un SLA. Tras la medición se propondrán objetivos de disponibilidad, percentiles de latencia, capacidad/carga, tiempos de detección y RPO/RTO, que requerirán aprobación explícita y no se presentarán como compromisos contractuales antes de ello. | Aceptación cuantitativa de RNF-PER/OPE/REC. |
| DEC-08 | Auditoría y privacidad. | **Propuesta acordada (07-10-2026; plazos sujetos a revisión legal/contractual antes de producción):** registrar solo metadatos necesarios para investigar —actor, acción, recurso, fecha, resultado y correlación cuando exista—; no guardar contraseñas, tokens, URLs firmadas ni contenido de documentos; exigir motivo solo para operaciones sensibles según la matriz de permisos; limitar la consulta a ADMIN/roles autorizados y auditar también esas consultas. Retención inicial: auditoría 12 meses, logs técnicos 90 días y telemetría identificable 90 días; métricas agregadas hasta 12 meses. Una URL emitida no equivale a descarga completada; si se necesita acreditar transferencia real, usar evidencia confiable del almacenamiento. Documentar integridad y tratamiento de registros históricos. Implementación y revisión de plazos pendientes. **Puerta P0:** no autorizar producción con datos reales hasta documentar revisión legal/contractual, aprobaciones y responsables, cerrar los plazos definitivos y demostrar controles implementados y validados. | Go-live con datos reales; RNF-PRV-01, RF-AUD-02/03. |
| DEC-09 | Respuesta ante motivo documental inválido. | **Decisión cerrada (07-10-2026):** conservar el contrato vigente por compatibilidad, sin modificar la API. HTTP 422 si falta el parámetro o la longitud original está fuera de 12–240; HTTP 400 con `MOTIVO_REQUERIDO` si la longitud inicial pasa, pero tras quitar espacios queda bajo 12. Las pruebas existentes cubren estos casos. No se requiere unificar errores; una futura modificación del contrato necesitará una nueva decisión y análisis de compatibilidad. | Cerrada para el contrato actual; no bloquea la entrega. |
| DEC-10 | Defensa contractual en base de datos. | **Decisión acordada (07-10-2026):** la autorización en API y las credenciales de base de datos de mínimo privilegio son obligatorias. RLS por contrato se considera defensa en profundidad si el contexto contractual puede propagarse de forma confiable y la implementación puede probarse de extremo a extremo; no se exige como capa independiente sin resolver antes ese diseño. Si se implementa, definir tablas y políticas, aislamiento de transacciones/conexiones reutilizadas y permisos acotados para workers, ADMIN y consultas agregadas. La denegación entre contratos en API sigue siendo obligatoria aunque no se implemente RLS contractual. Implementación y validación de controles pendientes; la decisión no certifica conformidad del estado actual. | Cierre de RF-SEG-01/RNF-SEG-01: pruebas negativas API por empresa/contrato y roles PostgreSQL de mínimo privilegio; SQL directo entre contratos si se adopta RLS contractual. |
| DEC-11 | Exportación de datos de negocio y archivos. | **Decisión acordada (08-10-2026):** exportar como ZIP con un CSV por tipo de entidad bajo `/datos`; documentos bajo `/archivos/<tipo>/<id>/`, con nombre original saneado y su ruta en el CSV correspondiente, evitando duplicar físicamente un archivo relacionado con más de una entidad. Al elegir una empresa, contrato, persona o equipo, incluir relaciones asociadas por defecto y permitir desmarcar categorías. Exigir motivo en toda exportación. Entregar para descarga inmediata y no conservar el ZIP después de transferencia completada. No fijar límites funcionales de filas ni tamaño: intentar incluir todo el alcance autorizado. Ante un fallo, cancelar el paquete completo, eliminar lo incompleto, informar el error y permitir un nuevo intento manual, sin reintento automático. Excluir contraseñas, tokens, secretos y credenciales. Autorización de cada recurso y archivo y auditoría de solicitud/generación/resultado/transferencia son obligatorias. Viabilidad técnica para volúmenes grandes pendiente. No equivale a respaldo/restauración (RNF-REC-01). | Cierre de RF-AUD-03/RNF-PRV-01 y validación de exportación autorizada. |
| DEC-12 | Ciclo de vida de contratos. | **Decisión acordada (08-10-2026):** reemplazar la eliminación física ordinaria por desactivado (pausa) y finalizado (cierre); conservar ambos en histórico de solo lectura, fuera de totales/alertas operacionales y sin nuevas alertas/notificaciones mientras estén históricos. Las fechas originales siguen corriendo. Al restaurar, recalcular estado vigente y generar solo alertas/notificaciones todavía aplicables, sin reproducir avisos atrasados individualmente. `company` gestiona contratos propios, ADMIN globalmente y `contract_admin` solo consulta el histórico dentro de su alcance. Cada transición requiere motivo y audita actor, fecha, motivo y estado anterior/nuevo. Datos y relaciones se preservan. Implementación registrada en v0.51; validación focalizada registrada en v0.52, sin equivaler a aceptación integral. | RF-CLI-02; cobertura de auditoría RF-AUD-01. |
| DEC-13 | Solicitud de vinculación de cuenta a otra empresa. | **Propuesta pendiente de aprobación del cliente (08-10-2026):** `company` o `contract_admin` podría solicitar una transferencia justificada de una cuenta a otra empresa. La persona titular debe aceptar primero; luego ADMIN revisa y decide. Ambas etapas deben completarse dentro de los 14 días desde el envío; rechazo o expiración no cambia empresa ni permisos. Solicitud, justificación, aceptación/rechazo, expiración y decisión ADMIN se auditan. La alternativa recomendada es transferir, sin membresía simultánea: al completarse se retira el acceso de origen y no se heredan permisos de contratos en destino, que requieren asignación explícita. No implementar hasta aprobación del cliente. El esquema actual solo admite un `company_id` y un `contrato_id` por usuario; diseño, implementación y validación pendientes. | RF-CLI-08, RF-USU-02, RF-AUD-01/03 y DEC-10. |

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
| RF-MET-02 | 39, 41 como relación parcial | El cronograma original menciona sesiones/tiempo de uso, pero no define telemetría real. La decisión posterior v0.25 incorpora medición de tiempo activo mediante DEC-05; representa alcance acordado adicional y no se atribuye retroactivamente a las actividades originales. | Implementación y validación de sesión autenticada, presencia visible, pausa por inactividad y duración promedio según RF-MET-02/DEC-05. |
| RF-MET-03 | 44, 71, 87, 99 | Ajuste técnico dentro de funciones comerciales existentes: corregir firma SQL de conversión UF. | Prueba de detalle comercial y cálculo esperado aprobados. |
| RF-SAL-01 | 60, 74 como relación parcial | Cliente: salud de clientes. Riesgo documental/inactividad no equivale a incidentes técnicos del cronograma. | Casos límite de acreditación/inactividad, totales completos y datos sin actividad. |
| RF-SAL-02 | 67, 72, 74 condicionadas; 86 opcional | Cronograma condicionado: sondas. Ajuste técnico: no mostrar salud sin evidencia. p95/Application Insights sigue siendo opcional. | Simulación controlada de caídas y recuperación, con dependencia externa identificada. |
| RF-SAL-03 | 52, 54, 57, 60, 65; 64 condicionada | Cronograma: procesos e incidentes. Ajuste técnico: tarea manual `inproc`. Precisar reintentos y vista de historial, además de listado/ejecución. | Ejecución final, historial, pausa/reanudación, duplicados e incidentes comprobados. |
| RF-USU-01 | 39, 41, 45, 48 como relación parcial | Cliente: administración global de usuarios. Resumen de usuarios del cronograma no implica por sí mismo crear/reactivar cuentas. | Flujos completos, paginación y cuentas revocadas sin acceso. |
| RF-USU-02 | 32, 48, 95 | Cronograma: acceso/permisos; cliente: alcance por empresa/contrato. Confirmar detalle de la matriz. | Combinaciones válidas y pruebas cruzadas por empresa/contrato. |
| RF-AUD-01, RF-AUD-02, RF-AUD-03 | 95, 99; relación con 32 y 48 | Cronograma menciona pruebas de auditoría; cliente precisa qué debe registrarse. Una actividad de pruebas no compromete automáticamente toda ampliación del registro. | Eventos con actor/fecha/objeto, cambios anteriores/nuevos y registros sin empresa visibles. |
| RF-SEG-01, RNF-SEG-01 | 28, 32, 48, 95 | Cronograma: modelos, acceso y seguridad. Ajuste técnico: políticas RLS vigentes efectivas en despliegue, no solo en fixtures; RLS contractual adicional condicionado a DEC-10. | Pruebas con roles de mínimo privilegio, recursos ajenos rechazados y, si se adopta RLS contractual, aislamiento verificado por SQL directo. |
| RF-SEG-02 | 32, 95 como relación parcial | Cliente: mínimo privilegio ADMIN. Mecanismo excepcional concreto por acordar, no se presume aprobado. | Matriz y motivo/alcance excepcional verificados en servidor. |
| RF-SEG-03 | 11, 13, 32, 95, 100 | Base existente y ajuste técnico de configuración segura. Distinguir instalación local de despliegue público. | Sin semillas/secretos conocidos ni tokens de recuperación expuestos en modo público. |
| RF-CLI-01 a RF-CLI-09 | 3, 11, 15, 93, 95 | Base recibida: inventario y regresión de módulos afectados. No es compromiso automático de desarrollar nuevamente el portal de empresa. | Desglose del alcance afectado y evidencia por flujo; registrar como cambio cualquier ampliación. |
| RNF-PRV-01 | 87, 95 | Cronograma: confidencialidad/seguridad; cliente: minimizar exposición. DEC-08 propone acceso restringido y auditado, minimización y retenciones diferenciadas; los plazos requieren revisión legal/contractual antes de producción. | Revisar respuestas, logs/exportaciones, materializar la política y documentar tratamiento histórico. |
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

**Corte de estados funcionales generales: 01-10-2026; línea base inicial del 29-09-2026.** Los estados siguientes resumen evidencia y pendientes, no porcentajes nuevos ni aceptación contractual. «Operativo» se limita a los recorridos comprobados; no significa listo para producción. Para la estimación más reciente de las ocho prioridades ADMIN, consultar el corte del 13-10-2026 en `RESUMEN_REQUISITOS_ADMIN.md`; no sustituye ni actualiza por sí solo los estados de aceptación de esta tabla.

| Área | Estado general | Qué se reconoce como realizado | Observación / pendiente principal | Seguimiento |
|---|---|---|---|---|
| Gestión y actividades iniciales | 100% declarado hasta actividad 37, con observaciones | Cronograma e hitos reportados por el equipo. | Adjuntar actas/entregables y acuerdos; separar cierre de actividad de validación del producto. | Sección 12. |
| Entorno local | Operativo en el alcance comprobado | Siete servicios definidos en Compose; API, esquema y frontend accesibles; build correcto. | Reproducibilidad, credenciales y configuración productiva pendientes. | RNF-REP-01, RNF-OPE-01; PT-03/09. |
| Consola ADMIN centralizada | Integrada y navegable | Ocho secciones bajo `/admin`, login y detalle agregado probados. | No se validaron todas las mutaciones ni estados de error desde navegador. | EV-01/05; PT-05/08. |
| Dashboard global | Parcial | Contadores, acreditación, documentos y actividad. | Precisar universos y crecimiento de adopción; reservar MRR/crecimiento comercial a Métricas SaaS. | RF-DAS-01/02; PT-07. |
| Gestión de empresas | Lectura validada; aprobación del registro verificada; rechazo/casos límite por validar | Listado y ficha agregada operativos. El registro queda pendiente y ADMIN puede aprobar; empresa y usuario inicial quedan aprobados y conservan rol `company`. | Validar rechazo, transiciones repetidas y auditoría; distinguir ficha agregada del detalle comercial, cuya conversión UF ya fue corregida. | RF-EMP-01/02, RF-MET-03; PT-02/08. |
| Buscador global | Parcial; clasificación corregida | Búsqueda conectada a API; filtro de trabajadores antes del límite. Alcance funcional definido en DEC-02. | Permisos por categoría/detalle en servidor y validación integral pendientes; comprobar las exclusiones acordadas. | RF-BUS-01/02; PT-04/05. |
| Métricas SaaS | Parcial; defecto UF corregido | Series e indicadores visibles. | Fecha/fuente UF, definiciones, datos demo y medición estimada de sesiones. | RF-MET-01/02/03; PT-02/07. |
| Salud de clientes | Parcial | Riesgos de acreditación, vencimientos y alertas. | Empresas sin usuarios habilitados, totales/paginación de bandeja e impacto por empresa no determinado. | RF-SAL-01; PT-06. |
| Sistemas, procesos e incidentes | Integrado, con correcciones pendientes | Panel, catálogo, heartbeat y funciones de incidentes; aliases `/admin` y `/admin/ops` cubiertos por regresión. El impacto por empresa no se atribuye sin vínculo verificable. | Tarea manual inproc corregida y probada; faltan recorrido Celery y sondas de salud real. | RF-SAL-02/03; PT-02/06; EV-09. |
| Usuarios y permisos | Parcial; reactivación y cambios auditables de alcance implementados | Listado, roles/alcance, revocación, reactivación y último acceso; cambios de rol/empresa/contrato requieren confirmación y motivo, registran valores anteriores/nuevos e invalidan sesiones. | Creación global, paginación, edición consistente del alcance, validación integral del flujo y recorrido visual. La API exige el esquema actual v11; la actualización de cada entorno debe validarse por separado. | RF-USU-01/02; PT-04/05. |
| Auditoría | Parcial | Registro y vista de actividad; creación de faenas globales ahora genera evento consultable; solicitudes de descarga con motivo. | Historial de autenticación, cobertura de otros catálogos/operaciones de eliminación, valores anteriores/nuevos, PII en descripciones y lecturas de metadatos sensibles. | RF-AUD-01/02/03; PT-04; EV-09. |
| Seguridad y aislamiento | Parcial; cierre técnico prioritario | Controles de aplicación y políticas RLS definidas. | Roles sin superusuario, mínimo privilegio, secretos y pruebas negativas; decisión de RLS contractual DEC-10. | RF-SEG-01/02/03, RNF-SEG-01; PT-03/04. |
| Portal de empresa | Implementado en parte y con validación focalizada | Consultas y suites existentes; el ciclo contractual reversible y el bloqueo de mutaciones históricas se validaron en la regresión focalizada v0.52. En Contratos se integró panel para asignar cuentas existentes como responsables (build EV-10). | Invitaciones nuevas y activación por correo siguen incompletas; faltan recorrido visual, pruebas distribuidas asíncronas y validación de responsables reales. No implica nueva obligación de reconstrucción del portal. | RF-CLI-01 a RF-CLI-09; EV-10; PT-08. |
| Datos demo para verificación | Población local ampliada | Seed idempotente cubre 16 empresas con contratos, trabajadores, equipos, documentos, alertas y eventos; unicidad de nombres y patentes comprobada. | Son datos sintéticos de demostración, no evidencia de uso real ni población productiva. | RNF-VAL-01; EV-09. |
| Pruebas y calidad | Regresión focalizada aprobada; aceptación integral pendiente | 363 aprobadas/0 fallidas el 01-10-2026 (EV-09) y 247/247 en ocho suites pertinentes el 08-10-2026 (v0.52), ambas en PostgreSQL temporal. | No sumar ejecuciones superpuestas ni presentarlas como suite completa. Extensiones reales, automatización limpia y recorridos de navegador/Celery distribuido pendientes. | RNF-VAL-01, EV-01/09; PT-01/02/09. |
| Documentación y alcance | En elaboración, con base disponible | SRS v0.52, plan técnico y registro de validación; registra panel de responsables, límites de invitación/activación, exportación con archivos, ciclo de vida de contratos y propuesta pendiente de vinculación entre empresas. | Incorporar fuentes/aceptación de cambios y completar trazabilidad antes de revisar compromisos. | DEC-01 a DEC-13; actividades 23/100/103/107; EV-10. |
| Entrega productiva y aceptación final | Pendiente de validar | Base local funcional disponible. | Seguridad, regresión completa, recuperación y aceptación del cliente todavía no acreditadas. | RNF-REC-01, RNF-VAL-01; PT-09 y actividad 107. |

**Avance del cronograma informado:** 26,73% real acumulado en la actividad 37. Se conserva como dato de gestión suministrado; no se interpreta como porcentaje de requisitos validados. No se modifica el 100% declarado de las actividades iniciales ni se asigna avance a celdas vacías. Las correcciones pendientes siguen abiertas en el SRS y en el plan de trabajo. La suite backend completa aprobada el 01-10-2026 acredita la regresión ejecutada, no sustituye criterios de aceptación, despliegue productivo ni aceptación del cliente.
