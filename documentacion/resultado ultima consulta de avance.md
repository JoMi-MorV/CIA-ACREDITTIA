Resultado de consulta de avance ADMIN — corte original 13-10-2026; actualizado al 15-10-2026 13:23:03 -03:00

## Actualización al 15-10-2026 13:23:03 -03:00

El avance ADMIN estimado permanece en **67%**, correspondiente a la revisión
documental/código del 13-10 y calculado como promedio simple de ocho
prioridades. No se recalculó con estos cambios ni representa aceptación de
producto o preparación para producción.

Desde el corte original se incorporó al portal `/gestion-cuentas` para listar,
buscar, paginar y administrar cuentas asociadas. En «Ver como empresa», ADMIN
puede consultar/editar el perfil de la empresa (razón social y correo; RUT y
estado son de solo lectura) y usar el panel de responsables de contrato.
La gestión de empresa no permite convertir una cuenta `company` con acceso
general en `contract_admin`: el selector la excluye y el API rechaza el cambio
con `ADMIN_EMPRESA_NO_CONVERTIBLE`. Cuentas `contract_admin` existentes pueden
reasignarse entre contratos. La gestión global de usuarios de ADMIN es una vía
separada.

**Evidencia reciente:** `npm run build` pasó y generó 25 rutas; la regresión
`python -m pytest tests/test_auth.py tests/test_tenants.py -q` pasó **71/71**
en PostgreSQL temporal, con 1 warning residual de `starlette.testclient` y
`httpx`. Se reconstruyeron API y web con Docker Compose. El navegador confirmó
la visibilidad del panel de responsables y el perfil de empresa durante
impersonación antes del último filtro de elegibilidad; no se completó una
comprobación visual del filtro final.

**Pendiente:** no existe aún un flujo de invitación/aceptación de una cuenta ya
existente a una empresa. El endpoint actual crea usuarios nuevos y el token de
activación no se entrega por email. Siguen abiertos DEC-08 y los bloqueos P0 de
seguridad/producción.

## Resultado del corte original — 13-10-2026

Avance estimado de ADMIN: 67% — promedio simple de las ocho prioridades, con el mismo peso para cada una. Es una estimación de cobertura funcional, no una certificación ni una medición objetiva de calidad. No lo interpretaría como “67% listo para producción”: hay brechas P0 de permisos, aislamiento y auditoría que bloquean declarar el módulo listo para operar con datos reales sensibles.

#	Prioridad	Avance estimado	Evaluación
1	Dashboard global	75%	Presenta los contadores, la acreditación, estados documentales y actividad mensual. Falta cerrar y contrastar universos, denominadores y crecimiento de empresas/usuarios; la actividad por eventos no demuestra por sí sola adopción ni crecimiento.
2	Gestión global de empresas	90%	Tiene listado y ficha agregada con estado, contratos, trabajadores, uso, actividad, industria y estado de cuenta. La vista revisada minimiza datos sensibles. Quedan por validar rechazos, transiciones repetidas y casos límite; “uso” y última actividad tienen límites de interpretación.
3	Buscador global	55%	Busca empresa, contrato, trabajador, equipo y usuario, y presenta resultados por categoría. No cumple todavía el requisito de permisos diferenciados por tipo de información: el backend exige ADMIN, pero las etiquetas de permisos no constituyen controles independientes por categoría y detalle.
4	Métricas SaaS	60%	Hay indicadores de clientes y usuarios activos, sesiones, series mensuales y actividad; clientes con baja actividad están en Salud. El tiempo de uso sigue siendo estimado y “documentos procesados” corresponde a revisiones de IA, no necesariamente a documentos únicos. Faltan validar cálculos y definiciones.
5	Alertas y salud de clientes	70%	Hay indicadores de baja acreditación, pendientes/vencidos, morosidad, alertas, baja actividad y operación. Faltan validar umbrales y casos límite, recuperar resultados más allá de los límites de las listas y demostrar que las sondas detecten fallos reales de los servicios.
6	Usuarios, roles y permisos	70%	Se administran roles y alcances de empresa/contrato; el backend valida que el contrato corresponda a la empresa e invalida sesiones en cambios de permisos. Se registra último acceso, pero no un historial completo. Siguen pendientes el ciclo integral de altas/invitaciones, la navegación sobre 100 usuarios y la validación específica del flujo de cambio auditado.
7	Auditoría y trazabilidad	50%	Se auditan cambios seleccionados, incluidos cambios de permisos, y el acceso a archivos documentales exige motivo y registra actor y archivo. Falta cobertura uniforme para inicios de sesión, lecturas sensibles, operaciones CRUD y exportaciones; solicitar una descarga no acredita necesariamente la transferencia efectiva.
8	Seguridad y aislamiento	62%	Hay controles de autorización, políticas RLS y pruebas de aislamiento multiempresa. Pero el Compose de desarrollo usa PostgreSQL postgres, no el rol de aplicación de mínimo privilegio; el alcance por contrato depende principalmente de la API; y ADMIN aún tiene acceso global sin un flujo completo de acceso excepcional limitado y auditado.
Promedio: (75 + 90 + 55 + 60 + 70 + 70 + 50 + 62) / 8 = 66,5%, redondeado a 67%.

Qué impide considerarlo completo
Los puntos más importantes por cerrar son:

Permisos del buscador por categoría y detalle, aplicados y probados directamente en el servidor.
Mínimo privilegio para ADMIN y evidencia de aislamiento en configuración equivalente a producción. Las pruebas de tenants son relevantes, pero no sustituyen la validación del despliegue real.
Auditoría completa de autenticación, acceso sensible, exportaciones y resultados de las operaciones.
Validación de métricas y salud: definiciones, umbrales, universos, límites de listas y telemetría real de tiempo de uso.
En la consulta original del 13-10, el GAP conservaba una estimación global anterior de 75–80% que aún no había sido recalculada; por eso no se tomó como resultado de aquel corte. La revisión se apoyó en el resumen de requisitos ADMIN, el SRS, los routers de ADMIN y consola interna, los controles transversales de autorización y tenant y la configuración de Compose. El GAP se actualizó posteriormente con el corte estimado de 67%.

En aquella revisión del 13-10 no se ejecutaron pruebas ni recorrido de navegador: se contrastaron código y documentación, que registraban validaciones previas y sus límites. Por ello, el 67% refleja avance observado/documentado, no una aceptación de extremo a extremo.