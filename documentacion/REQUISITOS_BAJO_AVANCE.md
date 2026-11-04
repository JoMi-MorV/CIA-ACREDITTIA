# Requisitos con menor avance estimado

**Fecha de corte:** 04-11-2026  
**Fuente principal:** [SRS.md](SRS.md) versión 0.66  
**Documentos complementarios:** [GAP_ANALYSIS.md](GAP_ANALYSIS.md), [RESUMEN_REQUISITOS_ADMIN.md](RESUMEN_REQUISITOS_ADMIN.md) y [VALIDACION_ACTUAL.md](VALIDACION_ACTUAL.md).

**Cronograma asociado:** [CRONOGRAMA_CIERRE_PRODUCCION.md](CRONOGRAMA_CIERRE_PRODUCCION.md) — cierre inicial simplificado del 5 al 19 de noviembre de 2026.

Los porcentajes siguientes son estimaciones de cobertura de código/evidencia propuestas para el SRS. No representan pruebas aprobadas, aceptación contractual ni preparación para producción.

## Lista de menores avances

| Pos. | Requisito | Avance | Estado | Prioridad | Pendiente principal |
|---|---|---:|---|---|---|
| 1 | **RF-AUD-02 — Histórico de autenticación** | 70% | PAR | P1 | Login, fallo, cierre, rotación y revocación registrados y consultables; quedan retención e integridad. |
| 2 | **RF-SEG-02 — Mínimo privilegio y acceso excepcional ADMIN** | 55% | PAR | P0 | Concesiones temporales, motivo, alcance, auditoría y revocación; falta integración de operaciones sensibles y pruebas negativas. |
| 3 | **RNF-PER-01 — Rendimiento** | 55% | PAR | P1 | Ejecutar carga representativa y acreditar resultados. |
| 4 | **RF-BUS-02 — Restricciones por información** | 65% | PAR | P0 | Integrar la matriz en detalle y exportaciones. |
| 5 | **RF-CLI-09 — Integraciones, credenciales y notificaciones** | 65% | PAR | P2 | Conectores externos, WhatsApp, sincronización e idempotencia. |
| 6 | **RNF-PRV-01 — Privacidad** | 60% | PAR | P0 | Retención, aprobación de privacidad, tratamiento histórico y acceso auditado. |
| 8 | **RF-SEG-03 — Autenticación sin credenciales demo** | 65% | PAR | P0 | Despliegue seguro, roles reales y administración inicial sin semillas demo. |
| 9 | **RF-AUD-01 — Cambios administrativos** | 55% | PAR | P1 | Cobertura uniforme de operaciones administrativas y cambios. |
| 10 | **RNF-SEG-01 — Seguridad de infraestructura** | 55% | PAR | P0 | Roles reales, mínimo privilegio, secretos y despliegue equivalente a producción. |

## Interpretación

La lista incluye:

- cinco P0 de seguridad, privacidad, autenticación o recuperación;
- tres requisitos de auditoría, permisos o operación;
- rendimiento reproducible;
- integraciones reales y canales de comunicación.

No significa que los requisitos estén en estado `PEN` o que falte toda su implementación. En varios casos existe código parcial o pruebas focalizadas, pero los criterios de aceptación completos aún están pendientes.

## Orden recomendado

### 1. Preparación para producción: P0

1. **RF-SEG-02:** mínimo privilegio y acceso excepcional temporal.
2. **RF-SEG-03:** despliegue seguro sin credenciales demo.
3. **RNF-SEG-01:** configuración y roles reales de infraestructura.
4. **RNF-PRV-01:** privacidad, retención y minimización aprobadas.
5. **RNF-REC-01:** respaldo, restauración, RPO/RTO y recuperación probada.

Este bloque debe completarse antes de admitir producción con datos reales. Sigue vigente el bloqueo P0 relacionado con DEC-08.

### 2. Auditoría y trazabilidad

**RF-AUD-02** supera el primer corte de implementación, pero sigue abierto. Debe completarse junto con:

- autenticación exitosa y fallida;
- cierre de sesión;
- expiración de sesión;
- revocación de tokens;
- lecturas sensibles;
- descargas;
- exportaciones;
- cambios administrativos;
- acceso excepcional.

Los eventos deben ser consultables por actor, recurso, fecha UTC, resultado y motivo cuando corresponda.

### 3. Permisos del buscador

**RF-BUS-02** requiere implementar y demostrar permisos efectivos por:

- categoría de información;
- ficha o detalle;
- empresa;
- contrato;
- recurso solicitado;
- usuario autenticado;
- operación realizada.

La interfaz no puede ser la única barrera de autorización.

### 4. Rendimiento

**RNF-PER-01** dispone de telemetría p95 y un ejecutor de línea base concurrente. Requiere fijar volumen y concurrencia representativos, ejecutar pruebas reproducibles de:

- concurrencia;
- carga;
- latencia;
- consultas lentas;
- paginación;
- exportaciones;
- recuperación ante degradación.

No deben declararse SLA ni objetivos de producción sin mediciones identificables.

### 5. Integraciones reales

**RF-CLI-09** requiere inventariar y cerrar por separado:

- vault o Key Vault real;
- almacenamiento seguro de credenciales;
- rotación y eliminación de secretos;
- sincronización real con proveedores acordados;
- correo SMTP;
- WhatsApp;
- reintentos;
- estados de disponibilidad;
- pruebas de fallos y recuperación.

Los conectores simulados o de demostración deben mantenerse claramente separados de integraciones productivas.

## Evidencias esperadas para aumentar el avance

Cada requisito debe avanzar solamente cuando exista evidencia suficiente:

- criterio de aceptación definido;
- prueba automatizada;
- recorrido manual reproducible;
- configuración del entorno utilizada;
- fecha de ejecución;
- resultado aprobado o pendiente;
- limitaciones conocidas;
- actor o aprobador responsable;
- decisión de producto o legal, si corresponde.

## Criterio de cierre sugerido

Un requisito no debe pasar a `IV` por la sola existencia de una pantalla, endpoint o prueba aislada.

Debe demostrar en conjunto:

1. implementación;
2. autorización;
3. aislamiento;
4. auditoría;
5. manejo de errores;
6. pruebas de casos límite;
7. configuración reproducible;
8. aceptación del alcance correspondiente.
