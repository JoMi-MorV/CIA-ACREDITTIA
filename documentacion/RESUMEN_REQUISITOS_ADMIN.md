# Resumen de requisitos ADMIN

**Corte:** 4 de octubre de 2026  
**Propósito:** resumir el estado técnico de las ocho prioridades ADMIN, distinguir lo implementado de lo validado y proponer criterios concretos para revisar su cierre.

Este documento es una guía de revisión, no una aceptación contractual ni una certificación de producción. Los estados reflejan los requisitos y la evidencia descritos en el [SRS](SRS.md) y en [VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md). `IV` significa implementado y validado dentro del alcance probado; `ISV`, implementado sin validación completa; `PAR`, parcial; `COR`, requiere corrección; y `PEN`, pendiente. Los porcentajes estimados del SRS no equivalen a porcentaje de cumplimiento validado.

## Resumen ejecutivo

| # | Prioridad | Estado actual | En síntesis |
|---|---|---|---|
| 1 | Dashboard global | **PAR** — RF-DAS-01/02 | Muestra contadores, acreditación, estados documentales y actividad por eventos. Falta acordar universos y definir cómo presentar el crecimiento. |
| 2 | Gestión global de empresas | **Mixto:** RF-EMP-01 **IV**; RF-EMP-02 **ISV** | La consulta de listado y ficha agregada está validada. Aprobación/rechazo requiere cerrar transiciones, auditoría y validación visual. |
| 3 | Buscador global | **PAR** — RF-BUS-01/02 | Búsqueda y filtros implementados; falta validación integral de interfaz y autorización efectiva por categoría/detalle en servidor. |
| 4 | Métricas SaaS | **PAR** — RF-MET-01/02/03 | Hay series e indicadores; faltan definiciones completas, precisión de las métricas de uso y metadatos/casos adicionales de conversión UF. |
| 5 | Alertas y salud de clientes | **Mixto:** RF-SAL-01 **PAR**; RF-SAL-02 **COR**; RF-SAL-03 **ISV** | Hay riesgos y procesos implementados parcialmente; faltan clientes sin actividad bien clasificados, sondas operacionales verificables y recorrido distribuido. |
| 6 | Usuarios, roles y permisos | **PAR** — RF-USU-01/02 | Listado, cambios de estado y reactivación existen; faltan altas completas, paginación/recorrido visual y validación integral de alcance. |
| 7 | Auditoría y trazabilidad | **PAR** — RF-AUD-01/02/03 | Hay registro parcial y ciertos accesos con motivo; falta cobertura de operaciones, historial de autenticación y controles uniformes para acceso sensible/exportaciones. |
| 8 | Seguridad y aislamiento | **PAR** — RF-SEG-01/02/03, RNF-SEG-01 | Hay controles de aplicación y políticas definidas, pero falta demostrar aislamiento y mínimo privilegio con configuración equivalente a producción y cerrar el acceso excepcional. |

## 1. Dashboard global

**Estado:** PAR — RF-DAS-01 y RF-DAS-02.

**Lo que hace hoy**

- Muestra cantidades de empresas, contratos, trabajadores y usuarios; distingue empresas aprobadas, trabajadores acreditados y usuarios con cuenta habilitada.
- Calcula acreditación ponderada por número de documentos obligatorios correctos de empresas aprobadas. También existe un promedio simple por empresa en la respuesta del backend, pero la pantalla presenta el porcentaje global ponderado.
- Muestra documentos pendientes, por vencer y vencidos.
- Presenta una serie mensual y un total de actividad expresados como eventos. No equivale a nuevas empresas, nuevos usuarios ni tiempo efectivo de uso.
- Algunos universos difieren: por ejemplo, el contador de usuarios excluye ADMIN y los documentos de la sección de estados no están restringidos a empresas aprobadas.

**Sugerencias y criterios a considerar**

1. Definir para cada contador su universo y exclusiones: estados de empresa, tipos de usuario, bajas, documentos obligatorios y si se incluyen empresas no aprobadas.
2. Etiquetar la acreditación como porcentaje ponderado por documentos y mostrar numerador/denominador o una explicación accesible.
3. Mantener actividad por eventos separada de crecimiento de adopción.
4. Propuesta de crecimiento: presentar empresas nuevas y usuarios nuevos por mes, con períodos y universos visibles; validar por separado la definición de alta de empresa/usuario y el tratamiento de registros desactivados.
5. Contrastar cada tarjeta y punto de serie con fixtures conocidos, incluyendo cero empresas/documentos, meses sin actividad y cambios de período.
6. No presentar métricas comerciales en el Dashboard; mantener MRR y crecimiento comercial en Métricas SaaS.

**Para considerar el punto validado:** definiciones acordadas y visibles, cálculos reproducibles con datos controlados, meses vacíos representados correctamente y ausencia de información personal/documental innecesaria. La propuesta de crecimiento requiere confirmación funcional antes de tratarla como alcance aprobado.

## 2. Gestión global de empresas

**Estado:** RF-EMP-01 **IV** para lectura; RF-EMP-02 **ISV** para aprobar/rechazar.

**Lo que hace hoy**

- El listado recupera las páginas de empresas y presenta estado, contratos, trabajadores, actividad y un acceso a la ficha agregada.
- Los trabajadores dados de baja no cuentan; el conteo de contratos no filtra por estado.
- El nivel de uso se calcula como cuentas con actividad registrada en los últimos 30 días dividido por las cuentas de la empresa. No representa duración ni necesariamente la proporción de cuentas habilitadas.
- La última actividad es el evento más reciente registrado y puede ser automático, no solo una acción humana.
- La ficha operativa presenta datos agregados y último evento/actor. No muestra RUT, email ni contenido documental en la vista revisada.
- La respuesta de detalle incluye `rejection_reason`, que la pantalla no utiliza; su necesidad para esta vista merece revisión.
- Aprobar/rechazar dispone de interfaz/endpoints y pruebas básicas, pero las transiciones, auditoría completa y recorrido visual no están cerrados.

**Sugerencias y criterios a considerar**

1. Conservar los conteos actuales solo si se aprueban expresamente las reglas de inclusión de contratos y trabajadores.
2. Etiquetar el porcentaje como “uso de cuentas con actividad en últimos 30 días” y mostrar su numerador/denominador; no llamarlo tiempo de uso.
3. Etiquetar “última actividad” como evento más reciente y aclarar que puede ser automático.
4. Retirar `rejection_reason` de esta respuesta si no existe una necesidad funcional de mostrarlo aquí; si se necesita, devolverlo solo en la vista/flujo autorizado que lo utiliza.
5. Validar el ciclo de aprobación/rechazo con estados permitidos, motivo requerido cuando corresponda, rechazo de transiciones inválidas y registro de actor/fecha/resultado.
6. Probar empresa sin usuarios, sin plan, sin eventos, sin contratos y sin documentos, además de paginación completa.

**Para considerar el punto validado:** lectura completa comprobada; etiquetas coincidentes con las fórmulas; datos sensibles minimizados; ficha correspondiente a la empresa elegida; y aprobación/rechazo con reglas y auditoría verificadas por pruebas y recorrido de interfaz.

## 3. Buscador global

**Estado:** PAR — RF-BUS-01 y RF-BUS-02.

**Lo que hace hoy**

- Busca empresas, contratos, trabajadores/personas, equipos y usuarios, con filtros por categoría y filtros específicos.
- Incluye búsqueda por RUT para empresas y sujetos; no asigna RUT propio a las cuentas de acceso ni devuelve el RUT en los resultados.
- Los filtros de cargo y tipo de equipo se alimentan de catálogos.
- Permite buscar con texto vacío cuando hay filtros específicos; si no los hay, solicita al menos dos caracteres.
- La ficha agregada se abre debajo de la fila concreta elegida; solo se mantiene una abierta y se descartan respuestas tardías al cambiar búsqueda/fila o cerrar.
- Persiste el pendiente de alcance de usuarios sin empresa. El acceso por categoría no se valida como una matriz independiente de permisos; se exige ADMIN.

**Sugerencias y criterios a considerar**

1. Definir la matriz actor × categoría × operación (búsqueda, ficha y campos visibles); aplicar autorización en servidor en cada solicitud.
2. Acordar el tratamiento de usuarios sin empresa y otras cuentas globales; no incluirlos/excluirlos silenciosamente.
3. Probar directamente la API como actor sin permiso, además de ocultar o deshabilitar controles en la interfaz.
4. Validar resultados por categoría, límites, filtros con texto vacío, catálogos vacíos, cambio rápido de filtro y respuestas tardías.
5. Mantener la minimización: sin RUT, documentos, tokens ni campos personales que no sean necesarios para identificar el resultado.

**Para considerar el punto validado:** autorización efectiva y negativa por API para cada categoría y detalle, resultados correctos y minimizados, y recorrido de interfaz probado para filtros, límites y apertura/cierre.

## 4. Métricas SaaS

**Estado:** PAR — RF-MET-01, RF-MET-02 y RF-MET-03.

**Lo que hace hoy**

- Hay indicadores de clientes activos, usuarios habilitados, DAU/WAU, actividad, revisiones de IA y series comerciales.
- Se cuentan sesiones vigentes usando refresh tokens.
- No existe una medición de duración de sesión plenamente observada: el tiempo de uso y la duración promedio se etiquetan como estimados y se derivan de eventos/tokens.
- Hay documentos procesados y series mensuales, pero debe conservarse la distinción entre revisiones/intentos y documentos únicos.
- Se calculan clientes con baja actividad en backend; falta que queden visibles de forma suficiente en la vista de métricas.
- La conversión UF tiene un caso mensual probado, pero la respuesta aún requiere identificar fecha/fuente de UF y completar cobertura de períodos/monedas.

**Sugerencias y criterios a considerar**

1. Aprobar un diccionario de métricas: nombre, definición, fuente, ventana temporal, unidad y universo.
2. Diferenciar “cuentas habilitadas”, “usuarios con actividad”, DAU/WAU y “sesiones vigentes”; no usarlos como equivalentes.
3. Mantener la etiqueta “estimado” en tiempo/duración hasta que exista telemetría de sesión lógica acordada.
4. Definir si documentos procesados cuenta revisiones, resultados completados o documentos únicos; mostrar estados fallidos/en proceso por separado cuando corresponda.
5. Mostrar clientes de baja actividad y especificar umbral, ventana temporal y casos sin usuarios/sin actividad.
6. Identificar fecha y fuente del valor UF; probar períodos mensual/anual, monedas admitidas, suscripción ausente y acceso denegado.

**Para considerar el punto validado:** diccionario aprobado, cifras contrastadas con fixtures, ausencia de datos diferenciada de cero y etiquetas/unidades/ventanas visibles y coherentes.

## 5. Alertas y salud de clientes

**Estado:** RF-SAL-01 **PAR**; RF-SAL-02 **COR**; RF-SAL-03 **ISV**.

**Lo que hace hoy**

- Calcula empresas con acreditación bajo el umbral existente, contratos con al menos tres documentos faltantes/vencidos, vencidos por empresa, morosidad y alertas activas.
- Hay límites en las listas de contratos (25) y alertas (50); la cantidad visible no siempre representa el total global.
- La clasificación de baja actividad no cubre de forma explícita todos los casos de empresas sin usuarios habilitados o empresas con usuarios sin eventos.
- Existen panel y heartbeats operacionales, pero las sondas actuales no acreditan por sí solas disponibilidad real de API/workers.
- Procesos e incidentes tienen catálogo y acciones; ejecución manual inproc fue corregida/probada, pero falta recorrido distribuido Celery.

**Sugerencias y criterios a considerar**

1. Acordar umbrales y ventanas para baja acreditación, “muchos pendientes”, inactividad y expiración de heartbeat.
2. Clasificar por separado empresa sin usuarios, empresa con usuarios sin eventos, empresa sin documentos y empresa saludable.
3. Mostrar total real, límite y mecanismo para recuperar el resto; no llamar “total” a la longitud de una muestra.
4. Probar casos justo por debajo, en y por encima de cada umbral y con más registros que el límite.
5. Comprobar que la API se detecta caída aunque el worker siga activo, y que cola vacía no se interpreta como worker disponible.
6. Ejecutar el flujo distribuido de Celery, reintento y cierre de incidente con actor, resultado y timestamps trazables.

**Para considerar el punto validado:** umbrales acordados, casos límite probados, totales completos/paginación definidos y sondas capaces de detectar fallos reales en API, worker y base de datos.

## 6. Usuarios, roles y permisos

**Estado:** PAR — RF-USU-01 y RF-USU-02.

**Lo que hace hoy**

- Existen roles `admin`, `company` y `contract_admin`, alcance por empresa/contrato, listado y cambios administrativos de estado.
- La reactivación de cuentas e invalidación de sesiones anteriores está implementada y probada en pruebas aisladas; el SRS registra pendiente aplicar migración al entorno habitual.
- Listado de usuarios solicita hasta 100 y no presenta navegación completa para universos mayores.
- Backend valida que el contrato pertenezca a la empresa; la interfaz puede enviar combinaciones inválidas que backend rechaza.
- El último acceso se conserva en `last_login_at`, pero no sustituye un historial de autenticación.

**Sugerencias y criterios a considerar**

1. Aprobar la matriz de roles y permisos por empresa/contrato, incluyendo ADMIN y cuentas sin empresa.
2. Probar que cambiar cuerpo, URL o identificadores nunca permita acceder a otra empresa/contrato.
3. Asegurar que rol, empresa y contrato se guarden como una combinación coherente, sin cambios parciales cuando hay error.
4. Completar altas/invitaciones y paginación o navegación por encima de 100 usuarios.
5. Validar en navegador crear/editar/revocar/reactivar, errores, confirmaciones e identidad del destinatario.
6. Aplicar y validar la migración pendiente en el entorno destino antes de considerar operativo el flujo allí.

**Para considerar el punto validado:** matriz probada contra API, aislamiento empresa/contrato, ciclo completo de usuario y navegación sin omisiones; ninguna cuenta revocada conserva acceso o refresh válido.

## 7. Auditoría y trazabilidad

**Estado:** PAR — RF-AUD-01, RF-AUD-02 y RF-AUD-03.

**Lo que hace hoy**

- Hay eventos de actividad y auditoría para operaciones seleccionadas; la creación global de faenas es consultable.
- Ciertos cambios de usuario y solicitudes de URL documental registran actor/fecha; la emisión de URL requiere motivo.
- `last_login_at` y refresh tokens existen, pero no hay historial completo consultable de ingreso, fallo, cierre y revocación.
- La cobertura de catálogos y eliminaciones es incompleta; algunos borrados se registran con semántica de actualización.
- Reportes/exportaciones no tienen justificación uniforme, y lecturas de metadatos sensibles no se auditan de manera integral en todos los handlers revisados.

**Sugerencias y criterios a considerar**

1. Acordar catálogo de acciones auditables y campos: actor, sujeto afectado, operación, recurso, tenant/contrato, fecha UTC, resultado y motivo cuando aplique.
2. Registrar valores anteriores/nuevos para cambios de permisos sin almacenar contraseñas, tokens u otros secretos.
3. Diferenciar inequívocamente creación, actualización, eliminación física, desactivación, revocación y reactivación.
4. Incorporar eventos de autenticación exitosos/fallidos, cierre y revocación, correlacionados con sesión sin guardar credenciales.
5. Clasificar datos sensibles y definir cuándo se requiere motivo para lectura, URL, descarga o exportación.
6. Diferenciar solicitud de URL de transferencia efectiva; determinar si se necesita confirmación del almacenamiento para acreditar una descarga.
7. Definir retención y quién puede consultar auditoría.

**Para considerar el punto validado:** pruebas por operación que verifiquen actor/recurso/alcance/resultado, registro consultable incluso para actores sin empresa cuando corresponda, y ausencia de secretos/PII innecesaria.

## 8. Seguridad y aislamiento de datos

**Estado:** PAR — RF-SEG-01/02/03 y RNF-SEG-01.

**Lo que hace hoy**

- Hay filtros de autorización en la aplicación, dependencias y políticas RLS definidas.
- Algunas pruebas de aislamiento pasan, pero la configuración Compose revisada utiliza superusuario PostgreSQL, por lo que no demuestra que RLS proteja efectivamente a la aplicación.
- El alcance contractual se comprueba principalmente en la API; no se identificó política RLS contractual independiente en los scripts revisados.
- ADMIN conserva privilegio global; no hay flujo completo de acceso excepcional temporal/limitado a documentos sensibles.
- Existen guardas de configuración de producción y respuesta minimizada en áreas revisadas; despliegue, roles y secretos productivos aún requieren validación.
- Emisión de URL documental requiere motivo y controles de pertenencia, pero la auditoría de toda lectura sensible/exportación sigue parcial.

**Sugerencias y criterios a considerar**

1. Probar con empresas A/B y dos contratos de A: lectura, listado, modificación, eliminación, archivos y exportaciones; comprobar denegación cruzada.
2. Ejecutar pruebas con credenciales equivalentes a producción: API/worker sin superusuario, `BYPASSRLS` ni propiedad de tablas.
3. Decidir en DEC-10 si el aislamiento contractual también se impone por RLS y cómo se propaga el contexto; no presentarlo como implementado antes de probar SQL directo.
4. Definir mínimo privilegio para ADMIN y acceso excepcional por capacidad, recurso y duración; selección de empresa no debe equivaler a acceso ilimitado.
5. Exigir actor, cuándo, recurso y motivo en accesos excepcionales; probar autorización/denegación por API.
6. Revisar dashboards, logs, respuestas, reportes y exportaciones para retirar RUT, documentos y PII que no sean necesarios.
7. Validar secretos, recuperación de cuenta, semillas demo y migraciones en configuración de producción aislada.

**Para considerar el punto validado:** pruebas negativas multiempresa/contrato en API y BD con rol de aplicación real, mínimo privilegio demostrado, accesos sensibles/exportaciones controlados y auditados, y revisión de privacidad aprobada.

## Orden sugerido de revisión

1. Confirmar definiciones de métricas y universos (puntos 1 y 4).
2. Cerrar matriz de roles/alcances y seguridad (puntos 6 y 8), prerrequisito para permisos del buscador y accesos sensibles.
3. Completar auditoría de operaciones y lecturas (punto 7).
4. Cerrar buscador, gestión de empresas y salud con esas reglas aplicadas (puntos 2, 3 y 5).
5. Ejecutar regresión integral y recorridos de navegador; registrar evidencia, límites y decisiones aprobadas.

La secuencia es una propuesta de trabajo, no un cambio automático de alcance. Cada requisito conserva su estado del SRS hasta que exista evidencia de sus criterios de aceptación o una decisión explícita sobre alcance.
