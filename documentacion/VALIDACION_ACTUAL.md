# Validación funcional — actualizado al 4 de octubre de 2026

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

Compose local continúa en modo demostración, esquema 9. Esta ejecución de pruebas
usó una base temporal aislada y no aplicó migraciones ni modificaciones a la base
habitual. Estados de requisitos relacionados permanecen PAR/ISV cuando sus
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
por DEC-02 y validación visual; RF-BUS-02 conserva sus permisos granulares pendientes.

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
límites, alcance de usuarios sin empresa (DEC-02) y permisos granulares
(RF-BUS-02). AT-05 permanece parcial.

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
