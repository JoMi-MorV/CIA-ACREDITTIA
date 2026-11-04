# Cronograma simplificado de 2 semanas

**Fecha de corte:** 4 de noviembre de 2026  
**Horizonte:** 5 al 19 de noviembre de 2026  
**Objetivo:** cerrar los bloqueadores críticos e preparar una decisión GO/NO-GO.

Este plan representa la primera fase de cierre. No sustituye las validaciones
pendientes de recuperación real, privacidad o infraestructura que requieran más
tiempo. El estado final esperado al término es **condicional NO-GO** hasta
completar la evidencia real.

## Semana 1 — seguridad y evidencia técnica

### 5-6 de noviembre

| Actividad | Responsable | Resultado esperado |
|---|---|---|
| Inventariar vulnerabilidades de Next.js/PostCSS/source-map-js | Frontend + Seguridad | Lista exacta de versiones y compatibilidad |
| Confirmar responsables y disponibilidad de PostgreSQL real | DevOps + DBA | Ambiente y dueño asignados |

### 9-13 de noviembre

| Actividad | Responsable | Resultado esperado |
|---|---|---|
| Actualizar dependencias frontend vulnerables | Frontend | Manifest/lock actualizado |
| Ejecutar `npm ci` y `npm run build` | Frontend + QA | Build aprobado |
| Repetir `npm audit --omit=dev` | Seguridad | 0 críticas/altas o excepción aprobada |
| Completar mínimo privilegio en endpoints críticos | Backend + Seguridad | RF-SEG-02 integrado |
| Ejecutar pruebas negativas de acceso | Backend + QA | Sin acceso fuera de concesión |
| Preparar roles PostgreSQL mínimos y validar RLS | DBA + Seguridad | Roles sin privilegios excesivos |
| Documentar pendientes de DEC-08 | Privacidad + Legal | Borrador listo para aprobación |

## Semana 2 — recuperación, validación y decisión

### 16-19 de noviembre

| Actividad | Responsable | Resultado esperado |
|---|---|---|
| Aprobar RPO/RTO objetivo | Negocio + Operaciones | Valores firmados |
| Ejecutar una restauración real aislada | DBA + Operaciones | Base restaurada e íntegra |
| Medir tiempo de restauración y rollback | DBA + QA | Tiempo y resultados registrados |
| Validar consulta/exportación auditada | Backend + Auditoría | Eventos registrados |
| Ejecutar suite backend completa y Compose | QA + DevOps | Resultados aprobados o errores registrados |
| Cerrar revisión de riesgos P0 | Seguridad + Dirección | Lista de riesgos y decisiones |
| Revisar cumplimiento de bloqueo legal DEC-08 | Legal + Privacidad | Aprobado o bloqueador formal |
| Reunión GO/NO-GO | Dirección + responsables | Decisión documentada |

## Criterio para avanzar

Solo puede considerarse GO si se cumplen los siguientes puntos:

1. Sin vulnerabilidades críticas o altas sin excepción formal.
2. Roles PostgreSQL y mínimo privilegio validados.
3. Auditoría de autenticación y operaciones sensibles disponible.
4. Privacidad/retención aprobadas por los responsables correspondientes.
5. Restauración real y rollback ejecutados exitosamente.
6. Suite backend y build frontend aprobados.
7. No existen credenciales demo ni secretos expuestos.

## Seguimiento diario

Durante las dos semanas, cada equipo debe informar diariamente:

- actividad completada;
- bloqueo actual;
- responsable siguiente;
- evidencia generada;
- fecha de cierre prevista.

## Estado esperado

Este cronograma puede mejorar la preparación técnica, pero un ciclo productivo
completo de respaldo y recuperación requerirá ejecución adicional. Mientras
falte restauración real, aprobación DEC-08 o infraestructura equivalente a
producción, la decisión debe permanecer **NO-GO**.
