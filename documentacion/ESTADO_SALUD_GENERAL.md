# Estado de salud general de Acredittia

**Fecha de corte:** 18 de noviembre de 2026
**Preparado para:** revisión técnica, operativa y de gestión  
**Alcance:** backend, frontend, SQL/migraciones, seguridad, privacidad, continuidad operativa, documentación y preparación para producción.

### Actualización de continuidad — 19 de noviembre de 2026

Se acordaron objetivos funcionales de RPO ≤24 horas y RTO ≤30 minutos, con
respaldo diario. La última restauración local en esquema 23 reportó RPO 13,659 s
y RTO 7,815 s, con estado `restored`, dentro de ambos objetivos.
`tests/test_esquema.py` y `tests/test_admin_backups.py` pasaron 41/41 tras la
migración 23 y la compatibilidad con respaldos v22. No se requiere una prueba
separada en staging para cerrar el alcance funcional local. La configuración,
activación y monitoreo del job,
el almacenamiento externo y la recuperación ante pérdida total siguen sin
acreditarse para producción. El cierre RNF-REP-01 actualiza las métricas globales
de avance; los demás datos del corte del 18 de noviembre no se recalcularon.

### Cierre RNF-REP-01 — 19 de noviembre de 2026

Se generaron locks Python de runtime y pruebas con versiones exactas y hashes,
compilados desde Linux para cubrir las dependencias de despliegue; Docker
verifica los hashes al instalar el lock runtime. La imagen frontend usa
`package-lock.json` y `npm ci`. `npm ci`, el build frontend y ambas imágenes
Docker pasaron. La suite backend instalada en un entorno virtual desde el lock
de pruebas pasó **532/532**, con un warning no bloqueante. RNF-REP-01 queda
IV/100% en el alcance de dependencias de aplicación; imágenes base por digest,
paquetes APT y auditoría de vulnerabilidades quedan separados.

### Actualización de avance — 19 de noviembre de 2026

Al subir RNF-REP-01 de 65% a 100%, el avance estimado de las 37 fichas queda en
3.243/37 = **87,6%**. El promedio de ocho prioridades ADMIN permanece en
**81,8%**; P0 es **90,0%**, P1 **86,3%** y P2 **89,2%**. Las cifras no equivalen
a aceptación integral ni preparación para producción, que sigue **NO-GO**.
RF-CLI-09 queda IV/100% en el alcance reducido aceptado; RNF-SEG-01 permanece
IV/100% para el entorno destino.

### Actualización de auditoría de dependencias npm — 19 de noviembre de 2026

La auditoría completa del árbol frontend reportó **4 paquetes vulnerables**:
1 crítico, 2 altos y 1 moderado. Es un conteo de paquetes afectados; `next`
agrupa múltiples avisos. Los hallazgos y su tratamiento recomendado son:

| Paquete observado | Severidad y procedencia | Indicación de resolución |
|---|---|---|
| `next@14.2.5` | Crítica; dependencia directa y de ejecución. Agrupa múltiples avisos; [uno documenta RCE bajo ciertas condiciones de servidor Windows](https://github.com/advisories/GHSA-p293-qw3h-jr36). El reporte ofrece `14.2.35` como actualización compatible sin salto major. | Actualizar el pin exacto en `package.json` a `14.2.35` o a una versión corregida compatible que indique una nueva auditoría; regenerar `package-lock.json`. Revisar los avisos agrupados y validar build y rutas afectadas antes de desplegar. |
| `postcss@8.4.38` y `postcss@8.4.31` | Alta; la primera es directa y la segunda aparece anidada bajo Next. El aviso incluye exposición de archivos al procesar source maps ([GHSA-fxqj-rqcc-2cmp](https://github.com/advisories/GHSA-fxqj-rqcc-2cmp)). | Actualizar la dependencia directa fijada en `package.json` y resolver también la copia anidada. Elegir la versión corregida que indique el aviso vigente de npm; no asumir que actualizar Next basta para corregir el pin directo. Verificar todas las instancias en el árbol final. |
| `source-map-js@1.2.1` | Alta; dependencia transitiva, con riesgo de denegación de servicio al procesar source maps ([GHSA-68fv-2mgg-jv7q](https://github.com/advisories/GHSA-68fv-2mgg-jv7q)). El rango reportado alcanza `1.2.1`. | Llevar la resolución a `1.2.2` o superior mediante la actualización compatible de su dependencia padre; usar `overrides` solo si se confirma compatibilidad. |
| `postcss-selector-parser@6.1.4` | Moderada; dependencia transitiva, con riesgo de consumo elevado de CPU por complejidad cuadrática ([GHSA-rj75-hqrm-r3gf](https://github.com/advisories/GHSA-rj75-hqrm-r3gf)). El rango reportado es anterior a `6.1.5`. | Llevar la resolución a `6.1.5` o superior mediante una actualización compatible de su dependencia padre; confirmar que no quede otra copia vulnerable. |

**Estado actual: resuelto el 19 de noviembre de 2026.** La tabla conserva la
línea base reportada antes de la remediación; las versiones finalmente
instaladas y las validaciones están registradas a continuación. El reporte por
sí solo no confirma explotabilidad en la configuración concreta.

### Resolución y validación de npm — 19 de noviembre de 2026

Se actualizaron las dependencias y `package-lock.json`:

- `next`: `14.2.5` → `15.5.29`. La auditoría completa tras probar la
  actualización compatible a `14.2.35` aún reportó el hallazgo crítico.
  Aunque `npm audit fix --force` proponía `16.4.6`, se eligió la rama 15
  compatible con React 18 y se verificó nuevamente el árbol.
- `postcss`: `8.4.38` y la copia anidada `8.4.31` → `8.5.23`. Se fijó esa
  versión directa y se añadió un `override` para que Next tampoco instale la
  copia vulnerable.
- `source-map-js`: `1.2.1` → `1.2.4`, mediante actualización compatible del
  árbol.
- `postcss-selector-parser`: `6.1.4` → `6.1.6`, mediante actualización
  compatible del árbol.

**Validaciones aprobadas:** `npm ci` instaló el lock limpio; `npm audit` y
`npm audit --omit=dev` reportaron **0 vulnerabilidades**; `npm ls` confirmó las
versiones resueltas; `npm run build` pasó con Next.js 15.5.29, incluyendo
compilación, tipos y generación de 30 rutas; `docker compose build web` pasó y
su instalación Docker también reportó **0 vulnerabilidades**. Next.js añadió
`target: ES2017` a `tsconfig.json` durante el build para admitir top-level
`await`. El frontend no define un script de pruebas unitarias; no se ejecutó
una suite aparte. Mantener la auditoría completa y de producción en cero en
futuras actualizaciones.

## Resumen ejecutivo

El proyecto presenta una base técnica sólida para desarrollo y validación focalizada, pero aún no alcanza un estado de madurez compatible con producción real. El backend muestra estabilidad funcional y la mayoría de las capas de aplicación tienen evidencia concreta; sin embargo, el conjunto presenta riesgos de integración, seguridad, requisitos de cumplimiento por confirmar y continuidad que siguen bloqueando el paso a producción con datos reales.

La evaluación actual se mantiene en **NO GO** para producción. La mejora más importante desde el último corte es que el código y la documentación han convergido hacia una visión más realista: el proyecto no se presenta como “listo para producción”, sino como una plataforma con avances relevantes y con bloqueadores específicos todavía abiertos.

### Suite backend completa — 19 de noviembre de 2026

Tras corregir las rutas de migración y actualizar las pruebas de respaldos, la
suite completa ejecutada con `python -m pytest -q` desde `BASE/app/backend`
pasó **526 pruebas, 0 fallidas y 1 warning** no bloqueante de Starlette/httpx,
en **1200.50 s**. Se utilizó PostgreSQL temporal; el fixture sustituye
`citext` y neutraliza `pg_trgm`. Esta evidencia no certifica producción ni
valida las extensiones reales.

### Actualización documental — 18 de noviembre de 2026

Se verificó una compilación de Next.js y se confirmó que la suite backend
completa registrada en el proyecto es la ejecución del 16-11-2026:
**492 aprobadas, 0 fallidas**. Las correcciones realizadas el 17-11 tienen
validación focalizada de **14/14** y no se reejecutó la suite completa posterior
a esas correcciones. También se confirmó que `BASE/app/.env` contiene secretos
locales administrados fuera de Git y sin evidencia de filtración pública;
se recomienda mantenerlos fuera de documentación y registros. El Compose local
sigue usando un rol de PostgreSQL elevado.

### Actualización de avance — 14 de noviembre de 2026

RF-DAS-01 pasa de 90% a 100% tras definir los universos de sus KPI, alinear los
conteos documentales con el universo de acreditación y representar la ausencia
de datos evaluables como “N/A”. La prueba focalizada pasó 2/2, el build
frontend compiló y validó tipos y el usuario confirmó la revisión visual. El
avance tras ese cambio era 2.928/37 = 79,1%. Posteriormente, RF-SEG-02 subió de
55% a 90% tras integrar el botón ADMIN de autoconcesión de lectura temporal.
Las suites focalizadas de documentos, búsqueda ADMIN, respaldos y privacidad
pasaron 88/88 y el build frontend pasó. El usuario confirmó el recorrido
completo de RF-SEG-02, su correcto funcionamiento y auditoría, lo que eleva
el requisito a 95%. Además, confirmó RNF-SEG-01 en el entorno destino: roles separados,
RLS efectivo con roles reales, denegaciones entre empresas/contratos, secretos
externos y cumplimiento de DEC-10. Queda IV/100%. RF-DAS-01 queda IV/100%;
RF-SEG-02 sigue PAR/95% y quedan pendientes otras lecturas sensibles. El
estado de producción sigue **NO-GO** por las brechas indicadas en la tabla.

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
| Backend | 🟢 Verde | Suite completa del 19-11: **526 aprobadas, 0 fallidas, 1 warning** en PostgreSQL temporal; `citext`/`pg_trgm` reales y validación productiva fuera de alcance. |
| Frontend | 🟡 Amarillo | Dependencias npm actualizadas; auditoría completa y de producción en 0 vulnerabilidades. Builds local y Docker aprobados; falta validación de comportamiento en el entorno destino. |
| Docker / composición | 🟢 Verde | Validación de configuración y ejecución en entorno local consistente. |
| Seguridad técnica | 🟡 Amarillo | RNF-SEG-01 queda IV/100% por confirmación en el entorno destino; continúan pendientes otros controles de RF-SEG-01/02/03 y preparación productiva. |
| Privacidad / RNF-PRV-01 | 🔴 Rojo / P0 | `ops_retencion` está activo y el usuario reporta ejecución local `ok` el 10-11-2026 00:18:52 (0 filas podadas); faltan Log Analytics, revisión histórica documentada y aprobación de producción. |
| Auditoría administrativa / RF-AUD-01 | 🟡 Parcial, 90% / P0 | 71 pruebas de `test_ops.py` y `test_contratos.py` pasaron; el usuario confirmó las mutaciones acordadas registradas. Pendiente único: comprobar valores anterior/nuevo para permisos/estados y pausa de procesos cuando corresponda. |
| Buscador global | 🟢 RF-BUS-01 y RF-BUS-02 cerrados (IV, 100%) | 83 pruebas focalizadas validan autorización por categoría, concesiones (titular, vigencia, revocación y alcance), ficha directa y exportación ZIP limitada; build frontend aprobado. El listado administrativo independiente de usuarios continúa bajo RF-USU. No se realizó recorrido manual de navegador. |
| Seguridad y aislamiento de datos | 🟡 Parcial; RNF-SEG-01 IV/100%, RF-SEG-02 al 95% | 76 pruebas focalizadas de roles, configuración, tenants y esquema pasaron. El usuario confirmó roles separados, RLS efectivo con roles reales, denegaciones y secretos externos en el entorno destino, además del recorrido de concesión temporal auditado. Falta revisar algunas lecturas sensibles y cerrar los requisitos RF-SEG-01/02/03; Compose de desarrollo conserva rol elevado. |
| Ajustes de negocio ADMIN | 🟢 Implementado | UF/vigencia/fuente, CAC, margen bruto y objetivo de churn son persistentes; solo ADMIN puede modificarlos, motivo obligatorio y auditoría con antes/después. Migración 17; suites focalizadas 86 aprobadas y build frontend correcto. La fuente UF es manual. |
| Recuperación y continuidad | 🟡 Parcial | RPO ≤24 h y RTO ≤30 min acordados; la última restauración local en esquema 23 cumplió (13,659 s / 7,815 s). Falta configurar/monitorear el job y acreditar continuidad productiva, almacenamiento externo y pérdida total. |
| Documentación y arquitectura | 🟡 Amarillo | Buena cobertura documental; SRS v0.92 refleja el recálculo actual, aunque persisten rutas heredadas, decisiones pendientes y verificaciones de consistencia por completar. |
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

- La auditoría inicial reportó cuatro paquetes vulnerables; el cierre actualizado a Next.js 15.5.29 y las dependencias transitivas corrigió todos: `npm audit` y `npm audit --omit=dev` ahora reportan cero.
- `npm ci`, el build local y la construcción de la imagen Docker pasaron con el lock actualizado.
- El salto mayor de Next.js 14 a 15 requiere conservar las validaciones de compatibilidad y auditoría en las siguientes entregas; no se realizó una prueba funcional de extremo a extremo en el entorno destino.

Esto cierra el hallazgo de dependencias npm revisado aquí, pero no sustituye los demás controles de seguridad ni la validación del frontend en el entorno objetivo.

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

1. Recuperación operativa y continuidad aún no demostrada.
2. Falta ejecutar/evidenciar el job de retención, verificar Log Analytics y documentar la revisión histórica; la aprobación de aplicabilidad de DEC-08 por producción sigue pendiente.
3. Validación real de roles PostgreSQL y permisos mínimos insuficiente.
4. Arquitectura de repositorio y rutas aún con drift y compatibilidad heredada.

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

1. Mantener las auditorías npm completa y de producción sin vulnerabilidades en cada actualización del frontend.
2. Alinear arquitectura y versiones de esquema.
3. Definir un estándar operativo único para rutas, API y migraciones.
4. Documentar y ejecutar prueba de recuperación real.
5. Confirmar requisitos de privacidad aplicables y obtener aprobación operativa antes de producción.
6. Validar roles PostgreSQL reales, secret management y permisos mínimos.

## 6. Plan de cierre recomendado

### Inmediato (1-2 semanas)

1. Mantener el lock frontend reproducible y comprobar con auditorías npm completa y de producción que las actualizaciones futuras no reintroduzcan vulnerabilidades.
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

- controles de seguridad y operación aún no validados,
- drift de esquema y rutas,
- ausencia de validación real de continuidad,
- controles de privacidad y retención aún no validados,
- y requisitos de cumplimiento/operación todavía no validados,

mantiene el proyecto en un estado claramente no apto para producción con datos reales.

La recomendación actual es mantenerlo en **NO GO**, con un plan de cierre técnico y operativo bien definido para pasar a un estado verificable y sostenible.
