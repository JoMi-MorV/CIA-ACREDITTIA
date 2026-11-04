# Estado de salud general de Acredittia

**Fecha de corte:** 4 de noviembre de 2026  
**Preparado para:** revisión técnica y de gestión  
**Alcance:** código, pruebas, documentación, composición Docker, frontend, backend y preparación productiva.

## Resumen ejecutivo

Acredittia presenta una salud técnica aceptable para desarrollo y validación
focalizada, con backend y frontend compuestos correctamente. La suite backend
completa está estable: 446 pruebas aprobadas en la ejecución final y ninguna
fallida o con error.

La preparación para producción sigue limitada por riesgos críticos de
dependencias frontend, controles operativos pendientes y requisitos legales o
contractuales aún abiertos. El proyecto debe conservar el estado **NO GO para
producción con datos reales** hasta cerrar los bloqueadores de este informe.

| Área | Estado | Evaluación |
|---|---|---|
| Backend | 🟢 Verde | Suite completa aprobada. |
| Frontend | 🟢 Verde | Compilación Next.js aprobada. |
| Docker Compose | 🟢 Verde | Configuración válida. |
| Dependencias frontend | 🔴 Rojo | 1 vulnerabilidad crítica y 2 altas reportadas por npm. |
| Respaldos y recuperación | 🟡 Amarillo | Ciclo local cifrado acreditado; faltan RPO/RTO aprobados y recuperación ante pérdida total. |
| Privacidad y auditoría | 🟡 Amarillo | Controles parciales; retención y aprobación DEC-08 pendientes. |
| Seguridad productiva | 🔴 Rojo | Roles reales, despliegue y controles operativos aún incompletos. |
| Producción con datos reales | 🔴 No GO | Bloqueada por riesgos P0 y decisiones pendientes. |

## 1. Cobertura y avance

La cobertura estimada de los 37 requisitos del SRS es **75,6%**, equivalente a
**76% redondeado**. El cálculo usa promedio simple y igual peso entre fichas:

```text
2798 / 37 = 75,6%
```

Esta cifra representa avance estimado de código/evidencia. No acredita pruebas
de aceptación, conformidad contractual ni preparación efectiva para producción.

## 2. Backend

### Evidencia

- Primera ejecución completa: 445 pruebas aprobadas y 1 falla en la semilla
  operacional demo.
- Caso aislado `test_demo_seed.py::test_seed_operacional_demo_es_amplio_y_repetible`:
  **1 aprobada, 0 fallidas**.
- Segunda ejecución completa: **446 aprobadas, 0 fallidas, 0 errores**.
- Duración: aproximadamente 15 minutos 50 segundos.
- Advertencia: deprecación en el cliente FastAPI/Starlette utilizado por pruebas.

### Evaluación

El backend no presenta fallos funcionales en la segunda ejecución completa.
La única falla observada fue transitoria y no se reprodujo en aislamiento ni
en la segunda corrida completa.

### Riesgos

- Persisten pruebas de integración real y escenarios de infraestructura distribuidos.
- La suite general no sustituye pruebas de restauración, alta disponibilidad,
  recuperación ante desastres ni carga sobre el entorno destino.

## 3. Frontend

### Evidencia

- Dependencias restauradas mediante `npm ci`: 116 paquetes instalados.
- `npm run build`: compilación Next.js completada correctamente.
- Docker Compose: validación correcta mediante
  `docker compose config --quiet`.

### Evaluación

La compilación frontend está funcional en el estado actual. Sin embargo, el
artefacto de ejecución no debe considerarse listo para producción porque
`npm audit --omit=dev` informa vulnerabilidades en componentes directos y
transitivos.

### Vulnerabilidades conocidas

- **1 crítica**
- **2 altas**
- **0 moderadas**
- **0 bajas**

Las dependencias afectadas incluyen:

1. `next`: dependencia directa.
2. `postcss`: dependencia transitiva.
3. `source-map-js`: dependencia transitiva.

La vulnerabilidad crítica requiere revisión y actualización antes de aceptar
una imagen o despliegue público. Esta declaración describe el resultado de
npm audit; la afectación explotable en los flujos específicos de la aplicación
debe verificarse al aplicar la corrección.

## 4. Seguridad y autenticación

La aplicación incorpora guardas relevantes:

- Producción rechaza JWT de desarrollo y secretos inferiores al mínimo requerido.
- Producción rechaza semillas demo.
- Producción rechaza la exposición de tokens de recuperación.
- Las semillas requieren activación explícita fuera de producción.
- Existe un procedimiento separado para aprovisionar el primer administrador.
- La recuperación no revela si una cuenta existe.
- La configuración de producción separa migración, API y supervisión.

### Pendiente

- Aprovisionamiento real de cuentas y catálogos de producción.
- Validación de roles reales PostgreSQL.
- Validación completa de acceso y aislamiento por usuario/rol/empresa.
- Gestión de secretos externos y rotación.
- Validación de entrega SMTP en producción.
- Retirada comprobada de cuentas y credenciales demo existentes.

## 5. Respaldos, restauración y continuidad

### Implementado

- Copia cifrada de PostgreSQL y almacenamiento local.
- Retención configurada de ocho respaldos.
- Verificación autenticada del paquete.
- Respaldo previo automático antes de restaurar.
- Separación entre credencial de lectura y credencial de mantenimiento.
- Trazabilidad de inicio, éxito y fallo.
- Medición técnica de RPO y RTO incorporada en la operación.

### Pendiente

- Restauración real con `pg_dump` y `pg_restore`.
- Prueba extrema a extremo con base PostgreSQL aislada.
- Validación de fallo de archivos y rollback.
- Ejecución real de intercambio de base.
- Objetivos RPO/RTO acordados por negocio.
- Custodia externa de clave y copia del respaldo.
- Compatibilidad con almacenamiento Azure Blob.
- Confirmación de permisos de mantenimiento.

## 6. Privacidad y auditoría

### Implementado

- Redacción centralizada de email, RUT, credenciales y secretos en auditoría.
- Minimización aplicada a descripciones y metadatos persistidos.
- Auditoría de autenticación, rotación, revocación y operaciones de respaldo.
- Pruebas focalizadas de privacidad y auditoría.

### Pendiente

- Aprobación legal/contractual de DEC-08.
- Definición y ejecución de retenciones diferenciadas.
- Auditoría completa de consultas y exportaciones.
- Tratamiento documentado de registros históricos.
- Clasificación integral de campos y destinatarios.
- Eliminación/poda comprobada de auditoría, logs y telemetría.

## 7. Integraciones y comunicaciones

La gestión de credenciales admite configuración de secreto local para desarrollo
y Azure Key Vault para entornos preparados. SMTP puede entregar enlaces de
restablecimiento mediante configuración pública del frontend.

Faltan conectores externos reales, WhatsApp, sincronización distribuida,
idempotencia, reintentos comprobados y operación de proveedores externos.

## 8. Estado por prioridad

| Prioridad | Estado | Observación |
|---|---|---|
| P0 | 🔴 Crítico | Controles de producción, privacidad, infraestructura y recuperación incompletos. |
| P1 | 🟡 Parcial | Auditoría, rendimiento y operabilidad tienen implementación pero requieren evidencia final. |
| P2 | 🟡 Parcial | Integraciones y canales externos están parcialmente implementados. |

Los porcentajes de requisitos bajos tienen impacto directo sobre el avance
global:

- RF-SEG-02: 55%.
- RF-AUD-01: 55%.
- RNF-PER-01: 55%.
- RNF-SEG-01: 55%.

Cada requisito cerrado desde 55% a 100% representa aproximadamente 1,22 puntos
porcentuales de avance global bajo el modelo actual.

## 9. Bloqueos para go-live

### Bloqueo crítico de seguridad

Actualizar Next.js y las dependencias afectadas y repetir:

1. `npm audit --omit=dev`.
2. `npm ci`.
3. `npm run build`.
4. Pruebas automatizadas del frontend disponibles.

### Bloqueo operativo

Completar:

- Restauración real.
- Recuperación y rollback de archivos.
- Objetivos RPO/RTO aprobados.
- Custodia y rotación de clave.
- Roles PostgreSQL reales.
- Validación de despliegue y recuperación.

### Bloqueo legal y contractual

Cerrar DEC-08 con evidencia de:

- Responsable designado.
- Revisión legal/contractual.
- Aprobación de retención.
- Tratamiento de datos históricos.
- Controles implementados y validados.

## 10. Plan recomendado

### Inmediato

1. Actualizar Next.js a una versión no afectada y resolver PostCSS/source-map-js.
2. Ejecutar auditoría y build tras actualizar.
3. Completar RF-SEG-02, RNF-SEG-01 y RF-AUD-01.
4. Ejecutar restauración aislada con datos representativos.

### Corto plazo

1. Validar infraestructura PostgreSQL real y mínimo privilegio.
2. Aprobar RPO/RTO.
3. Implementar y probar retención DEC-08.
4. Completar auditoría de consultas/exportaciones.
5. Validar recuperaciones de archivos y base.

### Antes de producción

1. Validar cuentas reales sin credenciales demo.
2. Confirmar SMTP y recuperación de contraseña.
3. Ejecutar pruebas de carga y rendimiento representativas.
4. Ejecutar una restauración completa documentada.
5. Resolver vulnerabilidades conocidas y evidenciar las excepciones aceptadas.
6. Obtener aprobación GO/NO-GO formal.

## 11. Criterios de salud final

Acredittia puede pasar a **estado verde operativo** cuando se cumpla
simultáneamente:

- Backend: 0 fallos críticos y suite integral aprobada.
- Frontend: compilación aprobada y sin vulnerabilidades críticas/altas abiertas.
- Seguridad: configuración, secretos, roles y RLS validados en destino.
- Privacidad: DEC-08 aprobado y retención implementada.
- Recuperación: restauración real y RPO/RTO demostrados.
- Operación: responsables, monitoreo, alertas y runbooks validados.

## Conclusión

La salud técnica actual es **parcialmente favorable**: el backend está estable,
el frontend compila y Docker Compose valida. Los principales riesgos están
concentrados en dependencias vulnerables, recuperación productiva, privacidad
contractual y seguridad de infraestructura.

La recomendación actual es mantener **NO GO** para producción con datos reales
hasta cerrar los bloqueadores críticos descritos en este documento.
