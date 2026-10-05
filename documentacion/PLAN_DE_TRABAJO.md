# Plan de trabajo — Acredittia

Versión 0.6 · 05-10-2026 · propuesta de ejecución vinculada a [SRS.md](SRS.md) versión 0.21.

**Actualización al 05-10-2026:** los avances de PT-05, PT-06, PT-07 y PT-08
incorporan cambios posteriores a la versión 0.5. La tabla refleja el trabajo
realizado y separa la implementación de la validación aún pendiente. Los
porcentajes, estados y evidencias anteriores se conservan como historial; esta
actualización no declara aceptación de producto ni cierre de requisitos.

**Avance PT-05-03 (30-09-2026):** API identifica recorte por categoría y la interfaz distingue resultados mostrados de coincidencias completas. Falta recorrido visual; se conservan pendientes de permisos y alcance. Evidencia en VALIDACION_ACTUAL.md.

**Avance PT-05-02 (30-09-2026):** validación de consultas vacías/cortas tras normalizar espacios y límites 2/100 comprobados. Buscador + ADMIN: 32/32; evidencia en VALIDACION_ACTUAL.md. RF-BUS-01 sigue parcial; faltan presentación de límites y decisiones de alcance/permisos.

No es una lista de nuevas funciones aprobadas automáticamente. Se priorizan correcciones confirmadas; las reglas nuevas sujetas a `DEC-*` se definen antes de implementarse. Responsables personales, estimaciones y fechas están por asignar; no se inventan plazos sin revisar el esfuerzo.

## 1. Secuencia de entregas

**PT-05-04 (30-09-2026):** Reactivar disponible en Usuarios mediante PATCH existente; cambios de estado ADMIN invalidan JWT/refresh anteriores. Esquema 9, migración `10_version_sesion.sql`. Pruebas en EV-01; altas, paginación, auditoría integral y navegador pendientes. No se migró el entorno habitual.

**PT-05-05 (30-09-2026):** identificación de cuentas mediante nombre y correo real en gestión ADMIN; alternativa legible para cuentas sin nombre y confirmaciones con correo. RF-USU-01 permanece PAR. Pruebas de acceso e identidad y build en EV-01; recorrido visual pendiente.

**PT-03-02 (30-09-2026):** guarda de conexiones nuevas en producción para API/Celery contra roles privilegiados o propietarios de tablas. Validación con PostgreSQL efímero en EV-01. La separación efectiva de credenciales y el cambio de Compose continúan pendientes; no se modifica el estado PAR de seguridad.

**Avances posteriores (05-10-2026):**

- **PT-05 / RF-BUS-01:** filtros de cargo y tipo de equipo conectados a catálogos; búsqueda con texto vacío cuando hay filtros específicos; ficha expandible bajo la fila seleccionada, una sola abierta, con descarte de respuestas tardías. Está documentado por revisión del código; falta recorrido visual y prueba específica de estos comportamientos.
- **PT-06/07 / RF-SAL-01 y RF-MET-01/02:** Métricas SaaS presenta clientes sin usuarios, usuarios sin actividad y con baja actividad, además de un diccionario de definiciones. Se mantiene pendiente la validación de umbrales, listas limitadas, métricas de sesión y sondas operacionales.
- **PT-08 / RF-CLI-01:** el registro solicita el nombre del usuario inicial y `/perfil` permite editar nombre, correo y contraseña sin migración. `tests/test_auth.py` pasó 34/34 y el build web generó 23 rutas. El bloqueo de perfil de ADMIN durante «Ver como empresa» está implementado como control de interfaz, no como autorización backend. Invitaciones por correo y validación visual completa siguen pendientes.

| Paquete | Prioridad / estado | Requisitos | Trabajo concreto | Dependencias | Evidencia de cierre |
|---|---|---|---|---|---|
| PT-01 — Base de pruebas | P1 / completado en alcance de esta entrega | RNF-VAL-01 | Rutas/fixtures actualizados; índices de claves foráneas y migraciones versionadas. La línea base del 30-09 validó actualización desde esquema 7; esquema 9 incorpora `users.auth_version` para invalidar sesiones. | DEC-09 documenta compatibilidad vigente; no cambia la API. | Suite backend completa: 363/363 el 01-10-2026 en PostgreSQL temporal (EV-09). Extensiones reales, automatización reproducible y validación de despliegue continúan en PT-09. |
| PT-02 — Backend administrativo | P1 / en curso; defectos corregidos | RF-MET-03, RF-SAL-03 | Conversión UF y registro inproc corregidos; ADMIN 19/19, incluidos pausa, concurrencia, snapshot y auditoría. Resta recorrido distribuido Celery y completar aceptación de los requisitos. | Entorno aislado existente. | Los seis casos fallidos de ADMIN pasan sin relajar aserciones; prueba del recorrido Celery aparte. |
| PT-03 — Despliegue e aislamiento | P0 / en curso | RF-SEG-01/03, RNF-SEG-01 | PT-03-01 implementa modo producción con validación, semillas opt-in y recuperación sin token expuesto por defecto. Restan roles BD reales, aprovisionamiento productivo, secretos/cuentas existentes y correo. Resolver RLS contractual/contexto en DEC-10. | PT-01 para pruebas negativas fiables. | Evidencia PT-03-01 en EV-01; AT-01/02/03 y validación de despliegue siguen pendientes de cierre integral. |
| PT-04 — Permisos y auditoría | P0 / pendiente | RF-SEG-02, RF-BUS-02, RF-USU-02, RF-AUD-01/02/03, RNF-PRV-01 | Definir matriz y acceso excepcional; historial de accesos/cambios, actores sin empresa, valores anteriores/nuevos, catálogos globales, semántica de eliminaciones, PII en textos libres, lecturas de metadatos sensibles y exports. | DEC-01/02/08; PT-03. | Matriz verificada por API, auditoría consultable y AT-04. |
| PT-05 — Usuarios y buscador | P1 / en curso | RF-USU-01/02, RF-BUS-01 | Buscador implementado en cinco categorías con filtros de catálogo y ficha por fila; quedan revisión visual, alcance de usuarios sin empresa, permisos por categoría y límites. Usuarios ADMIN: reactivación e identificación por nombre/correo; faltan altas completas, paginación y edición coherente del alcance. | DEC-02; PT-04 para nuevas autorizaciones. | Regresión de backend del buscador y revisión de UI en VALIDACION_ACTUAL.md; pruebas/recorrido visual de los cambios recientes del buscador pendientes. AT-05 parcial por permisos; AT-08 y ciclo completo de usuarios pendientes. |
| PT-06 — Salud y operación | P1 / en curso | RF-SAL-01/02/03, RNF-OPE-01 | Mantener clasificación de clientes de baja actividad ya visible en Métricas SaaS. Completar totales/paginación de bandejas, umbrales y casos límite, impacto solo con vínculo verificable, sondas reales de API/workers y detección de heartbeats vencidos; validar ejecución Celery distribuida. | DEC-04/06/07; PT-02. | AT-09, escenarios de umbrales, cobertura de listas y prueba de recuperación de procesos. |
| PT-07 — Métricas y dashboard | P2 / en curso | RF-MET-01/02, RF-DAS-01/02 | Diccionario de métricas y clasificación de baja actividad implementados en Métricas SaaS. Restan universos acordados para dashboard, coherencia de planes/datos, fuente y fecha de UF, precisión de métricas y telemetría observada de sesión (si se aprueba). Reservar MRR/crecimiento comercial a Métricas SaaS. | DEC-03/05; PT-02. | Cálculos contrastados con fixtures y definiciones/unidades/períodos consistentes; resolver metadatos UF y validar casos límite. |
| PT-08 — Empresas y portal | P1-P2 / en curso | RF-EMP-01/02, RF-CLI-01 a RF-CLI-09 | Registro con nombre del usuario inicial y sección Mi perfil implementados; control de interfaz para ocultar/bloquear perfil durante «Ver como empresa». Continúan pendientes ciclo de aprobación de empresa, invitaciones y activación por correo, recorridos visuales y validaciones integrales de formularios, calendario, documentos, exports e integraciones reales vs simuladas. | PT-03/04 para seguridad; EV-08 como inventario inicial. | `test_auth.py` 34/34 y build web con 23 rutas; evidencia en VALIDACION_ACTUAL.md. Completar recorridos funcionales y pruebas negativas por actor; las pruebas actuales no acreditan aceptación integral. |
| PT-09 — Entrega verificable | P1 / pendiente | RNF-REP-01, RNF-VAL-01, RNF-PER-01, RNF-REC-01, RNF-UX-01 | Dependencias reproducibles, automatización, análisis del aviso de dependencia, medición, respaldo/restauración y revisión responsive. | DEC-07; requisitos funcionales del alcance de entrega. | Build limpio, suite completa, recuperación demostrada y reporte de límites. |

P0 significa requisito previo a exposición con datos reales. La secuencia empieza por pruebas/correcciones porque permiten comprobar seguridad; no autoriza desplegar públicamente mientras PT-03/04 estén incompletos. Tareas independientes de reproducibilidad pueden adelantarse.

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

- Definir DEC-01/02: matriz actor × operación × alcance; incluir administrador global sin empresa, revocado y actor con permiso insuficiente.
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
