# Plan de trabajo — Acredittia

Versión 4.0 · 15-10-2026 · propuesta de ejecución vinculada a [SRS.md](SRS.md) versión 0.58.

**Actualización al 08-10-2026:** los avances de PT-05, PT-06, PT-07 y PT-08
incorporan cambios posteriores a la versión 0.5, incluida la implementación
inicial de DEC-12 y los diálogos de confirmación. La regresión backend
focalizada de ocho suites pasó 247/247 en PostgreSQL temporal; esto no equivale
a la suite completa ni a aceptación integral. La tabla refleja el trabajo
realizado y separa la implementación de la validación aún pendiente. Los
porcentajes, estados y evidencias anteriores se conservan como historial; esta
actualización no declara aceptación de producto ni cierre de requisitos.

**Actualización al 13-10-2026:** se registran mejoras de Empresas (industria,
estado de cuenta y detalle de perfiles/responsables), Salud de clientes
(indicadores de uso/adopción y detalle plegable), buscador (botones por
categoría), ayudas informativas y confirmación auditable con motivo para
cambios de permisos. Estas tareas de interfaz no cierran la validación
funcional de métricas, permisos ni seguridad. La evidencia y límites están en
[VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md); las estimaciones y estados de
aceptación no se elevan por la sola implementación visual. La revisión de
código/documentación del 13-10-2026 estima 67% de avance funcional ADMIN
(promedio simple de ocho prioridades); no ejecutó pruebas ni equivale a
aceptación o preparación para producción. Los bloqueos P0 continúan vigentes.

**Actualización al 14-10-2026:** se amplió Reportes en el portal de empresa:
los seis tipos están disponibles en PDF/CSV, con PDF paginado y metadatos. El
build frontend pasó; la validación de API, worker, almacenamiento y generación
PDF permanece pendiente por las limitaciones de entorno descritas en
[VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md). Este avance de portal no modifica
la estimación ADMIN del 67%.

**Actualización al 15-10-2026, 13:14:45 -03:00:** se incorporó
`/gestion-cuentas` para administrar cuentas asociadas, y ADMIN en «Ver como
empresa» vuelve a ver responsables de contrato y el perfil de empresa. Una
cuenta `company` no se puede convertir a `contract_admin` desde la gestión de
empresa; la UI la excluye y el API rechaza la conversión. Build frontend y
regresión de autenticación/tenant pasaron (71/71). La invitación/aceptación de
cuentas existentes y la notificación por email siguen pendientes; la
verificación visual del selector tras el último filtro no se completó. Ver
[VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md) y RF-CLI-08 en [SRS.md](SRS.md).

**DEC-09 cerrada (07-10-2026):** se conserva por compatibilidad la validación vigente del motivo documental: HTTP 422 para parámetro ausente o longitud original fuera de rango, y HTTP 400/`MOTIVO_REQUERIDO` cuando el valor pasa longitud inicial pero queda bajo el mínimo después de quitar espacios. No requiere cambios de API; cualquier unificación futura requiere decisión nueva y pruebas de compatibilidad.

**DEC-10 acordada (07-10-2026):** autorización en API y credenciales PostgreSQL de mínimo privilegio son obligatorias. RLS por contrato puede incorporarse como defensa adicional si el contexto se propaga de forma confiable y se prueba de extremo a extremo, incluidos workers, ADMIN, reportes agregados y conexiones reutilizadas. La denegación por API y el aislamiento funcional entre contratos siguen siendo obligatorios; el diseño e implementación de RLS contractual permanecen pendientes.

**DEC-01/02 acordadas (07-10-2026):** ADMIN conserva operaciones ordinarias y acceso agregado; los datos sensibles requieren permiso específico, motivo, alcance temporal/recurso y auditoría de concesión, uso y revocación. Se impide perder al último ADMIN activo. El buscador conserva cinco categorías, excluye administradores de plataforma y usuarios sin empresa, y no muestra documentos en las fichas. La matriz granular, la autorización de servidor y sus pruebas siguen pendientes.

**DEC-03 acordada funcionalmente (07-10-2026, precisión 08-10-2026):** separar solicitudes registradas como embudo, empresas aprobadas como adopción y clientes activos como empresas aprobadas con suscripción activa/trial; distinguir cuentas habilitadas de usuarios con actividad. `past_due` se presenta aparte como pago atrasado y los demás estados comerciales no activos/trial como «otro estado/no activo»; ninguno cuenta como cliente activo. DAU/WAU cuenta usuarios únicos de empresas con actividad humana, excluye ADMIN de plataforma y eventos automáticos, y usa `America/Santiago` para límites de día/semana. Cada indicador debe identificar definición, período, universo, denominador cuando aplique y zona horaria. MRR/crecimiento comercial queda en Métricas SaaS. Cálculos aún requieren validación.

**DEC-04 acordada (07-10-2026):** umbrales iniciales y revisables de acreditación <70%, 3 o más documentos requeridos faltantes/vencidos por contrato e inactividad humana registrada por 30 días para empresas aprobadas con usuarios habilitados. Empresas sin usuarios, sin documentos evaluables o con datos insuficientes se muestran en categorías explícitas y no como sanas/riesgo cero. Eventos humanos no miden duración de uso; telemetría real sigue pendiente en DEC-05. Implementación y pruebas de límites pendientes.

**DEC-05 acordada funcionalmente (08-10-2026):** heartbeat cada 60 segundos bajo las condiciones de actividad autenticada; pausa tras cinco minutos inactivo; guardar un registro por sesión lógica y agregados diarios por empresa/usuario, no cada ping. Métrica: minutos activos / usuarios únicos con actividad. El período seleccionable usa días calendario en `America/Santiago`: hoy, últimos 7 días (hoy y 6 anteriores), últimos 30 días (hoy y 29 anteriores) o mes calendario local. Sumar sesiones simultáneas aunque los minutos excedan el tiempo de reloj; el denominador sigue siendo personas únicas. Detalle y agregado por usuario (identificables) con retención propuesta de 90 días; agregados no identificables por empresa hasta 12 meses, sujeto a revisión de DEC-08. Implementación y validación siguen pendientes; se excluye ADMIN de plataforma según DEC-03.

**DEC-11/12 acordadas (08-10-2026):** exportar como ZIP con un CSV por tipo de entidad bajo `/datos` y documentos bajo `/archivos/<tipo>/<id>/`, con nombre saneado y ruta del archivo en el CSV para evitar duplicados; incluir relaciones por defecto y permitir desmarcar categorías; exigir motivo y ofrecer descarga inmediata sin conservar el ZIP luego de transferido. No hay topes funcionales: intentar incluir todo el alcance autorizado. Ante fallo, cancelar, eliminar el paquete incompleto e informar; no reintentar automáticamente, permitir nuevo intento manual. Excluir secretos/credenciales y autorizar/auditar cada recurso y archivo. Viabilidad ante grandes volúmenes sigue pendiente. La eliminación física deja de ser la acción ordinaria sobre contratos: se distinguen desactivación temporal y finalización; ambas aparecen en histórico de solo lectura, se excluyen de totales/alertas operacionales y no generan nuevas alertas/notificaciones. Las fechas originales siguen corriendo; al restaurar se recalcula el estado vigente sin reproducir avisos atrasados individualmente. `company` gestiona sus contratos y ADMIN globalmente; `contract_admin` solo consulta el histórico dentro de su alcance. Toda transición exige motivo y auditoría. La implementación inicial está incorporada; la validación integral queda pendiente. Exportar no sustituye respaldar/restaurar.

**DEC-13 propuesta pendiente de aprobación del cliente (08-10-2026):** `company` o `contract_admin` podría solicitar una transferencia justificada de una cuenta existente a otra empresa. La persona titular acepta primero; luego ADMIN revisa y decide. Ambas etapas deben completarse dentro de los 14 días desde el envío; rechazo o expiración no cambian empresa ni permisos. Solicitud, justificación, aceptación/rechazo, expiración y decisión ADMIN se auditan. La alternativa recomendada es transferir, no admitir membresía simultánea: al completarse se retira el acceso de origen y se asignan expresamente los permisos de destino, sin heredar contratos. No implementar sin aprobación del cliente. El modelo actual admite un solo `company_id` y `contrato_id` por cuenta. Diseño, implementación y validación pendientes.

**Avance PT-05-03 (30-09-2026):** API identifica recorte por categoría y la interfaz distingue resultados mostrados de coincidencias completas. Falta recorrido visual y siguen pendientes los permisos efectivos en servidor. El alcance funcional fue confirmado en DEC-02. Evidencia en VALIDACION_ACTUAL.md.

**Avance PT-05-02 (30-09-2026):** validación de consultas vacías/cortas tras normalizar espacios y límites 2/100 comprobados. Buscador + ADMIN: 32/32; evidencia en VALIDACION_ACTUAL.md. RF-BUS-01 sigue parcial; faltan presentación de límites y decisiones de alcance/permisos.

No es una lista de nuevas funciones aprobadas automáticamente. Se priorizan correcciones confirmadas; las reglas nuevas sujetas a `DEC-*` se definen antes de implementarse. Responsables personales, estimaciones y fechas están por asignar; no se inventan plazos sin revisar el esfuerzo.

## 1. Secuencia de entregas

**PT-05-04 (30-09-2026):** Reactivar disponible en Usuarios mediante PATCH existente; cambios de estado ADMIN invalidan JWT/refresh anteriores. Esquema 9, migración `10_version_sesion.sql`. Pruebas en EV-01; altas, paginación, auditoría integral y navegador pendientes. No se migró el entorno habitual.

**PT-05-05 (30-09-2026):** identificación de cuentas mediante nombre y correo real en gestión ADMIN; alternativa legible para cuentas sin nombre y confirmaciones con correo. RF-USU-01 permanece PAR. Pruebas de acceso e identidad y build en EV-01; recorrido visual pendiente.

**PT-03-02 (30-09-2026):** guarda de conexiones nuevas en producción para API/Celery contra roles privilegiados o propietarios de tablas. Validación con PostgreSQL efímero en EV-01. La separación efectiva de credenciales y el cambio de Compose continúan pendientes; no se modifica el estado PAR de seguridad.

**Avances posteriores (05-10-2026):**

- **PT-05 / RF-BUS-01:** filtros de cargo y tipo de equipo conectados a catálogos; búsqueda con texto vacío cuando hay filtros específicos; ficha expandible bajo la fila seleccionada, una sola abierta, con descarte de respuestas tardías. Está documentado por revisión del código; falta recorrido visual y prueba específica de estos comportamientos.
- **PT-06/07 / RF-SAL-01 y RF-MET-01/02:** Métricas SaaS presenta clientes sin usuarios, usuarios sin actividad y con baja actividad, además de un diccionario de definiciones. Se mantiene pendiente la validación de umbrales, listas limitadas, métricas de sesión y sondas operacionales.
- **PT-08 / RF-CLI-01 y RF-EMP-02:** el registro solicita el nombre del usuario inicial y `/perfil` permite editar nombre, correo y contraseña sin migración. `tests/test_auth.py` pasó 34/34 y el build web generó 23 rutas. Se verificó manualmente el flujo de registro pendiente y aprobación ADMIN de empresa/usuario inicial con rol `company`; el rechazo y transiciones repetidas aún requieren validación. El bloqueo de perfil de ADMIN durante «Ver como empresa» es un control de interfaz, no autorización backend. Invitaciones por correo siguen pendientes.

**Actualización PT-05 / RF-BUS-01 (07-10-2026):** la búsqueda acepta términos parciales separados por espacios que deben coincidir en campos del mismo resultado o de su empresa. Se retiraron los selectores desplegables; las referencias de empresas, cargos, contratos, tipos y marcas se activan/desactivan en un panel y aparecen como chips removibles dentro de la barra, combinadas con texto libre. `test_admin_busqueda.py` valida el catálogo y la ausencia de RUT/correo en sus respuestas; el build web compiló. El usuario confirmó que los resultados revisados no muestran datos sensibles. Falta recorrido visual de la selección/deselección. Evidencia en `VALIDACION_ACTUAL.md`.

**Actualización PT-07 / RF-MET-02 (07-10-2026):** se acordó incorporar telemetría real de tiempo activo: sesión autenticada, pestaña visible e interacción reciente, pausa tras cinco minutos inactivo, heartbeat cada 60 segundos y persistencia por sesión lógica más agregados diarios por empresa/usuario (sin guardar cada ping). La métrica principal será minutos activos medidos por usuario único con actividad en el período; no se agrega duración promedio por sesión. La duración heredada continúa siendo estimada. Las precisiones posteriores establecen períodos de días calendario inclusivos en `America/Santiago` (hoy, últimos 7 días, últimos 30 días o mes calendario) y suma de sesiones simultáneas. La población de usuarios de empresas excluye ADMIN de plataforma conforme a DEC-03. Detalle y agregados por usuario son identificables y sujetos a 90 días; agregados no identificables por empresa, hasta 12 meses tras aprobación DEC-08.

**Actualización PT-06 / RF-SAL-03 (07-10-2026):** DEC-06 acuerda conservar contexto de auditoría investigable (componente/proceso, operación, momento, resultado/error e identificador de correlación cuando estén disponibles) y asociar empresas solo con evidencia verificable. Impacto sin vínculo confirmado se presenta como global/indeterminado. Implementación, correlación entre servicios y aplicación de los controles de acceso/retención propuestos en DEC-08 quedan pendientes.

**Actualización PT-09 / DEC-07 (07-10-2026):** se acordó medir primero una línea base representativa de carga, latencia, disponibilidad, detección y recuperación. No se establece todavía porcentaje objetivo de disponibilidad ni SLA; los objetivos se propondrán tras medir y requerirán aprobación explícita.

**Actualización PT-04/06/07 / DEC-08 (07-10-2026):** se acordó como propuesta minimizar los datos de auditoría, restringir y auditar su consulta, exigir motivo solo para operaciones sensibles y aplicar retenciones iniciales de 12 meses para auditoría, 90 días para logs técnicos y 90 días para telemetría identificable, con métricas agregadas hasta 12 meses. Se excluyen contraseñas, tokens, URLs firmadas y contenido documental; una URL emitida no prueba una descarga. Los plazos requieren revisión legal/contractual antes de producción. Implementación, matriz de acceso, evidencia de transferencias cuando se requiera y tratamiento histórico siguen pendientes.

**Puerta de salida P0 — DEC-08 (07-10-2026):** no autorizar el paso a producción con datos reales hasta adjuntar evidencia de revisión legal/contractual, registrar quién revisó y aprobó y cuándo, resolver los plazos definitivos, asignar responsables y demostrar los controles de privacidad/auditoría mediante validación. La propuesta actual de retención no es aprobación. Esta puerta es un criterio de go/no-go, no una tarea que pueda darse por cerrada con la sola actualización documental.

| Paquete | Prioridad / estado | Requisitos | Trabajo concreto | Dependencias | Evidencia de cierre |
|---|---|---|---|---|---|
| PT-01 — Base de pruebas | P1 / completado en alcance de esta entrega | RNF-VAL-01 | Rutas/fixtures actualizados; índices de claves foráneas y migraciones versionadas. La línea base del 30-09 validó actualización desde esquema 7; esquema 9 incorpora `users.auth_version` para invalidar sesiones. | DEC-09 documenta compatibilidad vigente; no cambia la API. | Suite backend completa: 363/363 el 01-10-2026 en PostgreSQL temporal (EV-09). Extensiones reales, automatización reproducible y validación de despliegue continúan en PT-09. |
| PT-02 — Backend administrativo | P1 / en curso; defectos corregidos | RF-MET-03, RF-SAL-03 | Conversión UF y registro inproc corregidos; ADMIN 19/19, incluidos pausa, concurrencia, snapshot y auditoría. Resta recorrido distribuido Celery y completar aceptación de los requisitos. | Entorno aislado existente. | Los seis casos fallidos de ADMIN pasan sin relajar aserciones; prueba del recorrido Celery aparte. |
| PT-03 — Despliegue e aislamiento | P0 / en curso | RF-SEG-01/03, RNF-SEG-01 | PT-03-01 implementa modo producción con validación, semillas opt-in y recuperación sin token expuesto por defecto. Restan roles de mínimo privilegio reales, aprovisionamiento productivo, secretos/cuentas existentes, correo y pruebas negativas API/BD por empresa/contrato. DEC-10 exige autorización API; RLS contractual es defensa adicional condicionada a contexto confiable y pruebas viables. | PT-01 para pruebas negativas fiables. | Evidencia PT-03-01 en EV-01; API/worker sin superusuario ni BYPASSRLS; aislamiento probado por empresa/contrato y AT-01/02/03. Si se implementa RLS contractual, SQL directo y pruebas de contexto/transacciones; validación de despliegue sigue pendiente. |
| PT-04 — Permisos y auditoría | P0 / pendiente — bloquea go-live con datos reales | RF-SEG-02, RF-BUS-02, RF-USU-02, RF-AUD-01/02/03, RNF-PRV-01 | Se incorporó confirmación contextual y motivo obligatorio para cambios ADMIN de rol/empresa/contrato; la auditoría registra actor, motivo y valores anteriores/nuevos e invalida sesiones. Aún falta implementar la matriz y acceso excepcional acordados en DEC-01; extender cobertura auditora; controlar exportaciones; minimizar PII y aplicar retención. | DEC-08 (propuesta acordada; revisión legal/contractual obligatoria); DEC-01/02 cerradas; PT-03. | Validar cambios y auditoría con pruebas del flujo; matriz verificada por API, exportación y archivos restringidos al alcance autorizado, auditoría consultable y AT-04; revisión legal/contractual, plazos finales, aprobaciones y responsables documentados. Sin esa evidencia no se autoriza producción con datos reales. |
| PT-05 — Usuarios y buscador | P1 / en curso | RF-USU-01/02, RF-BUS-01 | Buscador implementado en cinco categorías con botones que despliegan listas, búsqueda multi-término, filtros de referencia y ficha por fila; quedan revisión visual y permisos efectivos por categoría/detalle. Usuarios ADMIN: cambios de alcance ahora requieren confirmación y motivo; aún faltan altas completas, invitación a pertenencia empresarial, paginación y aplicación de la guarda del último ADMIN. La vinculación entre empresas de DEC-13 es solo propuesta pendiente del cliente. | DEC-01/02 cerradas; DEC-13 pendiente de aprobación del cliente; PT-04 para nuevas autorizaciones. | Regresión backend y build web en VALIDACION_ACTUAL.md; probar exclusiones del alcance, controles de servidor, cambios de alcance/auditoría, último ADMIN, recorrido visual y ciclo integral de usuarios. Si se aprueba DEC-13, probar aceptación/rechazo del titular y autorización ADMIN; verificar que membresía y permisos no cambien antes de completar ambas aprobaciones. AT-05 parcial por permisos; AT-08 pendiente. |
| PT-06 — Salud y operación | P1 / en curso | RF-SAL-01/02/03, RF-AUD-01/03, RNF-OPE-01, RNF-PRV-01 | Salud de clientes ahora reúne actividad/adopción, usuarios por plan/industria y riesgos en detalles desplegables con ayuda contextual. Aplicar y probar umbrales DEC-04 con categorías explícitas sin usuarios/sin datos; completar totales/paginación, sondas reales de API/workers, detección de heartbeats vencidos y ejecución Celery distribuida. | DEC-04/06/07/08; PT-02/04. | AT-09; casos debajo/en/encima de umbrales y sin datos; incidentes correlacionables y consultables por actor autorizado, atribución empresarial comprobada, política de privacidad aplicada, cobertura de listas y recuperación de procesos. |
| PT-07 — Métricas y dashboard | P2 / en curso | RF-MET-01/02, RF-DAS-01/02 | Aplicar DEC-03: series separadas de solicitudes registradas, empresas aprobadas y clientes activos; distinguir cuentas habilitadas de actividad. `past_due` y otros estados no activos/trial se presentan aparte y no cuentan como clientes activos. DAU/WAU cuenta usuarios de empresas con actividad humana, sin ADMIN de plataforma ni eventos automáticos, con límites `America/Santiago`. Validar coherencia de planes/datos y fuente/fecha de UF. Implementar heartbeat de 60 s, registro por sesión lógica y agregados diarios según DEC-05, junto con retención DEC-08; permitir períodos día/7 días/30 días/mes calendario y sumar minutos concurrentes. Reservar MRR/crecimiento comercial a Métricas SaaS. | DEC-03/05 acordadas funcionalmente; DEC-08; PT-02. | Cálculos contrastados con fixtures y definición/universo/período/zona horaria visibles; promedio de minutos activos por usuario único con actividad; telemetría con pausa a 5 min, expiración, suma de sesiones simultáneas, sin persistencia de cada ping y con retención validada; metadatos UF y casos límite validados. |
| PT-08 — Empresas y portal | P1-P2 / en curso | RF-EMP-01/02, RF-CLI-01 a RF-CLI-09 | Registro con nombre del usuario inicial y sección Mi perfil implementados; aprobación normal de solicitud de registro verificada manualmente. Empresas (cuentas) incorpora industria, estado de cuenta y detalle de perfiles/responsables. Reportes ofrece seis tipos en PDF/CSV, historial, descarga y programación; los PDF incluyen metadatos, recuento y tablas paginadas. DEC-12 tiene implementación de desactivar/finalizar/restaurar, histórico, conservación de relaciones, restricciones de solo lectura y recálculo de alertas; validación backend focalizada completada. Rechazo/transiciones repetidas, invitaciones y activación por correo, recorrido visual, integraciones reales vs simuladas y aceptación integral siguen pendientes. El bloqueo de perfil de ADMIN durante «Ver como empresa» es solo de interfaz. | PT-03/04 para seguridad; DEC-12; EV-08 como inventario inicial. | `npm run build` completó correctamente. Regresión histórica de ocho suites: 247/247; además se repitieron 2 casos focalizados tras aquellos ajustes (resultado superpuesto, no sumar). Pruebas verifican permisos de empresa/ADMIN/contract_admin, mutaciones históricas, auditoría, conservación y alertas. La validación actual de Reportes no recolectó pruebas por falta de `pgserver` y no probó PDF en runtime por falta de ReportLab. Falta recorrido visual, probar API→Redis/Celery/almacenamiento y revisar procesos asíncronos; no acredita aceptación integral. |
| PT-09 — Entrega verificable | P1 / pendiente | RNF-REP-01, RNF-VAL-01, RNF-PER-01, RNF-REC-01, RNF-UX-01 | Dependencias reproducibles, automatización, análisis del aviso de dependencia, medición, respaldo/restauración, revisión responsive y validación completa de Reportes PDF/CSV. | DEC-07; requisitos funcionales del alcance de entrega. | Build limpio, suite completa, recuperación demostrada y reporte de límites; probar Reportes con API, worker y almacenamiento activos, incluidos PDF multipágina, CSV, permisos y fallos. |

P0 significa requisito previo a exposición con datos reales. La secuencia empieza por pruebas/correcciones porque permiten comprobar seguridad; no autoriza desplegar públicamente mientras PT-03/04 estén incompletos. La revisión legal/contractual y la evidencia de cierre de DEC-08 son una puerta de go/no-go, no una recomendación postergable. Tareas independientes de reproducibilidad pueden adelantarse.

## 2. Primera entrega ejecutable

**Objetivo:** contar con pruebas ADMIN fiables y corregir los dos defectos funcionales identificados.

**Avance del 30-09-2026 (registro histórico):** correcciones implementadas; regresión 295/295 en 484,26 s, incluidos ADMIN 19/19 y esquema 10/10 con migración 7→8. Evidencia en VALIDACION_ACTUAL.md. Los siete pasos siguientes quedaron ejecutados y conservan la secuencia de trabajo; no describen defectos todavía presentes. La suite posterior del 01-10-2026 pasó 363/363 en PostgreSQL temporal. Falta validar Celery distribuido y aplicar/verificar la migración necesaria en el entorno destino. El cierre de esta entrega no cierra todos los criterios de RF-MET-03, RF-SAL-03 o RNF-VAL-01.

1. Confirmar línea base focalizada: 13/19 pruebas ADMIN aprobadas; no reutilizar como total de la suite completa.
2. Ajustar conversión UF en la llamada SQL, manteniendo precisión y verificando resultado numérico; ejecutar el caso afectado y sus vecinos de métricas.
3. Registrar tareas administrativas para el modo `inproc` en el arranque correspondiente, sin depender de iniciar un worker Celery; verificar estado final y errores.
4. Ejecutar `test_admin.py` completo y conservar aserciones de permisos, errores, concurrencia y auditoría.
5. Alinear pruebas de versión de esquema y contrato de motivo. La prueba de aislamiento debe enviar un motivo válido para llegar al control de pertenencia.
6. Enumerar las cinco claves foráneas detectadas, decidir índices y preparar migración segura donde se necesiten; no alterar el chequeo para esconder relaciones.
7. Repetir la suite completa en contenedor temporal; registrar fecha, entorno, casos aprobados/fallidos y limitaciones de extensiones.

**Cierre:** no quedan fallos por rutas/esquema obsoletos ni por los dos defectos ADMIN identificados; los demás hallazgos quedan corregidos o explícitamente bloquean la aceptación. No declarar toda la plataforma validada solo porque ADMIN pase.

## 3. Preparación de la entrega de seguridad

- Implementar DEC-01/02: matriz actor × operación × alcance en servidor; cubrir ADMIN ordinario, acceso sensible excepcional y motivo, restricciones por categoría del buscador, usuarios sin empresa y actores revocados/sin permiso.
- Inventariar lecturas de credenciales necesarias para worker y prohibidas para API.
- Ensayar roles/migraciones en BD descartable antes de aplicar cambios a volúmenes actuales.
- Para cambios de esquema o permisos persistentes: documentar respaldo, verificación y recuperación.
- Casos mínimos: dos empresas, dos contratos de una empresa, documentos y reportes propios/ajenos, sesión vigente antes de cambiar el permiso.
- Cerrar mediante evidencias AT-01 a AT-04 y RF-AUD-03, no mediante revisión visual únicamente.

## 4. Tablero y ficha de tarea

Estados de trabajo: `Por definir` → `Lista` → `En curso` → `En validación` → `Terminada`. Usar `Bloqueada` con motivo y decisión/dependencia concreta; una tarea con pruebas fallidas no está terminada.

Cada tarea debe contener:

```text
ID: PT-XX-NN
Requisitos SRS:
Estado técnico del requisito:
Avance estimado (independiente del cronograma):
Fundamento del avance:
Validación (completa/parcial/no realizada):
Problema y evidencia actual:
Resultado esperado:
Alcance y exclusiones:
Decisiones y dependencias:
Responsable:
Criterios de aceptación:
Pruebas y datos de prueba:
Riesgo de migración / recuperación (si aplica):
Resultado y evidencia:
Estado / fecha:
```

Ejemplo: `PT-05-01`, ligado a `RF-BUS-01`: filtrar sujetos de tipo trabajador; usar persona y equipo con nombres similares; comprobar que el equipo no aparece en esa categoría y que el resultado conserva empresa y restricciones. La aceptación no se cumple únicamente porque la consulta devuelva 200.

## 5. Reglas de seguimiento

- Una entrega debe ser pequeña, revisable y tener criterio de cierre explícito.
- Actualizar estado y evidencia del SRS al terminar; conservar historial de validaciones anteriores con fecha.
- Separar defectos confirmados de propuestas de producto; resolver solo las decisiones que bloqueen la próxima tarea.
- No ejecutar altas, revocaciones, borrados ni reinicios de demo contra los datos habituales para probar: usar fixtures/entorno aislado.
- Conservar el avance declarado del cronograma. Usar las estimaciones individuales del SRS §2.5 con fundamento y pendientes; no convertir estados en porcentajes ni promediarlos sin pesos acordados. La aceptación se acredita mediante criterios y evidencia, independientemente del avance estimado.
- Antes de fijar fecha de entrega, asignar responsable y estimación a cada tarea lista.
