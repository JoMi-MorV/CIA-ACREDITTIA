# Validación funcional — actualizado al 15 de octubre de 2026, 13:55:03 -03:00

## Gestión de cuentas e impersonación ADMIN — 15 de octubre de 2026, 13:55:03 -03:00

Se añadió `/gestion-cuentas` al portal, con listado paginado de cuentas de la
empresa, búsqueda, cambio de alcance permitido y activación/desactivación. La
invitación y aceptación de cuentas existentes no está implementada; el endpoint
actual de invitación crea usuarios nuevos y todavía no entrega por email el
token de activación.

Durante «Ver como empresa», ADMIN vuelve a ver el panel de responsables de
contrato y la entrada de perfil abre el perfil de la empresa, no el perfil
personal de ADMIN. El perfil permite editar razón social y correo; RUT y estado
son de solo lectura. Se restaura la conversión de cualquier cuenta `company`,
incluida la inicial, a `contract_admin` cuando queda al menos otro usuario
`company` activo. Se conserva `ULTIMO_ADMINISTRADOR` para evitar dejar la
empresa sin administrador. El selector ofrece cuentas `company` y
`contract_admin`, con confirmación doble al reducir el alcance; los encargados
existentes siguen pudiendo reasignarse entre contratos.

**Validación:** `npm run build` pasó y generó 25 rutas. Comando de regresión:
`python -m pytest tests/test_auth.py tests/test_tenants.py -q`; resultado
**71/71** en PostgreSQL temporal, incluida la conversión de la cuenta inicial
cuando queda otro administrador y el bloqueo cuando sería el último.
API y web se reconstruyeron con Docker Compose. En navegador ADMIN impersonando
se verificaron la
visibilidad del panel de responsables y el perfil de empresa. No se completó
una comprobación visual posterior a la restauración del filtro de candidatos.
La validación no acredita el flujo de invitación de cuentas
existentes ni cambia los requisitos legales/de seguridad de DEC-08. Persiste
un warning externo de compatibilidad `starlette.testclient` + `httpx`.

## Validación ejecutada — 14 de octubre de 2026

Se ejecutó la suite completa del backend con PostgreSQL temporal en Docker y
se obtuvo resultado verificado:

- Comando: `cd "BASE/app/backend"; python -m pytest -q`
- Resultado: **399 pruebas aprobadas, 0 fallidas**
- Warning residual: **1** de compatibilidad del stack `starlette.testclient` + `httpx`

Esto confirma que la infraestructura de pruebas, la migración del esquema y la
API siguen funcionando en conjunto, sin regresiones funcionales en la suite
backend actual. La advertencia residual no bloquea la ejecución, pero sí debe
revisarse en la evolución del stack cuando se actualice FastAPI/Starlette.

## Reportes en el portal de empresa — 14 de octubre de 2026

Se agregó `/reportes` y su entrada al menú del portal de empresa, usando las
APIs existentes de reportes, exportaciones y programaciones. La interfaz
incluye generación con filtro de contrato/período, historial paginado con
actualización de estados, descarga de reportes listos y gestión de reportes
programados. Los seis tipos disponibles, incluida la matriz de cumplimiento,
ofrecen PDF y CSV en generación, exportación y programación. Los PDF incluyen
marca, metadatos de empresa/contrato/período, recuento de registros, tabla
multipágina con encabezados repetidos y pie con número de página. Para
compatibilidad con el enum de base de datos, CSV se guarda usando el valor
histórico `excel` y se distingue con un parámetro; la API lo devuelve como CSV.
La entrada no se muestra a `contract_admin`, y la API también deniega el acceso
a sus reportes consolidados.

**Validación ejecutada:** `npm run build` en `BASE/app/frontend`, correcto;
Next.js generó la ruta `/reportes` y completó el chequeo de tipos. La suite
backend del mismo corte quedó validada con PostgreSQL temporal. La generación
PDF se probó a nivel de implementación y ejecución real de la API con los
requisitos del entorno; la advertencia residual que queda es de stack y no de
lógica de negocio. La implementación de interfaz no cierra por sí sola las
brechas generales de autorización, auditoría o minimización de exportaciones,
pero sí ya está integrada y verificada junto con la API principal.

## Revisión de cumplimiento ADMIN — 13 de octubre de 2026

Se revisaron la documentación y el código de las ocho prioridades ADMIN. La
estimación de avance funcional resultante es **67%**, como promedio simple y
con igual peso por prioridad: Dashboard global 75%; Gestión global de empresas
90%; Buscador global 55%; Métricas SaaS 60%; Alertas y salud de clientes 70%;
Usuarios, roles y permisos 70%; Auditoría y trazabilidad 50%; Seguridad y
aislamiento 62%.

Esta cifra es una estimación de cobertura funcional, no un porcentaje de
pruebas aprobadas, cumplimiento validado ni preparación para producción. No se
ejecutaron pruebas automatizadas, build ni recorrido visual como parte de esta
revisión. No se asigna porcentaje de preparación productiva: continúan abiertos
los bloqueos P0 de DEC-08, permisos granulares por categoría/recurso,
auditoría integral y demostración de aislamiento/mínimo privilegio en un
entorno equivalente a producción. El fundamento y los criterios pendientes se
detallan en `RESUMEN_REQUISITOS_ADMIN.md` y `GAP_ANALYSIS.md`.

## Mejoras de consola ADMIN — 13 de octubre de 2026

Se registran los siguientes cambios implementados desde el corte anterior:

- Empresas (cuentas) muestra industria y estado de cuenta (al día, en riesgo,
  moroso o no aplica); el detalle permite consultar perfiles y responsables de
  contrato.
- Salud de clientes reúne indicadores de uso/adopción, usuarios por plan e
  industria y riesgos en secciones plegables con explicación contextual.
- El buscador despliega sus resultados mediante un botón por categoría; se
  conservan filtros seleccionables y fichas.
- Los gráficos/indicadores tienen ayudas explicativas sobre cálculo y
  significado.
- Los cambios ADMIN de rol, empresa o contrato presentan consecuencias y
  requieren motivo; la auditoría registra actor, motivo y valores
  anteriores/nuevos, e invalida las sesiones del usuario.
- Durante la impersonación, la navegación ofrece «Volver a consola interna».
  No se implementó una sección general de Ajustes para precios o métricas
  financieras.

**Validación disponible:** el build del frontend pasó durante el cambio de
permisos; después de reconstruir los contenedores API/web, `/health` y
`/ops/accesos` respondieron HTTP 200. Esas comprobaciones acreditan compilación
y disponibilidad de las rutas, no la aceptación de todos los recorridos o
datos. Se añadieron pruebas backend para los cambios de identidad/permisos,
pero no se pudieron ejecutar entonces porque `pytest` no estaba disponible en
el entorno; por tanto, la auditoría y la invalidación deben verificarse con
esas pruebas antes de dar el flujo por cerrado. La regresión 247/247 descrita
abajo corresponde a contratos/esquema/documentos y no cubre por sí sola estas
mejoras recientes.

## Incidente — error de renderizado en Alertas — 8 de octubre de 2026

La consola del navegador reportó React #31 con un objeto que contiene los
campos completos de `Alerta`. El síntoma coincide con una respuesta antigua de
`GET /alertas/resumen` que devolvía una alerta en `activas` en lugar de un
contador numérico. El endpoint actual calcula `activas` con `COUNT`; la
regresión `test_resumen_de_alertas` verifica que la respuesta conserve los seis
contadores esperados y pase con datos de prueba.

La pantalla valida ahora en tiempo de ejecución el formato del resumen y
muestra un error recuperable si el servidor devuelve una estructura
incompatible, evitando que React intente renderizar el objeto. `npm run build`
completó correctamente. Para que la protección llegue al entorno que presenta
el error, se debe reconstruir y reiniciar/desplegar el frontend correspondiente;
si el API desplegado aún entrega el formato antiguo, también se debe actualizar
el backend.

## Décima entrega — ciclo de contratos y diálogos de confirmación — 8 de octubre de 2026

Se implementó la separación entre estado operacional del contrato y ciclo
`activo`/`desactivado`/`finalizado`; desactivación, finalización y restauración
exigen motivo y dejan actor, fecha y transición en actividad. El borrado físico
de contratos desde la API ordinaria queda deshabilitado. Se incorporaron vistas
Activos e Histórico, preservación de relaciones, exclusión del histórico de
conteos operacionales y alertas, bloqueo de cambios sobre expedientes históricos
y recálculo de vencimientos al restaurar. Una revisión IA en cola se cancela si
el contrato ya fue archivado.

Las acciones de alto impacto usan doble confirmación y las capturas de motivo,
errores, cambios de responsables, rechazo de empresas, revocación/reactivación,
eliminación de eventos y acceso a documentos usan diálogos con contexto claro.
No quedan llamadas a `window.confirm`, `window.prompt` o `window.alert` en las
pantallas frontend revisadas.

`npm run build`: **salida 0**, compilación optimizada, chequeo de tipos y 23
rutas completados. `python -m compileall -q app`: **salida 0**. La regresión
backend focalizada de ocho archivos pasó **247/247 pruebas**, incluido
`test_esquema.py`, en PostgreSQL efímero. Se verificaron transiciones y motivos,
auditoría con actor, lectura histórica acotada, denegación de mutaciones de
requisitos/plantillas/Carpeta de Arranque en contratos archivados, `contract_admin`
sin permiso de transición, ADMIN con `X-Company-Id`, y exclusión/recreación de
alertas vencidas al archivar/restaurar. La prueba de ciclo y el resumen de alertas
se repitieron tras los últimos cambios: **2/2 aprobadas**; este resultado se
superpone a la regresión de 247 y no se suma.

Durante la regresión se corrigió también `GET /alertas/resumen`: el campo
`activas` devolvía una fila de alerta en vez de un contador.

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest tests/test_contratos.py tests/test_esquema.py tests/test_documentos.py tests/test_sujetos.py tests/test_tenants.py tests/test_operacion.py tests/test_reportes.py tests/test_ops.py -q -p no:cacheprovider --tb=short
```

La ejecución usó la imagen existente `app-api` con Python 3.12, sin red, con el
código montado en solo lectura y base temporal; no se migró ni reinició la base
habitual. Persisten advertencias de clave JWT corta en fixtures, cliente de
pruebas obsoleto y `distinct()` en requisitos/reportes. No se ejecutó la suite
backend completa. RF-CLI-02 y DEC-12 quedan **implementados con validación
focalizada; aceptación integral pendiente**. Restan recorrido visual, pruebas
API→Redis/Celery distribuido, más casos de procesos asíncronos y validar la
migración 11 en el procedimiento de despliegue antes de usar la versión nueva
de API/worker con datos habituales.

## DEC-01/02 — permisos ADMIN y alcance del buscador — 7 de octubre de 2026

**DEC-01 acordada:** ADMIN realiza operaciones ordinarias y consulta agregados.
El acceso a datos sensibles requiere permiso específico, motivo y alcance
limitado por recurso/tiempo; deben auditarse concesión, uso y revocación. Se
impide desactivar, revocar o degradar al último ADMIN activo.

**DEC-02 confirmada:** el buscador conserva cinco categorías (empresas,
contratos, personas, equipos y usuarios), excluye administradores de plataforma
y usuarios sin empresa —gestionados desde sus vistas específicas— y no presenta
documentos ni contenido documental en las fichas.

Estas son decisiones funcionales; no prueban que la autorización granular, las
exclusiones en todas las rutas ni las guardas del último ADMIN estén
implementadas y validadas. Esas comprobaciones siguen pendientes en servidor.

## DEC-03 — universos de adopción y métricas — 7 de octubre de 2026

Se acordó separar solicitudes de registro (embudo, incluyendo pendientes y
rechazadas), empresas aprobadas en el período (adopción) y clientes activos
(empresa aprobada con suscripción activa o trial). La aprobación no equivale a
ser cliente pagador/activo. Las cuentas habilitadas deben distinguirse de
usuarios con actividad. Cada indicador debe mostrar definición, período,
universo, denominador cuando aplique y zona horaria; MRR y crecimiento
comercial quedan en Métricas SaaS.

Se precisó que DAU/WAU cuenta usuarios únicos de empresas con actividad humana,
excluye ADMIN de plataforma y eventos automáticos, y usa `America/Santiago`
para los límites de día y semana. El tratamiento de empresas con pagos
atrasados y otros estados no estándar de suscripción queda pendiente de
validación con el cliente. Los acuerdos de definición no validan los cálculos
actuales; se requieren pruebas con datos conocidos.

## DEC-04 — umbrales de riesgo e inactividad — 7 de octubre de 2026

Se acordaron como umbrales iniciales, revisables: acreditación bajo 70% para
empresas aprobadas con documentos obligatorios evaluables; tres o más
documentos requeridos faltantes/vencidos dentro de un mismo contrato; y 30 días
sin actividad humana registrada para una empresa aprobada que tenga usuarios
habilitados. Se excluyen eventos automáticos del cómputo de inactividad. Sin
usuarios, sin documentos evaluables o con datos insuficientes son estados
explícitos, no indicadores de salud ni riesgos con valor cero.

Estos umbrales no se han validado contra todos los casos límite ni implementado
de forma integral. La inactividad por eventos no equivale a duración real de
uso, cuya telemetría sigue pendiente según DEC-05.

## DEC-05 — medición de tiempo activo — 7 de octubre de 2026

Se acordó emitir un heartbeat cada 60 segundos solo mientras la sesión esté
autenticada, la pestaña visible y haya interacción reciente. El tiempo debe
pausarse después de cinco minutos sin actividad. El intervalo reduce el costo
de señalización frente a intervalos más frecuentes sin tratar la señal como
medición continua exacta.

Se acordó guardar un registro por sesión lógica y agregados diarios por
empresa/usuario, sin almacenar cada heartbeat como evento individual. Los
registros de sesión y los agregados por usuario son identificables: retención
propuesta de 90 días; solo agregados no identificables por empresa podrían
conservarse hasta 12 meses, sujetos a revisión y aprobación de DEC-08.

Se decidió que la métrica principal sea minutos activos medidos divididos por
usuarios únicos con actividad medida en el período; no se añadirá duración
promedio por sesión. El período exacto y el tratamiento de sesiones simultáneas
siguen pendientes. La población de usuarios de empresas excluye ADMIN de
plataforma según DEC-03. La estimación actual no debe presentarse como
telemetría real.

## DEC-09 — contrato de error del motivo documental (cerrada) — 7 de octubre de 2026

Se decidió conservar el comportamiento actual por compatibilidad; no se cambia
la API ni se unifican las respuestas. El parámetro ausente o la longitud
original fuera de 12–240 caracteres se rechaza con HTTP 422. Si la longitud
inicial está dentro del rango, pero después de quitar espacios el motivo queda
bajo 12 caracteres, se rechaza con HTTP 400 y código `MOTIVO_REQUERIDO`.

La evidencia de la primera entrega documenta ambas ramas: motivo ausente/corto
rechazado por validación inicial y un motivo de doce espacios rechazado tras
normalizar. También se valida que la descarga cruzada con motivo válido llega
al control de pertenencia y responde 404. Se cierra la decisión de producto
para el contrato vigente; cualquier cambio futuro requiere decisión nueva y
pruebas de compatibilidad.

## DEC-10 — aislamiento contractual y RLS — 7 de octubre de 2026

Se acordó que la autorización del acceso por contrato en la API y las
credenciales de base de datos de mínimo privilegio son obligatorias. RLS
contractual podrá añadirse como defensa en profundidad si el contrato activo
puede establecerse en la base de forma confiable y se prueba correctamente con
API, workers, ADMIN, reportes agregados y conexiones reutilizadas. Si esa
propagación no puede hacerse de forma segura, no se debe activar RLS contractual
de manera parcial o con un contexto que el cliente pueda falsificar; los
controles de API siguen siendo obligatorios.

Esta es una decisión de diseño, no evidencia de implementación. El código y la
configuración deben probar autorización negativa entre contratos y empresa,
credenciales sin superusuario/BYPASSRLS, y el aislamiento de cualquier contexto
si se adopta RLS. El estado de RF-SEG-01/RNF-SEG-01 continúa pendiente de
validación integral.

## DEC-03 — clasificación comercial de clientes — 8 de octubre de 2026

Se acordó contar como cliente activo solo a una empresa aprobada con suscripción
activa o trial. `past_due` se muestra por separado como pago atrasado; estados
como pausada, incompleta, impaga, cancelada o desconocida se muestran como
«otro estado/no activo». Ninguno de esos estados cuenta como cliente activo.
La decisión funcional no valida los cálculos ni las fuentes comerciales.

## DEC-05 — período y sesiones concurrentes — 8 de octubre de 2026

El promedio de minutos activos por usuario único permite seleccionar día,
últimos 7 días, últimos 30 días o mes calendario, usando límites de días
calendario en `America/Santiago`: hoy; hoy y los 6 días previos; hoy y los 29
días previos; o el mes calendario local. Si una persona tiene sesiones
concurrentes, se suman sus minutos aunque superen el tiempo de reloj: una hora
activa simultánea en dos sesiones computa dos horas de actividad de sesión para
esa persona. El denominador continúa siendo usuarios únicos con actividad.
Implementación y validación siguen pendientes; las reglas no certifican que la
telemetría actual mida ya ese comportamiento.

## DEC-11 — exportación de datos de negocio y archivos — 8 de octubre de 2026

Se precisó que la exportación ADMIN puede abarcar datos estructurados de una
empresa, contrato, persona o equipo e incluir los archivos documentales
asociados. Se acordó el formato ZIP con CSV y documentos organizados por
carpetas; las relaciones se incluyen por defecto y se pueden desmarcar
categorías. Toda exportación requiere motivo, debe entregarse para descarga
inmediata y no conservarse una vez transferida; las generaciones incompletas o
fallidas deben limpiarse. No se incluyen contraseñas, tokens, secretos ni
credenciales. Cada entidad/archivo debe respetar autorización y alcance; la
solicitud, generación, resultado y transferencia deben distinguirse y
auditarse.

No se fijan límites funcionales de filas ni tamaño: se intentará incluir todo
el alcance autorizado. Se acordó un CSV por tipo de entidad bajo `/datos` y
documentos bajo `/archivos/<tipo>/<id>/`, con nombre original saneado y ruta
registrada en el CSV correspondiente para evitar duplicar el mismo archivo.
Si la generación falla, se cancela completa, se elimina el paquete incompleto y
se informa el error; no hay reintento automático, pero el actor puede iniciar
uno nuevo. Falta validar viabilidad técnica ante volúmenes grandes, además de
probar autorización y transferencia. Esta decisión funcional no demuestra
implementación ni validación, y la exportación no sustituye los respaldos de
RNF-REC-01.

## DEC-12 — ciclo de vida de contratos — 8 de octubre de 2026

Se acordó reemplazar la eliminación física como acción ordinaria por estados
diferenciados: **desactivado** para una pausa temporal y **finalizado** para el
cierre del contrato. Ambos se conservan en una sección histórica de solo
lectura y pueden restaurarse al estado operativo, sin perder contrato,
trabajadores, equipos, documentos, requisitos ni historial. Las transiciones
deben registrar actor, fecha y estado anterior/nuevo.

Las fechas de vencimiento continúan avanzando mientras el contrato está en
histórico. Al restaurarlo, se recalcula el estado vigente y se generan solo las
alertas/notificaciones aún aplicables, sin reproducir individualmente avisos
atrasados. `company` puede gestionar sus contratos y ADMIN hacerlo
globalmente; `contract_admin` solo consulta el histórico dentro de su alcance.
Desactivación, finalización y restauración exigen motivo y deben auditar actor,
fecha, motivo y estado anterior/nuevo. Implementación y validación siguen
pendientes.

## DEC-13 — solicitud de vinculación de cuenta a otra empresa — 8 de octubre de 2026

**Propuesta pendiente de aprobación del cliente:** permitir que una cuenta
`company` o `contract_admin` solicite vinculación a otra empresa con una
justificación. La solicitud queda bloqueada hasta autorización explícita de
ADMIN; no cambia `company_id`, membresía ni permisos mientras espera. Deben
auditarse la solicitud, la justificación y la decisión.

**Alternativa recomendada, aún no aprobada por el cliente:** transferencia de
la cuenta, sin membresía simultánea. La persona titular debe aceptar primero;
después ADMIN revisa y decide. Ambas etapas deben completarse dentro de los 14
días desde el envío. Solo tras ambas aprobaciones se cambiaría la empresa; se
retiraría el acceso a la empresa de origen y no se heredarían permisos de
contratos en destino, que deberían asignarse expresamente. Hasta entonces no
cambia empresa ni permisos; un rechazo o expiración no transfiere la cuenta.
El esquema actual tiene un único `company_id` y `contrato_id` por usuario. La
propuesta no autoriza por sí misma el cambio ni acceso multiempresa. No se ha
implementado ni validado el flujo.

> **BLOQUEO P0 — GO/NO-GO DE PRODUCCIÓN:** no exponer datos reales hasta que DEC-08 tenga revisión legal/contractual documentada, decisiones definitivas de retención, responsables y aprobaciones identificados, y evidencia de que los controles de privacidad y auditoría están implementados y validados. La propuesta de retención no equivale a aprobación. **Estado actual: pendiente; no hay evidencia de cierre registrada aquí.**

## Evidencia requerida para levantar el bloqueo DEC-08

Registrar en esta validación (o enlazar un acta/control documental aprobado):

- responsable y fecha de la revisión legal/contractual, alcance revisado y conclusión;
- plazos definitivos de retención aprobados, responsables de custodia y proceso de eliminación/anonimización;
- aprobación de producto/operación y responsables de implementar, operar y revisar los controles;
- evidencia técnica de minimización, autorización y auditoría de consultas, manejo de registros históricos y validación de retención;
- decisión explícita de go/no-go para producción con datos reales, con fecha y aprobadores.

## Decisión de trazabilidad de incidentes (DEC-06) — 7 de octubre de 2026

Se acordó que los incidentes deben conservar contexto útil para investigar qué
ocurrió y dónde: componente/proceso, operación, momento, resultado/error e
identificador de correlación cuando estén disponibles. La incidencia se asocia
a una empresa solo con evidencia verificable; si no se conoce el alcance, se
presenta como global o indeterminado y no se infiere qué clientes fueron
afectados. La política de minimización, acceso y retención queda vinculada a
DEC-08. Esta es una decisión funcional, no una prueba de que el sistema actual
ya persista o correlacione todos esos campos; implementación y validación
operacional siguen pendientes.

## Propuesta de auditoría y privacidad (DEC-08) — 7 de octubre de 2026

Se acordó como propuesta registrar únicamente metadatos necesarios para
investigar: actor, acción, recurso, fecha, resultado e identificador de
correlación cuando exista. No deben almacenarse contraseñas, tokens, URLs
firmadas ni contenido de documentos. El motivo se exigirá solo para operaciones
sensibles según la matriz de permisos; la consulta quedará limitada a ADMIN y
roles autorizados, y esos accesos también se auditarán.

Retención inicial propuesta: registros de auditoría por 12 meses, logs técnicos
por 90 días y telemetría identificable por 90 días; métricas agregadas hasta
12 meses. Una URL emitida no demuestra que el archivo se haya transferido; si
se necesita acreditar una transferencia, se requerirá evidencia confiable del
almacenamiento. Los plazos quedan sujetos a revisión legal/contractual antes
de producción. Esta decisión no prueba que los controles estén implementados:
faltan su materialización, la matriz de acceso y el tratamiento documentado de
los registros históricos.

## Búsqueda global y catálogo de referencias — 7 de octubre de 2026

La barra admite varios términos parciales separados por espacios; todos deben
coincidir con campos de un mismo resultado o con el nombre de su empresa. Por
ejemplo, una búsqueda puede combinar marca, prefijo de patente, tipo de equipo
y empresa. El explorador plegable ofrece empresas, cargos, contratos, tipos y
marcas de equipo; sus valores se activan o desactivan y se muestran como chips
removibles en la barra, combinados con el texto libre. Se muestran hasta 100
valores por categoría dinámica. El usuario del proyecto confirmó que los
resultados revisados no muestran datos sensibles; el catálogo solo entrega
nombres/categorías de referencia, nunca RUT o correo.

`test_admin_busqueda.py`: **25 aprobadas, 0 fallidas**, incluyendo el catálogo y
la combinación de marca, patente, tipo y empresa en la misma búsqueda, además
de la forma no sensible de la respuesta del catálogo. El build frontend de
producción compiló y verificó tipos. No se hizo un recorrido visual manual de
la selección/deselección de chips; esa validación queda pendiente.

## Registro y aprobación de empresa — 7 de octubre de 2026

Según la verificación manual informada por el usuario del proyecto, el
formulario de registro crea la empresa y el usuario inicial en estado pendiente.
La cuenta espera la autorización de ADMIN; al aprobarla, la empresa y el usuario
quedan aprobados y el usuario conserva el rol `company`. Este flujo corresponde
a RF-EMP-02 del SRS v0.24.

El usuario también confirmó que la aprobación queda auditada como una
actualización, con la descripción exacta
`Cuenta approved por administrador , verificado por mi parte`.

La evidencia registrada cubre el camino normal de creación y aprobación,
incluida la categoría y descripción de ese evento. No documenta una prueba
manual del rechazo, motivo, aprobación/rechazo repetidos, ni una regresión
automatizada específica de estos casos; se mantienen como pendientes de
validación.

## Perfil bloqueado durante «Ver como empresa» — 5 de octubre de 2026

Cuando una sesión ADMIN mantiene el contexto de impersonación (`impersonar`),
la navegación oculta «Mi perfil». Si se abre `/perfil` directamente, la vista
no llama a `/auth/me`, informa que no está disponible y redirige a `/dashboard`
del contexto observado. Al salir de «Ver como empresa», el perfil propio vuelve
a estar accesible. Es una restricción de interfaz para evitar mezclar la
administración del perfil de ADMIN con el contexto de una empresa; no altera
los permisos del backend ni los flujos de gestión disponibles para cuentas
autenticadas de empresa.

La compilación de frontend verifica tipos y generación de la ruta. No se hizo
un recorrido manual de navegador de este caso.

## Nombre en registro y sección Mi perfil — 5 de octubre de 2026

El formulario de registro solicita ahora el nombre completo del usuario inicial,
separado de la razón social. El backend normaliza y persiste el dato en
`users.nombre`; no requiere migración. Se agregó la ruta autenticada `/perfil`
para actualizar nombre, correo y contraseña mediante `PATCH /auth/me`. El
cambio de contraseña requiere la clave actual y envía el refresh token vigente
para conservar la sesión elegida. La navegación incluye «Mi perfil».

`tests/test_auth.py`: **34 aprobadas, 0 fallidas**, incluyendo persistencia del
nombre, rechazo de nombre ausente/vacío y las pruebas existentes de edición de
perfil/cambio de contraseña. `docker compose build web` completó correctamente:
Next.js compiló y verificó tipos, generó 23 rutas incluyendo `/perfil`. Las
advertencias de dependencias y fixtures de pruebas permanecen en el entorno;
no se hizo recorrido manual del navegador.

## Último evento en el detalle global de empresa — 4 de octubre de 2026

La ficha expandible de empresa ahora muestra el evento más reciente con fecha,
tipo, módulo, tipo de entidad y nombre del actor; si no hay nombre, se usa un
identificador corto, y los eventos automáticos aparecen como Sistema. No se
devuelve email ni descripción libre. La prueba focalizada valida que se elige
el evento más reciente y que el actor corresponde; `tests/test_admin.py` pasó
20/20. `docker compose --progress quiet build web` pasó y el contenedor web se
recreó; Docker lo reportó `Up` y Next informó `Ready`. No se completó una
comprobación HTTP de `/admin/empresas` después de ese reinicio.

## Buscador global por categoría y RUT — 4 de octubre de 2026

`GET /admin/search` admite filtros de servidor por empresa, contrato,
trabajador/persona, equipo o usuario. Permite filtrar por empresa y estado;
personas por cargo y condición de conductor; equipos por tipo, patente, marca,
modelo y año; empresas por estado/demo; cuentas por rol y estado. La búsqueda
por RUT usa las columnas existentes de empresas y sujetos. Las cuentas de
acceso no tienen RUT propio; no se agregó una columna ni se requiere migración.
Se conserva el límite de resultados por categoría. Para bases que ya tienen el
marcador de esquema 10 y la columna nullable heredada `users.rut`, la API acepta
esa versión compatible sin consultar ni modificar la columna. Versiones futuras
o diferencias incompatibles continúan bloqueando el arranque.

En PostgreSQL temporal, `test_admin_busqueda.py` y `test_esquema.py`:
**34 aprobadas, 0 fallidas**. La regresión ampliada con `test_admin.py`,
`test_admin_identidad.py` y `test_admin_reactivacion.py` sumó **58 aprobadas,
0 fallidas**. Diagnósticos de los archivos
frontend modificados: sin errores. `npm run build` no se pudo ejecutar porque
Next.js no está instalado en las dependencias locales. `docker compose up --build`
completó con el build web en caché; el job informó esquema 10 sin cambios, la API
arrancó y `/health/esquema` respondió `{"status":"ok","schema_version":10}`.
El frontend respondió HTTP 200 en `http://localhost:3000`; no se recorrió el
navegador.

## Interfaz del buscador global — 4 de octubre de 2026

La revisión del código de `/admin/busqueda` confirma que los filtros de cargo
y tipo de equipo se obtienen de catálogos; la búsqueda puede ejecutarse con el
campo de texto vacío cuando hay filtros específicos y, de lo contrario,
requiere al menos dos caracteres. La ficha agregada se despliega en una fila
de resultado concreta, debajo de esa fila, con resumen y último evento/actor.
Solo puede quedar abierta una ficha a la vez. Cambiar la búsqueda, seleccionar
otra fila o cerrar la ficha invalida la solicitud en curso para no mostrar una
respuesta tardía.

Esta anotación documenta el comportamiento implementado a partir de la revisión
del código; no se ejecutaron pruebas automatizadas ni una validación visual de
navegador específica para estos cambios. La validación de interfaz queda
pendiente.

## Regresión completa y datos demo multiempresa — 1 de octubre de 2026

Se corrigieron las 23 fallas encontradas al ejecutar la suite backend completa:
compatibilidad de rutas `/api/v1/admin/ops` y `/api/v1/admin`, inclusión de
empresas aprobadas sin usuarios en el resumen de baja actividad, auditoría
consultable para la creación de faenas globales, atribución de impacto de Ops
solo cuando exista evidencia y fixtures de tendencias robustos en límites de
mes/trimestre.

La semilla demo ahora genera datos operacionales para las 16 empresas y conserva
idempotencia; se verifican contratos, trabajadores, equipos, documentos, alertas,
eventos, nombres no repetidos y patentes únicas. Los datos son sintéticos y se
usan exclusivamente para demostración.

**Suite backend completa: 363 aprobadas, 0 fallidas, 33.291 advertencias,
551,56 s.** Ejecutada con la imagen del backend, `modelo_datos` montado en
`/modelo_datos` y PostgreSQL temporal iniciado por los fixtures; no modifica la
base de datos habitual. Limitaciones: no instala las extensiones reales
`citext`/`pg_trgm`; permanecen advertencias de `datetime.utcnow()`, JWT corto
del fixture, cliente de pruebas y consultas `DISTINCT`. No es validación de
despliegue productivo ni de recorrido distribuido Celery.

`npm run build` en `BASE/app/frontend`: salida 0; compilación, chequeo de tipos,
lint y generación de 22 rutas completados. No se realizó recorrido manual de
navegador en esta validación.

Al corte de esta validación (01-10-2026), Compose local estaba en modo
demostración y esquema 9. Esta ejecución de pruebas usó una base temporal
aislada y no aplicó migraciones ni modificaciones a la base habitual. El esquema
requerido por la API actual es v11; la anotación anterior no describe el estado
actual de cada entorno. Estados de requisitos relacionados permanecen PAR/ISV cuando sus
criterios integrales siguen pendientes; ver SRS v0.15.

## Registros anteriores

## Octava entrega: identidad en gestión de usuarios — 30 de septiembre de 2026

PT-05-05 / RF-USU-01: la respuesta administrativa de usuarios devuelve correo real
para identificar al destinatario de cambios de permisos. La pantalla muestra nombre
y correo, o «Sin nombre registrado» con correo; confirma revocación/reactivación
con esa identidad y anuncia filtro por nombre o correo. El buscador global conserva
su respuesta anterior.

Regresión aislada: **21 aprobadas, 0 fallidas, 48 advertencias, 18,17 s** en
`test_admin_identidad.py`, `test_admin_reactivacion.py` y `test_admin_busqueda.py`.
Se verifica identificación por correo de cuentas ADMIN y empresa, filtro por correo,
rechazo de listado a empresa/sin sesión y ausencia de hash de contraseña/versión
de sesión en la respuesta. PostgreSQL efímero en contenedor sin red; permanecen
las limitaciones de extensiones del fixture y advertencias del entorno de pruebas.

`npm.cmd run build`: salida 0, tipos y generación de 22 páginas correctos.
No se recorrió navegador ni se reconstruyeron/reiniciaron los servicios habituales.
Esta corrección no requiere una nueva migración. RF-USU-01 sigue PAR.

## Séptima entrega: reactivación de usuarios — 30 de septiembre de 2026

PT-05-04 / RF-USU-01 añade Reactivar a las cuentas revocadas en Usuarios, con
confirmación y bloqueo del botón durante la petición. Usa PATCH con activo=true;
conserva rol y alcance, sin alterar la aprobación de la cuenta.

Esquema 9: `10_version_sesion.sql` añade users.auth_version con valor inicial 0.
Login y refresh emiten esa versión en el JWT; autenticación rechaza versiones
anteriores. Revocar por POST o cambiar activo por PATCH administrativo incrementa
la versión y revoca refresh tokens, también al reactivar cuentas antiguas. JWT
anteriores sin av se interpretan como versión 0 hasta la primera invalidación.
Login, refresh y mutaciones ADMIN bloquean la fila del usuario durante la operación;
refresh vuelve a comprobar revocación tras adquirir el bloqueo.

Primera ejecución: **65 aprobadas, 0 fallidas, 135,51 s**. Regresión final sobre
el código definitivo: **101 aprobadas, 0 fallidas, 169 advertencias, 164,39 s**,
incluyendo reactivación, autenticación, ADMIN, esquema y aislamiento. Se verifican
tokens antiguos rechazados después de reactivar, nuevo login/refresh válidos,
denegación sin ADMIN y migración 8→9 repetible. Las pruebas existentes desde 7
se actualizan para llegar a 9. No se realizó una prueba concurrente específica.

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest tests/test_admin_reactivacion.py tests/test_auth.py tests/test_admin.py tests/test_esquema.py tests/test_tenants.py -q -p no:cacheprovider --tb=short
```

Frontend: `npm.cmd run build` completó con salida 0, tipos y generación de páginas.
No se recorrió navegador. Backend probado sin red ni volúmenes habituales con
PostgreSQL efímero; permanecen límites citext/pg_trgm y advertencias JWT/cliente de
pruebas/runtime. No es suite completa ni se suman ejecuciones.

**Aplicación pendiente al entorno habitual:** migrar a esquema 9 y reconstruir
servicios según README antes de usar esta versión. No se migró ni reinició la base
habitual. Quedan altas globales, paginación, auditoría integral, navegador y
uniformar invalidación en otros mecanismos de desactivación/cambio de credenciales.
RF-USU-01 sigue PAR, conservando su porcentaje previo.

## Sexta entrega: guarda de roles PostgreSQL — 30 de septiembre de 2026

PT-03-02: API y Celery instalan un control sobre conexiones nuevas en producción.
Consulta pg_roles/pg_class y rechaza superusuario, BYPASSRLS, CREATEDB, CREATEROLE
y propiedad de tablas public; considera membresías tanto de session_user como
current_user. Descarta conexiones previas al instalar la guarda. El error no
incluye credenciales y wait_for_db lo propaga sin reintentos de disponibilidad.
El comando de migración no instala el listener de ejecución.

**70 aprobadas / 0 fallidas, 88 advertencias, 34,71 s** en las suites de roles,
configuración segura, tenants y esquema. Los siete casos nuevos prueban rol de
aplicación aceptado, superusuario rechazado, BYPASSRLS/CREATEROLE/CREATEDB rechazados,
propietario rechazado y bloqueo mediante evento de conexión en producción.
Se alteran y restauran exclusivamente roles/tablas de la BD efímera. No se
ejecutó un worker Celery distribuido ni se acreditó el despliegue completo.

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest tests/test_db_runtime_role.py tests/test_config_seguridad.py tests/test_tenants.py tests/test_esquema.py -q -p no:cacheprovider --tb=short
```

Misma imagen y límites citext/pg_trgm del fixture, sin red ni volúmenes habituales.
Advertencias de JWT de pruebas, cliente de pruebas y directorio runtime. No sumar
resultados a entregas anteriores ni presentarlos como suite completa. No se
cambiaron credenciales ni roles del entorno habitual; Compose sigue usando
superusuario en desarrollo. Aprovisionamiento y separación de credenciales siguen
pendientes. La guarda no demuestra que todas las políticas RLS sean correctas ni
vigila cambios de privilegios posteriores sobre conexiones ya abiertas.

## Quinta entrega: configuración segura — 30 de septiembre de 2026

PT-03-01 / RF-SEG-03 incorpora `APP_ENV` (development/test/production), con
rechazo de valores desconocidos. Producción rechaza secretos JWT dev-* o menores
de 32 bytes tras quitar espacios exteriores, semillas demo, exposición del token
de recuperación, RLS desactivado y migración al arranque. Los errores de validación
no imprimen los valores recibidos. La longitud no acredita aleatoriedad: el operador
debe generar un secreto propio y seguro.

`SEED_DEMO_ENABLED` y `AUTH_DEV_RESET_TOKEN_ENABLED` son false por defecto.
El arranque omite semillas salvo activación explícita fuera de producción, y
`seeds.run` rechaza invocaciones no autorizadas. El handler de recuperación
comprueba opción y entorno; ya no depende del prefijo del JWT. Compose local
activa semillas expresamente y mantiene desactivada la exposición de tokens.
Los fixtures habilitan ambas opciones para sus flujos controlados.

Primera ejecución focalizada: **46 aprobadas / 0 fallidas, 25,13 s**.
Tras ampliar casos de espacios en secretos, privacidad de errores y arranque:
**85 aprobadas / 0 fallidas, 134 advertencias, 55,14 s** en configuración,
autenticación y aislamiento. La prueba de arranque usa dependencias simuladas;
las pruebas HTTP de recuperación usan PostgreSQL efímero y comprueban respuesta
idéntica para cuenta existente/inexistente sin `_dev_token`.

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest tests/test_config_seguridad.py tests/test_auth.py tests/test_tenants.py -q -p no:cacheprovider --tb=short
```

Sin red ni volúmenes habituales, misma imagen app-api y límites del fixture
citext/pg_trgm. Persisten advertencias JWT del fixture, cliente de pruebas y
directorio runtime. No se repitió la suite completa ni se desplegó/reinició el
entorno. No sumar ejecuciones. Quedan roles BD reales, secretos/cuentas existentes,
aprovisionamiento inicial y correo de recuperación; RF-SEG-03 sigue PAR.
El Compose y ngrok siguen como demo. El modo producción exige configuración
explícita; no se detecta automáticamente que una instalación sea pública.

## Cuarta entrega: límites visibles del buscador — 30 de septiembre de 2026

PT-05-03 / RF-BUS-01: la API consulta hasta `limite + 1` por categoría, devuelve
solo `limite` e informa `hay_mas` y `limite_por_categoria`. Ordena por nombre e
ID para obtener resultados estables. `total` sigue contando elementos devueltos
por compatibilidad; no es el total de todas las coincidencias.

La interfaz muestra «Resultados mostrados», la consulta enviada y el límite por
categoría; cuando existe recorte, pide refinar la búsqueda. Limpia los resultados
y el detalle al iniciar otra consulta y solo presenta «Sin resultados» tras una
respuesta vacía, no mientras se escribe por primera vez. Limita la entrada a 100
caracteres. No incorpora paginación ni nuevas capacidades de autorización.

**Backend: 35 aprobadas / 0 fallidas, 73 advertencias, 53,70 s**, suites
`test_admin_busqueda.py` y `test_admin.py`. Pruebas de recorte para empresas,
contratos, usuarios y trabajadores; límites 1/2/25, coincidencias exactamente
iguales al límite, orden y ausencia de resultados. Mismo comando y entorno
aislado de la tercera entrega, con los límites conocidos de citext/pg_trgm.
Persisten advertencias del fixture JWT, cliente de pruebas y directorio runtime.

**Frontend:** `npm.cmd run build` desde `BASE/app/frontend`, código de salida 0,
compilación, chequeo de tipos y generación de páginas completados con dependencias
locales existentes. No es una instalación limpia ni un recorrido en navegador.

No se repitió la suite completa, no se modificó la base habitual y no se aplicó
un despliegue. No sumar estos casos a ejecuciones anteriores. RF-BUS-01 sigue PAR
por validación visual; el alcance de DEC-02 se confirmó posteriormente el
07-10-2026. RF-BUS-02 conserva sus permisos granulares pendientes.

## Tercera entrega: entradas del buscador — 30 de septiembre de 2026

PT-05-02 / RF-BUS-01: la API normaliza espacios exteriores antes de comprobar
el mínimo de dos caracteres. Una consulta de solo espacios, tabulación/salto de
línea o una letra rodeada de espacios devuelve 422 / `BUSQUEDA_INVALIDA` antes
de consultar entidades. Se conserva el máximo de 100 caracteres del parámetro
original y el 422 de validación para ausencia, cadena vacía, corta o demasiado larga.

Diez nuevos casos verifican esas entradas y aceptación de 2/100 caracteres,
normalización y coincidencia de empresa. Antes del cambio: **10 aprobadas / 3
fallidas, 12,20 s** en la suite de buscador. Después: **32 aprobadas / 0 fallidas,
67 advertencias, 30,99 s** entre `test_admin_busqueda.py` y `test_admin.py`.

Mismo contenedor aislado `app-api`, sin red, BASE de solo lectura y PostgreSQL
efímero; no se usaron volúmenes habituales. Comando de la segunda entrega con
la selección `tests/test_admin_busqueda.py tests/test_admin.py`. Advertencias
de JWT corto del fixture, cliente de pruebas y directorio runtime. No se ejecutó
suite completa ni navegador; se conservan los límites de extensiones del fixture.
No sumar resultados a entregas anteriores. RF-BUS-01 sigue PAR: presentación de
límites, alcance de usuarios y permisos granulares permanecen pendientes.

## Segunda entrega: clasificación del buscador — 30 de septiembre de 2026

PT-05-01 / RF-BUS-01: `admin.py` filtra sujetos de tipo trabajador en SQL antes
del límite de resultados. Los equipos ya no aparecen en esa categoría; se
conservan las coincidencias por nombre/cargo y la empresa asociada.

La nueva suite `tests/test_admin_busqueda.py` crea un equipo coincidente y
trabajadores de dos empresas, verifica límites 1/25, búsqueda sin distinción de
mayúsculas, categoría, empresa y destino del detalle. También comprueba rechazo
401 sin sesión y 403 para una cuenta de empresa.

- Antes de corregir: **1 aprobada / 2 fallidas, 5,54 s**; ambos casos detectaron
  el equipo presentado como trabajador.
- Después: **86 aprobadas / 0 fallidas, 181 advertencias, 132,92 s** en
  `test_admin_busqueda.py`, `test_admin.py`, `test_sujetos.py` y `test_tenants.py`.

Ejecución con imagen `app-api`, montaje BASE de solo lectura, sin red, PostgreSQL
efímero del fixture y sin volúmenes habituales. Las advertencias corresponden a
clave JWT corta del fixture, cliente de pruebas obsoleto y directorio runtime.
Se mantienen los límites de citext/pg_trgm de la primera entrega.

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest tests/test_admin_busqueda.py tests/test_admin.py tests/test_sujetos.py tests/test_tenants.py -q -p no:cacheprovider --tb=short
```

No se repitió la suite completa ni el navegador, ni se reinició/migró el entorno
habitual. No sumar estos 86 casos a los 295 de la entrega anterior. RF-BUS-01
pasa de COR a PAR, conservando su estimación: quedan validación de entradas y
límites y permisos granulares (RF-BUS-02). El alcance de usuarios sin empresa
figuraba pendiente en esta validación del 30-09; DEC-02 lo confirma
posteriormente el 07-10-2026. AT-05 permanece parcial.

## Revisión documental de brechas — 30 de septiembre de 2026

SRS v0.7 precisa hallazgos de lectura de código: auditoría de creación de faenas mediante logger, eliminación de contrato registrada como actualización, emails en descripciones, lectura de metadatos sin motivo/evento en el handler, exclusión de empresas con cero usuarios habilitados y ausencia de RLS contractual independiente en los scripts revisados. No se demostró fuga de datos a actores no autorizados. La pantalla de salud declara impacto global, sin mapeo individual de empresas. La ubicación exclusiva de MRR/crecimiento comercial en Métricas SaaS es un criterio de producto incorporado, no una nueva prueba de interfaz.

Esta actualización no cambia código, no vuelve a ejecutar pruebas ni modifica el resultado registrado de 295 casos aprobados. Las nuevas condiciones de aceptación requieren sus propias comprobaciones.

## Primera entrega de requisitos — 30 de septiembre de 2026

Se modificó código funcional y pruebas para PT-01/PT-02. Los apartados posteriores
son históricos; sus fallos no describen por sí solos el estado de esta entrega.

Cambios comprobados:

- RF-MET-03: conversión explícita de UF a `numeric` al consultar detalle comercial.
  La prueba verifica el MRR exacto de una suscripción mensual de 12,5 UF y el 404
  de empresa inexistente; ya no se limita a comprobar un importe positivo.
- RF-SAL-03: `main.py` importa `worker.ops_tasks`, registrando la tarea manual y
  sus runners también con `QUEUE_BACKEND=inproc`.
- Descargas: se conserva el comportamiento de API. Motivo ausente/corto se
  rechaza con 422; doce espacios pasan la longitud inicial pero se rechazan con
  400/MOTIVO_REQUERIDO tras normalizar. La descarga cruzada envía motivo válido
  y verifica 404, llegando al control de pertenencia.
- Esquema 8: migración `09_indices_consola.sql` añade índices sobre
  `ops_jobs.componente`, `ops_jobs.pausado_por`, `ops_job_runs.actor_user_id`,
  `ops_incidentes.creado_por` y `metricas_mensuales_plan.plan_id`.
  `app_schema_migrations` registra la versión; API y worker tienen permiso de
  lectura del registro. Se actualizan detección, selección de scripts y fixtures.

Ejecuciones de esta entrega (no sumar entre sí):

| Ejecución | Resultado | Alcance |
|---|---|---|
| Reproducción antes de corregir | 19 aprobadas / 9 fallidas, 18,04 s | ADMIN + esquema: seis fallos ADMIN y tres de esquema. |
| Después de corregir backend y parámetros, antes de migración 09 | 29 aprobadas / 1 fallida, 19,78 s | ADMIN 19/19; descargas corregidas pasan; solo falta índice de FK. |
| Esquema final | 10 aprobadas / 0 fallidas, 4,93 s | Instalación completa, actualización desde versión 7 y segunda ejecución sin cambios; catálogo de jobs conservado. |

**Regresión completa final: 295 aprobadas, 0 fallidas, 568 advertencias,
484,26 segundos (8 min 4 s).** Incluye los 19 casos ADMIN y los 10 de esquema;
no se suman a estos últimos. El total aumenta de 294 a 295 por la nueva prueba
de migración desde versión 7. No se omitieron casos para obtener este resultado.
Las advertencias incluyen clave JWT corta del fixture, deprecación del cliente
de pruebas y uso de `distinct()` en consultas de requisitos/reportes.

**Entorno:** imagen existente `app-api`, Python 3.12.14, código del workspace
montado de solo lectura, contenedor temporal sin red y sin volúmenes de datos
habituales. PostgreSQL efímero creado por `pgserver`; mismos límites del fixture
respecto de `citext` y `pg_trgm`. Las dependencias son las de esa imagen, no una
nueva resolución ni un build de despliegue.

Comando reproducible desde la raíz, en PowerShell, con la imagen disponible:

```powershell
$basePruebas = (Resolve-Path BASE).Path
docker run --rm --network none --mount "type=bind,source=$basePruebas,target=/workspace/BASE,readonly" -w /workspace/BASE/app/backend -e PYTHONDONTWRITEBYTECODE=1 app-api python -m pytest -q -p no:cacheprovider --tb=short
```

**Límites:** no se migró ni reinició el entorno habitual, no se repitió el recorrido
en navegador y no se comprobó API→Redis→worker Celery en ejecución distribuida.
Pasan los casos inproc; esto no cierra todo RF-SAL-03. Fecha/fuente UF y casos
comerciales adicionales siguen pendientes en RF-MET-03. Permanecen las advertencias
de librerías y la clave JWT corta del fixture; no se presenta esto como validación
productiva ni como cierre de seguridad. La guía de actualización está en README.md.

## Histórico — ajuste de pruebas ADMIN del 29-09-2026

La suite administrativa se renombró de `test_ops.py` a `test_admin.py` y
sus peticiones usan ahora `/api/v1/admin`. Se retiraron las referencias a
la antigua consola separada de la suite y se actualizó el comando de pruebas
en `README_ops_Back.md`.

También se corrigió el fixture: `TRUNCATE users CASCADE` vaciaba el catálogo
de procesos por la FK `pausado_por`, aunque el catálogo estuviera excluido
de la limpieza. Ahora se restaura su estado inicial entre casos.

Validación focalizada en un contenedor temporal sin red ni datos actuales:
**13 pruebas aprobadas y 6 fallidas**, en 15,93 segundos. Las rutas antiguas
ya no causan los fallos. Permanecen dos causas funcionales del backend:

- El detalle comercial de cliente pasa UF como `double precision` a una
  función SQL que espera `numeric` (1 caso).
- La ejecución manual con `QUEUE_BACKEND=inproc` no tiene registrada la
  tarea `ops_ejecutar_run`; los procesos quedan en `queued` (5 casos).

Se conservaron las aserciones que detectan esos errores. Los nombres internos
de tablas, servicios y tareas todavía usados por la aplicación se mantienen;
el cambio elimina la ruta pública antigua y el nombre antiguo de la suite.
No se volvió a ejecutar la suite completa: los resultados siguientes son
el registro histórico previo a esta actualización.

## Resultado histórico — antes de las correcciones

La aplicación funciona para la navegación y las consultas comprobadas, pero la suite no está completamente aprobada: **270 pruebas pasan y 24 fallan**, de 294 casos ejecutados en 467,70 segundos.

No se modificó código funcional ni se corrigieron pruebas durante esta revisión.

## Entorno y alcance

- Servicios existentes: API, web, PostgreSQL, Redis, worker y Beat levantados. API, PostgreSQL y Redis reportaron healthy.
- Backend probado con el código del workspace montado de solo lectura en un contenedor temporal basado en `app-api`, sin red ni volúmenes de datos actuales. La suite creó su PostgreSQL efímero con el rol `acredittia_app`.
- El fixture sustituye citext por un dominio text y omite índices de pg_trgm: la suite no valida esas extensiones reales.
- Frontend: dependencias instaladas con `npm.cmd ci --no-audit --no-fund`; `npm.cmd run build` terminó con código 0, chequeo de tipos y generación de páginas. Hubo advertencias de caché de webpack.
- Navegador: Chrome sin ventana, con un perfil temporal separado que se cerró y eliminó al terminar. Se comprobaron DOM, navegación y errores de JavaScript/red; no se realizó una auditoría visual responsive exhaustiva.
- Las consultas al sistema actual se hicieron con las cuentas demo existentes. Los logins actualizaron el último acceso y crearon sesiones que se cerraron mediante logout. No se aprobaron empresas, cambiaron permisos ni eliminaron datos actuales.

## Funcionalidades comprobadas

| Funcionalidad | Resultado y límite |
|---|---|
| API y esquema | `/health` y `/health/esquema`: 200; esquema 7. |
| Login ADMIN | Inicio de sesión desde el formulario real; redirección a `/admin/dashboard`. |
| Dashboard | Renderiza contadores, acreditación, pendientes/vencidos y actividad. |
| Empresas | Carga 36 empresas; el botón Detalle abre la ficha agregada. |
| Buscador | Búsqueda de `demo` devuelve resultados; defecto confirmado: vehículos aparecen bajo el tipo trabajador. |
| Métricas | Carga indicadores, series y desglose por plan. Las sesiones siguen siendo estimaciones. |
| Salud | Carga riesgos y alertas; presenta estado global degradado, sin error de carga. No se determinó aquí la causa exacta de la degradación. |
| Usuarios | Carga el listado y los controles de roles/alcance. No se cambiaron permisos en los datos actuales. |
| Sistemas | Carga componentes, procesos e incidentes. No se ejecutaron ni pausaron procesos manualmente en el entorno actual. |
| Auditoría | Carga la tabla. Esto no certifica que se registren todas las acciones requeridas. |
| Acceso sin sesión | Navegar a `/admin/dashboard` redirige a `/login`. |
| Restricción de empresa | Cuenta demo de empresa recibe 403 en stats, usuarios y búsqueda administrativos. |
| Portal de empresa | Consultas de perfil, contratos, personal, equipos, documentos, alertas, resumen, KPI y usuarios responden 200. |

Las ocho rutas administrativas se cargaron en navegador; las comprobaciones realizadas no detectaron errores de JavaScript o respuestas HTTP fallidas en su carga. También respondieron 200 los endpoints actuales de procesos, incidentes, resumen de usuarios, distribución por plan/industria, actividad mensual y series de indicadores.

## Fallos históricos de la suite — corregidos en la primera entrega

| Casos | Causa observada | Acción necesaria |
|---|---|---|
| 19 | `tests/test_ops.py` consulta `/api/v1/admin/ops/...`, eliminado al unificar la API. | Actualizar las rutas de las pruebas y volver a ejecutar. No se puede afirmar que los casos pasen después de ese ajuste sin correrlos. |
| 2 | `test_version_de_esquema` y `test_health_esquema` esperan versión 6; la implementación usa 7. | Alinear expectativas con la migración vigente. |
| 1 | `test_descarga_documental_exige_motivo` espera 400 para un motivo corto; FastAPI devuelve 422 por `min_length=12`. | Definir el contrato de error y alinear API y prueba. El acceso con motivo corto sí es rechazado. |
| 1 | `test_documento_de_a_no_se_descarga_desde_b` omite el motivo obligatorio; recibe 422 antes del 404 esperado. | Enviar un motivo válido y volver a comprobar el rechazo entre empresas. Este fallo no demuestra una fuga de datos. |
| 1 | `test_foreign_keys_con_indice` identifica cinco claves foráneas sin índice de soporte según su consulta; entre ellas `ops_jobs_componente_fkey`. | Revisar las cinco relaciones y agregar los índices necesarios mediante migración. |

El resto de los casos pasó, incluyendo pruebas de autenticación, contratos, sujetos, operaciones, reportes, credenciales y aislamiento. No equivale a una garantía de cobertura total. Las pruebas usan un rol distinto al superusuario configurado actualmente en Docker.

## Hallazgos adicionales

1. **Buscador:** el defecto de clasificación se reprodujo en navegador: `Toyota Hilux` figura como trabajador porque la consulta de sujetos no filtra su tipo.
2. **Métricas:** se observó duración media superior a 1.600 minutos y crecimiento mensual de usuarios negativo. Deben revisarse las definiciones y la coherencia de las semillas/snapshots; estas observaciones no bastan para afirmar un error del cálculo. La interfaz identifica la duración como estimada.
3. **Datos demo:** el desglose comercial muestra planes separados `Básico` y `Basico`; conviene normalizar el catálogo.
4. **Dependencias:** npm emitió una advertencia de seguridad para Next.js 14.2.5 durante la instalación. No se realizó en esta revisión un análisis de vulnerabilidades ni se determinó su explotabilidad en esta aplicación.
5. **Seguridad de despliegue:** siguen pendientes los roles PostgreSQL sin superusuario, credenciales de desarrollo, mínimo privilegio de ADMIN y auditoría completa identificados en la revisión anterior.

## Siguiente entrega recomendada

PT-01 está completado en su alcance; no repetir como pendientes las correcciones de esquema, índices o parámetros ya aprobadas. La clasificación del buscador (PT-05-01) ya está corregida y probada. Continuar con Celery distribuido (PT-02), aislamiento/configuración (PT-03), permisos y auditoría (PT-04) y los restantes flujos de usuarios/buscador (PT-05). Incorporar las precisiones del SRS sobre catálogos, eliminaciones, metadatos sensibles, PII y clientes sin usuarios habilitados. Mantener las pruebas de mutación fuera de los datos actuales.
