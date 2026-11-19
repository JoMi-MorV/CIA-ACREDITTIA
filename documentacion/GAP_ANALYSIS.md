# Gap Analysis — Acredittia

**Corte vigente:** 18-11-2026  
**Estado:** funcionalmente avanzado; **NO-GO** para producción con datos reales.

Este análisis refleja la implementación y la evidencia documentada en el SRS
v1.03 y en [VALIDACION_ACTUAL.md](./VALIDACION_ACTUAL.md). Distingue entre
funcionalidad local, validación en el entorno destino y aceptación para
producción; una no sustituye a las otras.

## 1. Resumen ejecutivo

- Cobertura estimada de las 37 fichas SRS: **84,8% (3.138/37)**.
- Promedio estimado de las ocho prioridades ADMIN: **82,7%**.
- Promedios estimados P0/P1/P2: **86,1% / 84,7% / 83,3%**.
- Son promedios documentales de avance por requisito, no un porcentaje
  ponderado del producto, aceptación contractual ni preparación productiva.
- El proyecto sigue **NO-GO** hasta cerrar los bloqueos P0 de privacidad,
  seguridad, auditoría y validar continuidad, despliegue y regresión completa.

### Cierres respaldados dentro de su alcance

- `RF-DAS-01`: dashboard global funcional, con universos acordados y “N/A”
  cuando no hay documentos evaluables.
- `RF-BUS-01/02`: búsqueda, concesiones, alcance y exportación probados.
- `RNF-SEG-01`: roles, RLS, denegaciones y secretos confirmados en el entorno
  destino; no implica que todo `RF-SEG-01/02/03` esté cerrado.
- `RF-AUD-03`: exportación de negocio con autorización, motivo, auditoría y
  documentos asociados validada localmente (46 pruebas y pruebas sintéticas
  de 60 MiB/10.000 filas). No es certificación de producción.
- `RNF-REC-01`: creación, descarga, eliminación, importación, verificación y
  restauración local acreditadas; recuperación productiva sigue pendiente.
- Exportación general ADMIN: PDF y ZIP contienen solo resúmenes agregados; la
  exportación de negocio permanece separada.
- El PDF ADMIN ahora usa gráficos circulares para estados, líneas para series
  mensuales y barras horizontales para comparaciones. Las dos pruebas
  focalizadas de generación PDF pasaron con
  `tests/test_admin_backups.py -k "export_console_pdf_resumen or export_pdf_summary_needs_no_user_grant"`;
  el usuario confirmó que el flujo se ve más claro. Véase
  [console_exports.py](../BASE/app/backend/app/services/console_exports.py).

## 2. Matriz de prioridades ADMIN

Los porcentajes se conservan según el corte vigente del SRS; los recortes de
alcance no se usan para inflarlos.

| Prioridad | Avance estimado | Funcionamiento actual | Brecha mínima restante |
|---|---:|---|---|
| Dashboard global | 90% | `RF-DAS-01` al 100%; KPI y universos acordados. | `RF-DAS-02`: completar/aceptar las series de actividad y crecimiento incluidas en el alcance de producto. |
| Gestión global de empresas | 90% | Listado y ficha agregada; datos de empresa, usuarios y contratos disponibles. | Validar rechazo y transiciones/casos límite del flujo de empresa. |
| Buscador global | 100% | `RF-BUS-01/02` validados en las rutas y operaciones probadas. | Ninguna para este requisito. El listado ADMIN de usuarios se mantiene en `RF-USU`. |
| Métricas SaaS | 60% histórico | Telemetría de sesiones/uso implementada para `RF-MET-02`. | Cerrar definiciones y series de `RF-MET-01/03`; distinguir documentos únicos de revisiones IA. |
| Alertas y salud | 83,3% | Alertas, sondas, historial y progreso medible de procesos disponibles. | Validar umbrales, totales/paginación y fallos/recuperación distribuida. |
| Usuarios, roles y permisos | 70% histórico | Gestión de usuarios e invitaciones para cuentas nuevas dentro de una empresa. | Validar integralmente permisos y lecturas sensibles. La transferencia de una cuenta existente entre empresas queda fuera de la primera salida. |
| Auditoría y trazabilidad | 86,7% | `RF-AUD-03` al 100% funcional local; `RF-AUD-01` 90%; `RF-AUD-02` 70%. | Revisar anterior/nuevo en eventos pendientes; completar retención, integridad, acceso y revocación administrativa de auditoría. |
| Seguridad y aislamiento | 81,3% | `RNF-SEG-01` al 100% en el entorno destino; concesiones sensibles implementadas. | Completar matriz de operaciones empresa/contrato, inventario de lecturas sensibles y controles de despliegue (`RF-SEG-01/02/03`). |

El promedio ADMIN de 82,7% y el promedio SRS de 84,8% no son métricas de
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
2. **Autorización y mínimo privilegio (`RF-SEG-01/02/03`).** `RNF-SEG-01` está
   validado en el entorno destino; el Compose local de desarrollo conserva un
   rol elevado. Completar pruebas de la matriz empresa/contrato en listados,
   detalle, cambios, archivos y exportaciones; terminar el inventario de otras
   lecturas sensibles; y validar roles, secretos y semillas en el despliegue
   real.
3. **Auditoría (`RF-AUD-01/02`).** Comprobar que cambios de permisos/estados y
   pausas de procesos muestran anterior/nuevo cuando corresponde. Completar
   evidencia de retención, integridad, aislamiento de consultas y revocación
   administrativa de eventos de autenticación.
4. **Entorno de aceptación.** No hay URL HTTPS de staging, remitente corporativo
   ni buzón de prueba disponibles. Validar externamente acceso, invitación y
   recuperación de contraseña antes del go-live.

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
   `citext` y neutraliza `pg_trgm`; queda validar esas extensiones reales y
   conservar evidencia reproducible del entorno.
3. **Dependencias y reproducibilidad (`RNF-REP-01`).** Confirmar con auditoría
   actual si siguen vigentes las vulnerabilidades reportadas anteriormente;
   actualizar lo que corresponda, fijar dependencias/lockfiles para builds
   reproducibles y repetir build/regresión. El hallazgo histórico de npm no se
   presenta como vulnerabilidad confirmada en el corte actual.
4. **Operación (`RNF-OPE-01`, `RF-SAL-02/03`).** Probar caída y recuperación de
   API, worker y base de datos; verificar reintentos, heartbeat vencido,
   recuperación distribuida y alertas con umbrales acordados.

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
P0 de privacidad, autorización, auditoría ni recuperación. Para cambiar el SRS
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

- [SRS.md](./SRS.md), versión 1.03, 18-11-2026: requisitos, porcentajes y
  criterios vigentes.
- [VALIDACION_ACTUAL.md](./VALIDACION_ACTUAL.md): pruebas, límites de evidencia,
  DEC-08, restauración local y validación de flujos.
- [ESTADO_SALUD_GENERAL.md](./ESTADO_SALUD_GENERAL.md): resumen NO-GO y riesgos.
- [console_exports.py](../BASE/app/backend/app/services/console_exports.py):
  exportación ADMIN y gráficos PDF.
- [test_admin_backups.py](../BASE/app/backend/tests/test_admin_backups.py):
  regresiones de exportación PDF/ZIP y respaldos.

