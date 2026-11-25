# Gap Analysis — Acredittia

**Corte vigente:** 25-11-2026 (actualización funcional RF-AUD-02)  
**Estado:** funcionalmente avanzado; **NO-GO** para producción con datos reales.

Este análisis refleja la implementación y la evidencia documentada en el SRS
v1.16 y en [VALIDACION_ACTUAL.md](./VALIDACION_ACTUAL.md). Distingue entre
funcionalidad local, validación en el entorno destino y aceptación para
producción; una no sustituye a las otras.

## 1. Resumen ejecutivo

- Cobertura estimada actual de las 37 fichas SRS: **89,7% (3.318/37)**.
- Promedio estimado de las ocho prioridades ADMIN: **92,0%**.
- Promedios estimados P0/P1/P2: **95,0% / 87,7% / 89,2%**.
- Son promedios documentales de avance por requisito, no un porcentaje
  ponderado del producto, aceptación contractual ni preparación productiva.
- El proyecto sigue **NO-GO** hasta cerrar los bloqueos P0 de privacidad
  (DEC-08/RNF-PRV-01), seguridad y continuidad, y validar el despliegue real.

### Cierres respaldados dentro de su alcance

- `RF-DAS-01`: dashboard global funcional, con universos acordados y “N/A”
  cuando no hay documentos evaluables.
- `RF-BUS-01/02`: búsqueda, concesiones, alcance y exportación probados.
- `RNF-SEG-01`: roles, RLS, denegaciones y secretos confirmados en el entorno
  destino; no implica que todo `RF-SEG-01/02/03` esté cerrado.
- `RF-AUD-03`: exportación de negocio con autorización, motivo, auditoría y
  documentos asociados validada localmente (46 pruebas y pruebas sintéticas
  de 60 MiB/10.000 filas). No es certificación de producción.
- `RF-AUD-02`: historial de autenticación funcional al 100% en el alcance
  acordado; revisión de código confirma minimización, consulta ADMIN auditada,
  retención de 12 meses, revocación administrativa por acción y protección
  append-only con purga controlada. Pasaron 16 pruebas focalizadas, con un
  warning no bloqueante; producción sigue bloqueada por DEC-08/RNF-PRV-01.
- `RNF-REC-01`: creación, descarga, eliminación, importación, verificación y
  restauración local acreditadas; recuperación productiva sigue pendiente.
- Exportación general ADMIN: PDF y ZIP contienen solo resúmenes agregados; la
  exportación de negocio permanece separada.
- **Planes y servicios:** se cubrió la brecha de interfaz señalada por el
  usuario: la cuenta `company` puede consultar catálogo, plan/estado actual e
  iniciar trial o cambiar/reactivar plan; ADMIN ve el plan por empresa como
  dato informativo. No se conectó una pasarela, no se aplican los límites del
  catálogo y la página no incluye cancelación ni facturas. Es una adición fuera
  de las 37 fichas SRS, por lo que en el corte del 23-11-2026 no cambiaba el
  avance (**88,7%**) ni el promedio ADMIN (**90,6%**); P0/P1/P2 tampoco
  cambiaban. El build y la prueba focalizada de la columna ADMIN pasaron; la
  interacción completa de la página aún no tiene
  recorrido manual/end-to-end documentado.
- El PDF ADMIN ahora usa gráficos circulares para estados, líneas para series
  mensuales y barras horizontales para comparaciones. Las dos pruebas
  focalizadas de generación PDF pasaron con
  `tests/test_admin_backups.py -k "export_console_pdf_resumen or export_pdf_summary_needs_no_user_grant"`;
  el usuario confirmó que el flujo se ve más claro. Véase
  [console_exports.py](../BASE/app/backend/app/services/console_exports.py).

## 2. Matriz de prioridades ADMIN

Cada porcentaje de área es el promedio simple de las estimaciones de las fichas
SRS asociadas, sin ponderar por tamaño de grupo. En Seguridad y aislamiento se
incluyen RF-SEG-01/02/03 y RNF-SEG-01. Los recortes de alcance no se usan para
inflar el avance.

| Prioridad | Avance estimado | Funcionamiento actual | Brecha mínima restante |
|---|---:|---|---|
| Dashboard global | 90,0% | `RF-DAS-01` al 100%; `RF-DAS-02` al 80%; KPI y universos acordados. | Completar/aceptar las series de actividad y crecimiento incluidas en el alcance de `RF-DAS-02`. |
| Gestión global de empresas | 100,0% | `RF-EMP-01/02` con 100% en las fichas; el 100% de `RF-EMP-02` cubre el flujo normal de registro/aprobación. | Validar rechazo y transiciones/casos límite; el valor de las fichas no significa que esos casos estén cerrados. |
| Buscador global | 100,0% | `RF-BUS-01/02` validados en las rutas y operaciones probadas. | Ninguna para estos requisitos. El listado ADMIN de usuarios se mantiene en `RF-USU`. |
| Métricas SaaS | 86,7% | Promedio de `RF-MET-01` 75%, `RF-MET-02` 100% y `RF-MET-03` 85%. | Cerrar definiciones/series pendientes de `RF-MET-01/03`; distinguir documentos únicos de revisiones IA. |
| Alertas y salud | 83,3% | Promedio de `RF-SAL-01` 75%, `RF-SAL-02` 80% y `RF-SAL-03` 95%; el usuario reporta verificación manual de reintentos y alertas. | Los escenarios y umbrales de esa verificación no están detallados; siguen pendientes totales/paginación y trazabilidad operativa. Se mantienen los porcentajes de RF-SAL-02/03 hasta reconciliar esos criterios. |
| Usuarios, roles y permisos | 77,5% | Promedio de `RF-USU-01` 75% y `RF-USU-02` 80%; gestión e invitaciones para cuentas nuevas dentro de una empresa. | Validar integralmente permisos y lecturas sensibles. La transferencia de una cuenta existente entre empresas queda fuera de la primera salida. |
| Auditoría y trazabilidad | 100,0% | `RF-AUD-01/02/03` al 100% en sus alcances funcionales acordados; RF-AUD-02 pasó 16 pruebas focalizadas el 25-11-2026. | La aprobación de producción, aplicación de DEC-08 a datos reales y tratamiento de históricos siguen pendientes en RNF-PRV-01. |
| Seguridad y aislamiento | 98,8% | Promedio de `RF-SEG-01` 100%, `RF-SEG-02` 95%, `RF-SEG-03` 100% en la demo pública temporal y `RNF-SEG-01` 100%. | Completar el inventario de lecturas sensibles de RF-SEG-02. El usuario confirmó el túnel operativo y el smoke test acreditó login/API protegida en el alcance de desarrollo; la preparación productiva sigue pendiente en el NO-GO general. |

El promedio ADMIN de 92,0% y el promedio SRS de 89,7% no son métricas de
preparación para producción. No hay un modelo de ponderación por esfuerzo,
criticidad o aceptación aprobado.

## 3. Bloqueos de salida y evidencia pendiente

### P0 — Antes de usar datos reales

1. **Privacidad (`DEC-08` / `RNF-PRV-01`, 80%).** DEC-08 está acordada y no
   aplica a desarrollo/pruebas con datos simulados. Producción tendrá clientes
   reales: falta aprobación del responsable de Producción sobre aplicabilidad
   contractual/legal, reconciliar el plazo de 90 días con la política vigente,
   demostrar retención por fuente (incluido Log Analytics) y documentar el
   inventario/tratamiento de históricos. No borrar históricos antes de aprobar
   su disposición.
2. **Autorización y mínimo privilegio (`RF-SEG-01/02`).** `RNF-SEG-01` está
   validado en el entorno destino; el Compose local de desarrollo conserva un
   rol elevado. El 20-11 pasó la matriz automatizada de tenants/RLS en la suite
   aislada, y el usuario reportó el recorrido manual end-to-end de empresas A/B,
   cambios, archivos, exportaciones, `contract_admin` y concesión ADMIN. Completar
   el inventario de otras lecturas sensibles y validar los controles del
   despliegue real. `RF-SEG-03` se limita a la demo pública temporal ngrok con
   datos sintéticos. El usuario confirmó que el túnel ya funciona y la evidencia
   manual registrada verificó `/login` y el rechazo anónimo de una ruta
   protegida. No usar datos reales; producción sigue en NO-GO.
3. **Auditoría y autenticación (`RF-AUD-01/02`).** El 20-11 el usuario confirmó
   manualmente auditoría de permisos/roles, estados y pausa/reanudación.
   RF-AUD-01 queda IV/100%. La revisión estática del 25-11 confirma RF-AUD-02
   al 100% funcional: retención de 12 meses, consulta ADMIN auditada,
   append-only con purga controlada y revocación administrativa auditada por
   acción. Las pruebas focalizadas pasaron 16/16, con un warning no bloqueante.
   La aprobación de producción, Log Analytics y tratamiento de históricos
   siguen en RNF-PRV-01.
4. **Entorno de aceptación.** El 20-11-2026 se realizó un smoke test de solo
   lectura con HTTPS temporal vía ngrok: TLS/redirect, carga de `/login` y
   rechazo de acceso no autenticado por el proxy API. Esto no equivale a un
   staging estable ni valida TLS en el origen. El usuario confirmó el mismo
   día que autenticación, invitación y recuperación funcionaron con los enlaces
   de ngrok. Esto acredita esos flujos en el entorno temporal reportado, no un
   remitente corporativo ni un dominio estable; la validación del correo
   corporativo y del entorno de go-live sigue pendiente.

### P1 — Para una operación recuperable y repetible

1. **Continuidad (`RNF-REC-01`).** RPO ≤24 h y RTO ≤30 min están acordados; la
   última restauración local en esquema 23 reportó RPO 13,659 s y RTO 7,815 s
   (`status=restored`), dentro de ambos objetivos. La programación diaria está
   implementada, pero debe habilitarse y monitorearse tras configurar respaldos.
   Siguen fuera del cierre funcional local el destino externo, el procedimiento
   externo de claves y la recuperación ante pérdida total; no se exige una
   prueba separada en staging.
2. **Regresión (`RNF-VAL-01`).** Tras corregir las rutas de migración, el
   19-11-2026 la suite backend completa pasó **526/526**, con un warning no
   bloqueante, en 1200.50 s. `tests/test_esquema.py` y
   `tests/test_admin_backups.py` también pasaron 41/41 tras agregar la migración
   23 al fixture y probar la actualización de respaldos v22 durante la
   restauración. La suite usa PostgreSQL temporal y el fixture sustituye
   `citext` y neutraliza `pg_trgm`. El 20-11-2026 se verificaron ambas
   extensiones reales y su comportamiento en PostgreSQL 16 de Compose; esto no
   valida el rol/RLS productivo. El 20-11-2026, otros **302 tests focalizados**
   de autenticación, tenants/RLS, roles, auditoría, operaciones, privacidad,
   respaldos y esquema pasaron en PostgreSQL 16 aislado; el fixture usa
   `acredittia_app NOBYPASSRLS`, pero parchea `citext` y `pg_trgm`. Falta
   conservar evidencia reproducible del entorno destino.
3. **Dependencias y reproducibilidad (`RNF-REP-01`).** Cerrado al 100% en el
   alcance de locks Python con hashes, `npm ci` y builds reproducibles; la
   regresión backend pasó 532/532 con el lock de pruebas. La auditoría npm se
   gestiona por separado de RNF-REP-01 y quedó resuelta el 19-11-2026: las
   auditorías completa y de producción reportaron cero vulnerabilidades tras
   actualizar las dependencias del frontend.
4. **Operación (`RNF-OPE-01`, `RF-SAL-02/03`).** El 20-11-2026 se detuvieron y
   restauraron API, worker, Redis y PostgreSQL, uno a la vez; antes de las
   interrupciones de worker, Redis y PostgreSQL se confirmó que la cola estaba
   vacía. Todos recuperaron servicio. Las pruebas automatizadas del mismo día
   cubren heartbeat vencido, reintento de un job encolado, alertas y alcance
   contract_admin. El usuario reportó que reintentos y alertas también quedaron
   verificados manualmente; no se documentaron los escenarios/umbrales, por lo
   que no se recalculan todavía RF-SAL-02/03. Durante la caída de PostgreSQL, `/health/esquema`
   devolvió 500; revisar si el contrato operativo requiere responder 503.

### Candidatos funcionales a diferir (requieren aprobación)

- Definiciones y series avanzadas de adopción/métricas SaaS aún incompletas.
- Casos excepcionales de rechazo y transiciones de empresas.
- Umbrales de salud y escenarios límite de paginación/totales.
- Validación visual/responsive y revisión de accesibilidad donde aplique.
- Integraciones de proveedores externos solo requieren validación productiva si
  el proveedor estará habilitado en la primera salida; un modo simulado no
  acredita disponibilidad externa.

## 4. Alcance mínimo acordado y recortes propuestos

Solo se consideran acordados los límites confirmados por el usuario. Las
propuestas de diferimiento de esta sección no cambian el SRS ni los porcentajes
hasta que Producto las apruebe.

- **Una empresa por cuenta** en la primera salida. Transferir una cuenta
  existente entre empresas queda fuera de alcance y requiere una decisión
  posterior para incorporarse.
- **Invitar cuentas nuevas** dentro de la misma empresa está implementado. El
  vínculo de una cuenta existente no se marca como aceptado ni como fuera de
  alcance hasta que Producto confirme esa decisión.
- **Exportación ADMIN general:** solo resúmenes globales agregados en PDF y
  ZIP; no filas identificables. La exportación de negocio autorizada por
  empresa/contrato/persona/equipo y documentos permanece separada.

Estos recortes reducen el alcance de la primera salida; no eliminan requisitos
P0 de privacidad, autorización ni recuperación. Para cambiar el SRS
o recalcular porcentajes se debe registrar la decisión y actualizar sus
criterios de aceptación, no solo el GAP.

### Recortes candidatos a aprobación de Producto

- Diferir las métricas avanzadas de adopción hasta acordar sus fórmulas, dejando
  en lanzamiento los KPI actuales con universos definidos.
- Validar solo los proveedores externos habilitados para el lanzamiento. Una
  integración simulada no acredita disponibilidad; los proveedores no
  habilitados deben quedar desactivados y excluidos formalmente del alcance.
- Mantener fuera de la primera salida la invitación para vincular cuentas
  existentes, solo si Producto confirma que basta con invitar cuentas nuevas.
- Priorizar rechazo y transiciones comunes de empresa; diferir escenarios
  excepcionales no requeridos por el flujo aprobado, sin omitir denegaciones ni
  controles de seguridad.

## 5. Criterio de GO/NO-GO

Mantener **NO-GO** para producción con datos reales hasta contar con evidencia
de:

- aprobación de Producción para privacidad/retención y tratamiento de históricos;
- matriz de autorización y denegación probada en roles del entorno destino;
- auditoría suficiente de operaciones y lecturas sensibles;
- habilitación y monitoreo del respaldo diario; destino externo y procedimiento
  de claves para preparación productiva (no requeridos para cerrar el alcance
  funcional local);
- validación reproducible con `citext`/`pg_trgm` reales y auditoría actual de
  dependencias;
- URL HTTPS, correo productivo y validación de los flujos desde el entorno de
  aceptación.

## 6. Fuentes de evidencia

- [SRS.md](./SRS.md), versión 1.11, 23-11-2026: requisitos, porcentajes y
  criterios vigentes.
- [VALIDACION_ACTUAL.md](./VALIDACION_ACTUAL.md): pruebas, límites de evidencia,
  DEC-08, restauración local y validación de flujos.
- [ESTADO_SALUD_GENERAL.md](./ESTADO_SALUD_GENERAL.md): resumen NO-GO y riesgos.
- [console_exports.py](../BASE/app/backend/app/services/console_exports.py):
  exportación ADMIN y gráficos PDF.
- [test_admin_backups.py](../BASE/app/backend/tests/test_admin_backups.py):
  regresiones de exportación PDF/ZIP y respaldos.

