# Estado de salud general de Acredittia

**Fecha de corte:** 14 de noviembre de 2026
**Preparado para:** revisión técnica, operativa y de gestión  
**Alcance:** backend, frontend, SQL/migraciones, seguridad, privacidad, continuidad operativa, documentación y preparación para producción.

## Resumen ejecutivo

El proyecto presenta una base técnica sólida para desarrollo y validación focalizada, pero aún no alcanza un estado de madurez compatible con producción real. El backend muestra estabilidad funcional y la mayoría de las capas de aplicación tienen evidencia concreta; sin embargo, el conjunto presenta riesgos de integración, seguridad, requisitos de cumplimiento por confirmar y continuidad que siguen bloqueando el paso a producción con datos reales.

La evaluación actual se mantiene en **NO GO** para producción. La mejora más importante desde el último corte es que el código y la documentación han convergido hacia una visión más realista: el proyecto no se presenta como “listo para producción”, sino como una plataforma con avances relevantes y con bloqueadores específicos todavía abiertos.

### Actualización de avance — 14 de noviembre de 2026

RF-DAS-01 pasa de 90% a 100% tras definir los universos de sus KPI, alinear los
conteos documentales con el universo de acreditación y representar la ausencia
de datos evaluables como “N/A”. La prueba focalizada pasó 2/2, el build
frontend compiló y validó tipos y el usuario confirmó la revisión visual. El
avance estimado de las 37 fichas queda en 2.928/37 = **79,1%**; las ocho
prioridades ADMIN promedian **79,2%**, y P1 84,7%, P0 72,2%, P2 69,2%.
RF-DAS-01 queda IV/100% en su alcance funcional. El estado de producción sigue
**NO-GO**.

### Actualización de avance — 12 de noviembre de 2026

Se reevaluaron RF-CLI-01 (75% → 80%) y RF-SAL-03 (90% → 95%) tras los cambios
de confirmación de correo y seguimiento de procesos, con pruebas focalizadas
de autenticación/esquema y operaciones/esquema, respectivamente, y build
frontend aprobado. La suma directa de las 37 fichas da 2.908/37 = 78,6% antes
de estos cambios y 2.918/37 = **78,9%** después; el agregado anterior 2.888 no
coincidía con los valores individuales y se corrige. Las ocho prioridades ADMIN
pasan de 77,1% a **77,3%**, Salud de 81,7% a **83,3%**; desde requisitos
individuales, P0 queda en 72,2%, P1 en 84,2% y P2 en 69,2%. Esto no cambia la
conclusión de salud ni el **NO GO**: siguen pendientes
validación integral, SMTP real, recuperación completa de contraseña,
trazabilidad/recuperación distribuida y bloqueadores de seguridad, privacidad
y continuidad. El detalle y los límites de evidencia están en
[VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md) y [GAP_ANALYSIS.md](GAP_ANALYSIS.md).

| Área | Estado | Evaluación |
|---|---|---|
| Backend | 🟢 Verde | Evidencia funcional sólida y pruebas relevantes aprobadas. |
| Frontend | 🟡 Amarillo | Build funcional; sin embargo, persisten dependencias con vulnerabilidades reportadas. |
| Docker / composición | 🟢 Verde | Validación de configuración y ejecución en entorno local consistente. |
| Seguridad técnica | 🟡 Amarillo | Hay guardas de RLS, JWT y producción; falta validación real en entorno objetivo. |
| Privacidad / RNF-PRV-01 | 🔴 Rojo / P0 | `ops_retencion` está activo y el usuario reporta ejecución local `ok` el 10-11-2026 00:18:52 (0 filas podadas); faltan Log Analytics, revisión histórica documentada y aprobación de producción. |
| Auditoría administrativa / RF-AUD-01 | 🟡 Parcial, 90% / P0 | 71 pruebas de `test_ops.py` y `test_contratos.py` pasaron; el usuario confirmó las mutaciones acordadas registradas. Pendiente único: comprobar valores anterior/nuevo para permisos/estados y pausa de procesos cuando corresponda. |
| Buscador global | 🟢 RF-BUS-01 y RF-BUS-02 cerrados (IV, 100%) | 83 pruebas focalizadas validan autorización por categoría, concesiones (titular, vigencia, revocación y alcance), ficha directa y exportación ZIP limitada; build frontend aprobado. El listado administrativo independiente de usuarios continúa bajo RF-USU. No se realizó recorrido manual de navegador. |
| Ajustes de negocio ADMIN | 🟢 Implementado | UF/vigencia/fuente, CAC, margen bruto y objetivo de churn son persistentes; solo ADMIN puede modificarlos, motivo obligatorio y auditoría con antes/después. Migración 17; suites focalizadas 86 aprobadas y build frontend correcto. La fuente UF es manual. |
| Recuperación y continuidad | 🔴 Rojo | Faltan pruebas de restauración real y objetivos RPO/RTO certificados. |
| Documentación y arquitectura | 🟡 Amarillo | Buena cobertura documental; SRS v0.86 refleja el recálculo actual, aunque persisten rutas heredadas, decisiones pendientes y verificaciones de consistencia por completar. |
| Producción con datos reales | 🔴 No GO | Bloqueado por seguridad, continuidad, controles de privacidad y validación operativa. |

## 1. Alcance y método de auditoría

Se revisó de forma transversal:

- Estructura del repositorio y coherencia entre raíz, `BASE/app` y `modelo_datos`.
- Documentación principal y operativa: [README.md](../README.md), [documentacion/ESTADO_SALUD_GENERAL.md](ESTADO_SALUD_GENERAL.md), [documentacion/VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md), [documentacion/estructura_repositorio_unificado.md](estructura_repositorio_unificado.md).
- Configuración de entorno y arranque: [BASE/app/backend/app/config.py](../BASE/app/backend/app/config.py).
- Conexión y aislamiento por tenant: [BASE/app/backend/app/database.py](../BASE/app/backend/app/database.py).
- Arranque de API, healthchecks y routers: [BASE/app/backend/app/main.py](../BASE/app/backend/app/main.py).
- Estado operativo y documentación de repositorio: [README_ops_Back.md](../README_ops_Back.md), [README_ops_Front.md](../README_ops_Front.md).

La auditoría no concluye que el proyecto esté “roto”; concluye que está bien avanzado para una etapa de maduración funcional, pero aún no validado para una implementación con datos reales ni para una operación de producción.

## 2. Hallazgos clave

### 2.1. Backend: maduro para validación, no para producción

El backend tiene evidencia funcional relevante:

- La suite completa de backend registra ejecuciones exitosas con pruebas aprobadas.
- Hay validación de salud, esquemas y autenticación.
- La aplicación incluye guardas de producción, separación de migraciones y protección de contexto multi-tenant.

Sin embargo, esta madurez funcional no sustituye:

- validación real en entorno objetivo,
- pruebas de recuperación ante falla real,
- roles PostgreSQL reales y certificados,
- validación de permisos minimos y auditoría de operaciones sensibles,
- validación de secret management en despliegue real.

### 2.2. Frontend: build funcional, pero con deuda técnica material

El frontend compila y la configuración Docker/Next parece estar operativa. Sin embargo, la deuda no es menor:

- `npm audit --omit=dev` reporta vulnerabilidades de dependencias.
- El riesgo principal se concentra en `next`, `postcss` y `source-map-js`.
- Aun cuando la aplicación arranca, la dependencia directa con un framework crítico no puede asumirse segura en un entorno externo o público.

Esto obliga a corregir primero la seguridad de dependencias antes de cerrar cualquier decisión de go-live.

### 2.3. Drift de arquitectura y documentación

Uno de los hallazgos más importantes es la diferencia entre la documentación “objetivo” y la realidad del repositorio:

- La raíz del proyecto no está unificada como monorepo final; la estructura real sigue siendo `BASE/app` y `BASE/modelo_datos`.
- La documentación habla de una unificación de repositorios y de un esquema objetivo que aún no está reflejado en la estructura vigente.
- Hay mezcla de rutas históricas (`/ops`) y rutas actuales (`/admin`), además de compatibilidad de API (`/api/v1/admin` y `/api/v1/admin/ops`).
- La versión de esquema documentada no es completamente consistente con la configuración real del backend.

Esto no invalida el trabajo, pero sí indica una falta de estándar de despliegue y un riesgo de confusión operativa y de integración.

### 2.4. Seguridad: la base existe, pero no está cerrada

La capa de seguridad del backend tiene elementos relevantes:

- validación de producción para JWT,
- rechazo de tokens de recuperación y semillas demo en producción,
- RLS y contexto de tenant,
- guardas de runtime para roles PostgreSQL inseguro,
- separación clara entre migración y ejecución.

Pero el proyecto todavía está lejos de la evidencia de producción:

- no se ha validado un rol real de PostgreSQL con privilegios mínimamente necesarios,
- no hay evidencia de despliegue real con secretos de entorno y rotación,
- no hay validación de acceso por empresa/usuario/rol bajo un escenario real,
- no hay evidencia de pruebas negativas exhaustivas para permisos sensibles.

### 2.5. Privacidad y cumplimiento no resueltos

DEC-08 quedó acordada como política interna funcional el 9 de noviembre de 2026: auditoría 12 meses, logs técnicos 90 días, telemetría identificable 90 días y métricas agregadas no identificables 12 meses. La aplicación ya minimiza datos en persistencia, respuestas y exportaciones; registra lecturas de auditoría y limita las exportaciones por motivo. En PostgreSQL, el usuario confirmó `max(app_schema_migrations.version)=16` y `privacy_retention_policy.effective_at=2026-11-09 03:00:00+00` (medianoche local UTC−03). También confirmó el job `ops_retencion` activo y reportó una ejecución manual desde Sistemas y procesos el 10-11-2026 a las 00:18:52, estado `ok`, 0 filas podadas y 0 ejecuciones marcadas timeout. Esto acredita una corrida sin error en la base local reportada, pero no prueba por sí sola que todas las fuentes tengan sus plazos configurados o que hubiera datos elegibles. La regla de Log Analytics y el análisis documentado de los registros de auditoría anteriores al 09-11-2026 no están acreditados. La aprobación del responsable de producción sigue pendiente.

Esto es un bloqueador relevante porque no alcanza solo con que el sistema registre eventos o los minimice; también requiere:

- confirmación de aplicabilidad de la política por el responsable designado,
- referencia verificable de la evidencia de retención técnica en base de datos y Log Analytics,
- clasificación de datos,
- cadena de custodia,
- proceso de eliminación segura,
- revisión de exportaciones y consultas sensibles.

### 2.6. Continuidad operativa: faltan pruebas reales de recuperación

La documentación actual reconoce una parte funcional del ciclo de respaldo, pero no certifica:

- recuperación ante pérdida total,
- validación real de restauración con `pg_dump`/`pg_restore`,
- RPO/RTO aprobados por negocio,
- pruebas de rollback y fallo de archivos,
- concurrencia y continuidad con cargas reales,
- intercambio de base y recuperación del entorno.

En otras palabras: existen mecanismos y evidencia local, pero no una demostración formales de continuidad productiva.

## 3. Estado por área

### 3.1. Backend

**Estado: 🟢 Verde**

**Evidencia**
- Arquitectura de servicios y routers bien pensada.
- Configuración de entorno con validación de producción.
- Contexto tenant + RLS y guardas de seguridad.
- Suite funcional con múltiples pruebas aprobadas.

**Riesgos**
- Validación de migración en un entorno real no concluida.
- Faltan pruebas de recuperación y de operación distribuidas.
- El diseño es sólido, pero aún no está certificado para producción.

### 3.2. Frontend

**Estado: 🟡 Amarillo**

**Evidencia**
- Compilación y bootstrap funcional.
- Rutas y vistas de administración implementadas.
- Integración de sesión/autenticación y UI operativa.

**Riesgos**
- Dependencias con vulnerabilidades reportadas.
- Rutas heredadas y actuales no están completamente unificadas.
- La capa visual está funcional, pero aún requiere hardening de seguridad y consistencia de arquitectura.

### 3.3. Infraestructura y Docker

**Estado: 🟢 Verde**

**Evidencia**
- `docker compose config --quiet` se valida correctamente.
- El entorno local se puede iniciar con comandos estándar.
- La composición de servicios está integrada y es útil para desarrollo.

**Riesgos**
- El entorno no está preparado para producción real.
- No hay evidencia de seguridad operacional del despliegue, ni de resiliencia y recuperación. 

### 3.4. Seguridad y control de acceso

**Estado: 🟡 Amarillo**

**Evidencia**
- Validación de producción en configuración.
- RLS aplicado a nivel de contexto y transacción.
- Rechazo de credenciales y comportamiento inseguro en producción.

**Riesgos**
- No hay validación real de roles de PostgreSQL con mínimo privilegio.
- No hay evidencia de acceso excepcional, auditoría y revocación en entorno objetivo.
- Falta evidencia de pruebas negativas para operaciones sensibles.

### 3.5. Privacidad, retención y cumplimiento

**Estado: 🔴 Rojo**

**Evidencia**
- Hay redacción y minimización implementadas parcialmente.
- La auditoría de autenticación y actividad está presente.

**Riesgos**
- DEC-08 está acordada como política interna; RNF-PRV-01 sigue parcialmente implementado.
- Falta evidencia de retención efectiva y del ciclo de vida de los registros.
- No hay evidencia de revisión de registros históricos ni de aprobación de aplicabilidad para el entorno de producción.

### 3.6. Recuperación, continuidad y DR

**Estado: 🔴 Rojo**

**Evidencia**
- Se cuenta con respaldo local y verificación técnica.
- Hay trazabilidad de backups y restauración lógica.

**Riesgos**
- No hay pruebas de restauración real ni demostración del objetivo de negocio.
- Faltan RPO/RTO aprobados.
- No hay pruebas de pérdida total del entorno.

## 4. Evaluación de riesgo general

### Riesgos P0

1. Seguridad de dependencias Frontend no cerrada.
2. Recuperación operativa y continuidad aún no demostrada.
3. Falta ejecutar/evidenciar el job de retención, verificar Log Analytics y documentar la revisión histórica; la aprobación de aplicabilidad de DEC-08 por producción sigue pendiente.
4. Validación real de roles PostgreSQL y permisos mínimos insuficiente.
5. Arquitectura de repositorio y rutas aún con drift y compatibilidad heredada.

### Riesgos P1

1. Documentación técnica con versiones y rutas inconsistentes.
2. Falta de pruebas de carga y recuperación representativas.
3. Convergencia entre back-office, portal, operaciones y administración aún no unificada.
4. Mecanismos de backup y restauración funcionales pero no certificados.

### Riesgos P2

1. Integraciones externas incompletas o parcialmente validadas.
2. Configuración local de desarrollo no transferible directamente a producción.
3. Necesidad de hardening operativo y guardas de alertas más exhaustivas.

## 5. Estado de cumplimiento y recomendación

### Estado general

El proyecto está en un estado de **maduración técnica buena para desarrollo y validación** y de **preparación insuficiente para producción**.

### Recomendación ejecutiva

Se recomienda mantener la decisión de **NO GO** para producción con datos reales, pero con una estrategia de cierre bien definida:

1. Cerrar vulnerabilidades de dependencias del frontend.
2. Alinear arquitectura y versiones de esquema.
3. Definir un estándar operativo único para rutas, API y migraciones.
4. Documentar y ejecutar prueba de recuperación real.
5. Confirmar requisitos de privacidad aplicables y obtener aprobación operativa antes de producción.
6. Validar roles PostgreSQL reales, secret management y permisos mínimos.

## 6. Plan de cierre recomendado

### Inmediato (1-2 semanas)

1. Actualizar `next` y paquetes vulnerables con revisión de build y auditoría.
2. Reforzar la consistencia de versiones de esquema y rutas públicas/legacy.
3. Revalidar backend y frontend en entorno limpio tras la actualización.
4. Ejecutar una restauración real aislada documentada.

### Corto plazo (2-4 semanas)

1. Validar roles PostgreSQL reales y permisos mínimos.
2. Implementar la política de retención acordada, revisar registros históricos y validar su aplicabilidad con el responsable.
3. Ejecutar pruebas de continuidad y DR con evidencia formal.
4. Revisar incorporaciones de seguridad y auditoría en endpoints sensibles.

### Antes de producción

1. Obtener confirmación de aplicabilidad y autorización operativa para uso con datos reales.
2. Validar entorno de producción con secretos reales y rotación.
3. Ejecutar pruebas de carga, seguridad y recuperación representativas.
4. Certificar RPO/RTO y restauración documentada.
5. Certificar que el estado de salud final queda en verde antes del go-live.

## 7. Conclusión

Acredittia ya no se encuentra en un estado de inconsciencia técnica ni de simple prototipo. Tiene una base funcional sólida y una documentación de gestión aceptable. DEC-08 ya fija una política interna simplificada, pero la combinación de:

- vulnerabilidades de dependencias,
- drift de esquema y rutas,
- ausencia de validación real de continuidad,
- controles de privacidad y retención aún no validados,
- y requisitos de cumplimiento/operación todavía no validados,

mantiene el proyecto en un estado claramente no apto para producción con datos reales.

La recomendación actual es mantenerlo en **NO GO**, con un plan de cierre técnico y operativo bien definido para pasar a un estado verificable y sostenible.
