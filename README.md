# Consola Interna de Administración — código backend

## Estado actual verificado

Actualizado al 16-11-2026.

- Avance estimado vigente: **83,7%** para las 37 fichas SRS (`3098 / 37`).
  El promedio de las ocho prioridades ADMIN es **81,0%**; P0/P1/P2: 81,7%,
  84,7% y 83,3%. El corte anterior de `3013 / 37` no coincidía con la suma
  de las estimaciones vigentes y se corrigió.
- RF-DAS-01 queda **IV/100%**: universos acordados, conteos documentales
  alineados, salida “N/A” sin datos evaluables, pruebas/build aprobados y
  revisión visual confirmada por el usuario.
- RNF-SEG-01 queda **IV/100% para el entorno destino**, tras la confirmación
  del usuario de roles separados, RLS efectivo con roles reales, denegaciones
  entre empresas/contratos, secretos externos y cumplimiento de DEC-10.
- RF-SEG-02 queda en **95%**: el usuario confirmó el recorrido de concesión
  temporal desde la vista de empresa y revisó personal/documentos de empresa.
  También confirmó la exportación CSV + JSON global y por empresa y su auditoría.
  Falta completar el inventario de otras lecturas sensibles y validar controles
  del despliegue.
- RNF-PER-01 queda **IV/100% para la carga local sintética acordada**: siete
  rutas, 100 solicitudes por ruta, concurrencia máxima 10, p95 entre 252,0 y
  729,5 ms y cero errores HTTP. No es SLA ni certificación de producción;
  resultados y límites en [Validación actual](documentacion/VALIDACION_ACTUAL.md).
- Las suites focalizadas de roles/configuración/tenants/esquema pasaron
  **76/76**; las de documentos/búsqueda/backups/privacidad, **88/88**. El build
  frontend pasó. El 16-11-2026 se volvió a ejecutar la suite backend completa:
  **492 aprobadas, 0 fallidas**, con un warning no bloqueante de Starlette/httpx.
  También pasaron el build frontend y `docker compose config --quiet`.
- RF-CLI-01 está en 80% por el cambio seguro de correo; RF-SAL-03, en 95% por
  el progreso medible y la actualización automática de procesos. La entrega
  SMTP se probó con dobles; no se verificó un servidor SMTP real.
- En la auditoría de dependencias reportada el 04-11, `npm audit --omit=dev`
  encontró **1 vulnerabilidad crítica y 2 altas** en Next.js/PostCSS/source-map-js;
  confirmar el estado actual con una nueva ejecución de auditoría.
- Respaldos: ciclo funcional local 100% acreditado (crear, descargar `.acb`,
  eliminar, importar, verificar y restaurar). Faltan RPO/RTO aprobados y
  recuperación ante pérdida total del entorno.
- Producción con datos reales: **NO-GO** por privacidad/retención, otros
  controles de seguridad y auditoría, dependencias, infraestructura y
  recuperación pendientes. RNF-SEG-01 está validado en el entorno destino;
  el Compose local de desarrollo conserva un rol elevado.

Estos porcentajes son estimaciones de cobertura de código/evidencia, no
mediciones de esfuerzo, cumplimiento contractual ni preparación certificada
para producción.

Documentos vigentes:

- [Estado de salud general](documentacion/ESTADO_SALUD_GENERAL.md)
- [Cronograma de cierre de 2 semanas](documentacion/CRONOGRAMA_CIERRE_PRODUCCION.md)
- [Validación actual](documentacion/VALIDACION_ACTUAL.md)
- [Requisitos con menor avance](documentacion/REQUISITOS_BAJO_AVANCE.md)

### Historial de regresión backend

| Fecha | Ejecución | Resultado | Observaciones |
|---|---|---|---|
| 16-11-2026 | Suite completa: `cd BASE/app/backend; python -m pytest -q` | **492 aprobadas, 0 fallidas** | PostgreSQL temporal; 1 warning no bloqueante Starlette/httpx. El fixture sustituye `citext` y neutraliza `pg_trgm`; no es validación productiva. |
| 14-10-2026 | Suite completa: `cd BASE/app/backend; python -m pytest -q` | **399 aprobadas, 0 fallidas** | 1 warning de compatibilidad Starlette/httpx. Corte histórico, sustituido por la ejecución del 16-11. |
| 01-10-2026 | Suite completa | **363 aprobadas, 0 fallidas** | PostgreSQL temporal; las pruebas relacionadas de autenticación/registro/perfil fueron 34/34. |

En la ejecución del 16-11 también pasaron `npm run build` en
`BASE/app/frontend` y `docker compose config --quiet` en `BASE/app`. Estos
resultados verifican código y configuración; no equivalen a pruebas en
producción ni cierran RNF-VAL-01.

La producción no queda declarada como cerrada ni lista para go-live con datos
reales. La política interna DEC-08 quedó acordada el 09-11-2026 y sus controles
de aplicación de privacidad/retención están implementados. El usuario confirmó
la migración y el job `ops_retencion` activo; reportó una ejecución local `ok`
el 10-11-2026 a las 00:18:52, con cero filas podadas. Falta verificar Log
Analytics, documentar la revisión histórica y obtener aprobación del responsable
de producción, junto con permisos granulares, dependencias vulnerables y
restauración efectiva.

El estado de producción continúa **NO-GO**. El aumento de avance no cierra los
bloqueos P0 de privacidad, seguridad/aislamiento, auditoría y continuidad.
Consultar el [estado de salud](documentacion/ESTADO_SALUD_GENERAL.md) y la
[validación actual](documentacion/VALIDACION_ACTUAL.md) para el detalle de
pendientes y límites de evidencia.

## Requisitos y planificación

- [SRS del proyecto](documentacion/SRS.md): alcance, actores, requisitos implementados y pendientes, evidencia y criterios de aceptación.
- [Cronograma de cierre de 2 semanas](documentacion/CRONOGRAMA_CIERRE_PRODUCCION.md): actividades críticas del 5 al 19 de noviembre de 2026.
- [Plan de trabajo](documentacion/PLAN_DE_TRABAJO.md): entregas propuestas, prioridades, dependencias y condiciones de cierre.
- [Validación actual](documentacion/VALIDACION_ACTUAL.md): resultados y limitaciones de las comprobaciones ejecutadas.
- [Gap Analysis](documentacion/GAP_ANALYSIS.md): brechas funcionales, operativas y de seguridad aún abiertas.

El SRS es un documento de trabajo; las decisiones de producto aun abiertas estan identificadas explicitamente.

Y esta la carpeta codigo_adminitracion con lo que quieren que sea desarrollado. 

La especificación original de la Consola Interna v1.0 describía 20 endpoints
bajo `/api/v1/admin/ops`. La API administrativa actual se publica bajo
`/api/v1/admin`; algunas rutas antiguas de Ops se conservan por compatibilidad.
El alcance, estado y evidencia vigentes se detallan en el SRS.

## Ejecutar en local

Requisitos: Docker Desktop.
Bash

cd BASE/app
docker compose up --build

### Actualización de esquema 20

Las migraciones `09_indices_consola.sql` y `10_version_sesion.sql` crean índices
administrativos y añaden `users.auth_version`. `11_ciclo_vida_contratos.sql`
añade estado de ciclo, motivo, actor y fecha de transición, preservando el estado
operacional existente del contrato.
`12_scheduling_operacional.sql` cambia el despachador de reportes programados a
una revisión cada minuto, necesaria para respetar el minuto de sus expresiones cron.
`13_respaldos_admin.sql` incorpora el esquema del módulo inicial de respaldos y
exportaciones ADMIN. La migración 18 (`18_confirmacion_cambio_email.sql`) agrega
el flujo de confirmación de correo; la migración 19
(`19_progreso_procesos.sql`) persiste etapa y porcentaje de procesos; la 20
(`20_telemetria_actividad.sql`) agrega telemetría de sesiones activas y retención.
La API exige el esquema 20 para este corte. Desde
`BASE/app`, actualizar las imágenes y aplicar las migraciones pendientes antes
de recrear los servicios:

```bash
docker compose build api worker beat migrate
docker compose run --rm migrate
docker compose up -d api worker beat
```

Si se configuró `SCHEMA_VERSION_ESPERADA` externamente, debe coincidir con la
versión que requiere la aplicación (20 para este corte). Las migraciones
conservan los datos; la validación automatizada se realiza en PostgreSQL
temporal y no aplica cambios a la base habitual. La migración 19 se validó con
las pruebas focalizadas descritas en `documentacion/VALIDACION_ACTUAL.md`; la
migración 20 también pasó pruebas en PostgreSQL temporal. Confirma el esquema
de tu entorno antes de arrancar la API y workers.

En Usuarios, las cuentas revocadas tienen la acción **Reactivar** con confirmación.
Conserva identidad, rol y alcance. Revocar o cambiar el estado activo desde ADMIN
invalida los JWT anteriores y los refresh tokens; el usuario debe iniciar sesión
nuevamente. Reactivar no aprueba una solicitud pendiente/rechazada. Instalar esquema
11 fue el requisito de la versión que introdujo esta función; para el código
actual, seguir la sección de esquema 20 anterior. Las cuentas que ya estaban
revocadas también invalidan sus sesiones antiguas al reactivarse.



## ⚠️ Problemas Encontrados y Notas de Configuración Backend

    Actualización de versión esperada (config.py): Durante la puesta en marcha, la API fallaba al iniciar con un error de validación de esquema ("Esquema en versión 7, se esperaba 6"). Esto ocurría porque en la guía de instalación original no se especificaba que en el archivo config.py era necesario actualizar explícitamente el dígito de la variable de configuración de 6 a 7:


### Cambios 01-09-2026
Se Instalo el fronted tal como se especifica en README_ops_Front
Se Instalo el backend tal como se especifica en README_ops_Back
Ambos con ajustes
Se dejo el Mock=0 (.env.local) y esta funcionando con la poblacion de datos actual que es 1.

### Cambios 04-09-2026
Poblacion de datos a traves de seeds.py para sistema y procesos.

Las semillas requieren `SEED_DEMO_ENABLED=true` y se prohíben con
`APP_ENV=production`. Su valor por defecto es `false`; el Compose base las activa
explícitamente para demostración local. Sin semillas, los catálogos y el primer
administrador deben aprovisionarse mediante un procedimiento separado; este cambio
no crea automáticamente un administrador productivo ni elimina cuentas demo existentes.

Para el modo producción, definir `APP_ENV=production`, un `JWT_SECRET` propio y
aleatorio de al menos 32 bytes, `DB_RLS_ENABLED=true`,
`DB_APPLY_SCHEMA_ON_START=false`, `SEED_DEMO_ENABLED=false` y
`AUTH_DEV_RESET_TOKEN_ENABLED=false`. La aplicación rechaza combinaciones inseguras
al cargar la configuración. Esto no comprueba todavía los privilegios reales del
rol PostgreSQL; el Compose base sigue siendo de desarrollo y no es una plantilla
productiva. El overlay ngrok hereda ese entorno demo: un túnel no lo convierte en
despliegue productivo seguro.

API y Celery instalan además una guarda para conexiones PostgreSQL nuevas en
`APP_ENV=production`: rechaza superusuario, BYPASSRLS, CREATEDB, CREATEROLE y
propiedad de tablas del esquema public, incluidas membresías de roles. El comando
`python -m migrate.run` permanece separado y puede usar la identidad de migración.
Este control no cambia ni aprovisiona roles y no verifica por sí solo todas las
políticas RLS. El Compose de desarrollo conserva sus credenciales actuales;
activar production con ellas provoca rechazo de la conexión.

La recuperación ya no devuelve tokens por usar un secreto `dev-*`. Solo los
entornos no productivos que activen `AUTH_DEV_RESET_TOKEN_ENABLED=true` pueden
recibir `_dev_token`; por defecto y en Compose está desactivado. El envío real de
correo para recuperación de contraseña sigue pendiente, por lo que aún no hay un
flujo productivo completo de recuperación. Las pruebas aisladas habilitan estas
opciones explícitamente. El seed actual incluye al menos 30 empresas demo con
industrias, usuarios y antigüedades diferentes para
que los filtros y el resumen de clientes se parezcan a un entorno de producción.

Para crear el primer administrador productivo sin ejecutar semillas demo, configurar
`INITIAL_ADMIN_EMAIL`, `INITIAL_ADMIN_PASSWORD` y opcionalmente
`INITIAL_ADMIN_NAME`, luego ejecutar desde `BASE/app/backend`:

```bash
python scripts/provision_admin.py
```
Se agregaron planes Básico, Pro y Enterprise con suscripciones activas, en trial,
morosas y canceladas, además de facturas de ejemplo con estados variados.
Se agregaron integraciones SIGA, Workmate, Metacontratas, WebControl, WhatsApp y
Google Drive con estados activos, con error y desconectados, junto con sus logs de
sincronización. Las credenciales son referencias ficticias a Key Vault y no secretos.
La consola Ops ahora incluye disponibilidad variable, historial de jobs exitosos,
fallidos y con timeout, además de incidentes abiertos/resueltos que representan
decisiones operativas de producción.
Se corrigio `ops_tasks.py` para castear el valor UF de `double precision` a `numeric` antes de llamar a `ops_snapshot_metricas`, evitando el error de PostgreSQL al cargar los indicadores.

### Cambios 06-09-2026
## Exponer API y frontend con ngrok

Para una demo temporal se utiliza un solo dominio de ngrok. El frontend queda
expuesto públicamente y Next.js redirige internamente las llamadas `/api` al
backend, que sigue escuchando en el puerto 8000 dentro de Docker.

1. Copiar `BASE/app/.env.ngrok.example` como `BASE/app/.env` y completar
    `NGROK_AUTHTOKEN` y `NGROK_DOMAIN`.
2. Levantar la composición con el override de ngrok:

    ```bash
    cd BASE/app
    docker compose -f docker-compose.yml -f docker-compose.ngrok.yml up --build
    ```

    La plataforma quedará disponible en `https://<NGROK_DOMAIN>`. No se
    necesita un segundo enlace para la API: las rutas `/api/...` se envían al
    servicio `api:8000` dentro de la red Docker.
3. El inspector local de ngrok queda disponible en
    `http://localhost:4040`.

El archivo `BASE/app/.env` contiene credenciales y no debe versionarse. Para
el arranque local habitual se sigue usando únicamente `docker-compose.yml`.

### Registro de tareas Ops en Celery

Se agregó en `BASE/app/backend/worker/celery_app.py` la importación de
`registrar_ops` desde `worker.ops_tasks` y su ejecución con la instancia
`celery`. Esto registra en el worker las tareas de la consola interna y añade
al beat los procesos de heartbeat, disponibilidad, snapshots de indicadores y
retención.

Este cambio es necesario para que, al levantar Docker, los heartbeats se
ejecuten y la vista de Sistemas pueda mostrar el estado real de la API, la
base de datos, los workers y los demás componentes. Sin este registro, los
componentes quedan sin heartbeat y aparecen como caídos aunque sus
contenedores estén funcionando.

### Corrección de Celery Beat y estados de Sistemas

Al probar la consola Ops, todos los componentes aparecían como `Caído` aunque
la API, PostgreSQL y Redis estuvieran funcionando. La causa era que Celery
Beat no podía crear su archivo `celerybeat-schedule` por permisos, por lo que
no enviaba el heartbeat periódico. Además, el worker y Beat estaban heredando
el healthcheck HTTP de la API, aunque esos procesos no sirven la API en el
puerto 8000.

Se ajustó `BASE/app/docker-compose.yml` para que:

- Celery Beat guarde su programación en `/tmp/celerybeat-schedule`.
- Worker y Beat no utilicen el healthcheck HTTP de la API.

Para aplicar estos cambios, reconstruir los servicios:

```bash
cd BASE/app
docker compose up -d --build worker beat
```

La corrección fue verificada: Beat envía `ops-heartbeat` cada minuto y el
worker procesa `acredittia.ops_tick` correctamente. Después de iniciar, recarga
la vista de Sistemas para que la plataforma consulte los nuevos heartbeats.

### Cambios 19-09-2026

Se revisaron `README_CLIENTE.md` y `IDEA/Acredittia_Wireframe_Demo.html` para
alinear la interfaz de la empresa usuaria con el flujo visual definido para
Acredittia.

Se actualizo exclusivamente la capa visual del frontend:

- Se incorporo una identidad visual basada en tonos carbon, cobre y crema.
- Se rediseño el sidebar de la vista empresa con estados activos, iconografia
    simple, indicador de alertas y comportamiento responsive para pantallas
    pequeñas.
- Se ajusto el layout protegido para mejorar el espaciado, la lectura y la
    adaptacion movil.
- Se rediseño la pantalla de login con una composicion dividida, mejor
    jerarquia visual y estados de registro, recuperacion y cuenta en revision.
- Se actualizaron botones, tablas, chips, tarjetas KPI, paneles y estados
    documentales compartidos.
- Se ajusto el dashboard para reflejar la jerarquia del wireframe: resumen
    operativo, cumplimiento por contrato, acreditaciones, vencimientos y
    actividad reciente.

No se modificaron el backend, los endpoints, los tipos TypeScript ni la
logica de carga de datos. El frontend fue validado con `npm run build`,
completando correctamente la compilacion, el chequeo de tipos, el lint y la
generacion de las 17 rutas existentes.

Ademas, se creo y agrego el modulo visual de Calendario siguiendo el wireframe
y reutilizando la estructura existente del frontend y la API disponible:

- Se creo la ruta `/calendario` y se agrego su acceso al sidebar de la empresa.
- Se implemento una vista mensual con navegacion entre meses y seleccion de
    dias.
- Se agrego un filtro por categoria y una leyenda visual para vencimientos,
    vencidos, mantenciones y capacitaciones.
- Se integraron los vencimientos proyectados desde los documentos existentes,
    sin duplicarlos como eventos manuales.
- Se habilito la creacion, edicion y eliminacion de eventos anotados por la
    empresa para mantencion, capacitacion, administrativo, entrega y otros.
- Se agrego el panel lateral con el detalle del dia seleccionado y el acceso al
    expediente de personal o equipos cuando corresponde.
- Se implemento el modal `Anotar evento`, respetando que los vencimientos
    proyectados no se editan ni eliminan desde el calendario.

La nueva pantalla fue validada con `npm run build`, completando correctamente
la compilacion, el chequeo de tipos, el lint y la generacion de las 18 rutas.

### Cambios 21-09-2026

Se reviso el apartado de Alertas del wireframe y se aplico a la pantalla
`/alertas` de la plataforma, reutilizando el cliente y los endpoints existentes.

- Se agrego el filtro por origen: vencimientos, inteligencia artificial,
    integraciones y sistema.
- Las alertas no leidas ahora se destacan con borde cobre, como en el
    wireframe.
- Se muestran de forma legible la severidad, el estado, el origen, la fecha y
    la plataforma asociada cuando corresponde.
- Se agruparon las acciones de cada alerta: marcar como leida, pasar a
    progreso, resolver y reabrir.
- Se agrego informacion contextual del sujeto, documento y contrato
    relacionado.
- Se habilito el acceso al contrato relacionado cuando la alerta dispone de
    ese vinculo.
- Se conservaron los KPI de criticas, advertencias, alertas activas, no leidas
    y resueltas en los ultimos 30 dias.
- Se mantuvieron la paginacion, el aislamiento por empresa y contrato, y la
    generacion automatica de alertas por vencimientos, IA e integraciones.

No se modifico el backend ni la logica de generacion de alertas. El frontend
fue validado con `npm run build`, completando correctamente la compilacion, el
chequeo de tipos, el lint y la generacion de las 18 rutas existentes.


### Cambios 28-09-2026: unificación Admin + Ops

Se unificaron el back-office de administración de plataforma y la consola
interna de operaciones en una única experiencia administrativa. La finalidad
es que el rol `admin` acceda desde `/admin` a las funciones de Admin y Ops,
manteniendo la interfaz visual de la consola Ops.

#### Cambios técnicos principales

- El router que contiene la lógica de Ops conserva sus servicios, modelos,
    métricas, procesos e incidentes, pero ahora publica sus 20 endpoints bajo
    `/api/v1/admin`. La superficie anterior `/api/v1/admin/ops` dejó de usarse.
- Los endpoints existentes de Admin normal (`companies`, `stats`, `faenas`,
    `requisitos/templates`, `reset-demo`, entre otros) se mantienen bajo el
    mismo prefijo `/api/v1/admin` y comparten la dependencia de autorización
    `require_admin`.
- La entrada frontend `/admin` redirige a la consola unificada. Sus vistas
    públicas son `/admin/usuarios`, `/admin/sistemas`, `/admin/indicadores` y
    `/admin/plataforma`.
- La estética, layout, tema, idioma, gráficos, indicadores, disponibilidad,
    procesos e incidentes de Ops se conservan. Las rutas visuales se resuelven
    internamente mediante rewrites de Next.js, por lo que el usuario trabaja
    únicamente con la superficie `/admin`.
- La antigua gestión de empresas se incorporó como la sección
    `/admin/plataforma`, incluyendo aprobación y rechazo de empresas,
    estadísticas globales, impersonación y reinicio de la demo.
- La autenticación de la consola y del back-office comparte los tokens JWT,
    incluido el refresh, para que ambas capas puedan consumir los endpoints
    administrativos sin sesiones duplicadas.

La estructura interna conserva nombres como `admin_ops.py` y `lib/ops` para
evitar una refactorización innecesaria de la lógica ya implementada; la
separación Ops desaparece de la API pública y de la navegación del usuario.

#### Dashboard global: cumplimiento de la tarea

Como parte de la unificación se amplió el dashboard global de `/admin` para
concentrar la visión operativa y comercial de toda la plataforma. Se extendió
`GET /api/v1/admin/stats` con métricas calculadas desde las tablas existentes,
sin crear una API paralela ni duplicar la lógica de Admin y Ops.

La tarea solicitada quedó cubierta de la siguiente forma:

- **Empresas:** total, aprobadas, pendientes y rechazadas.
- **Contratos:** total global de contratos.
- **Trabajadores:** total y trabajadores acreditados.
- **Usuarios:** total de usuarios y usuarios activos.
- **Acreditación global:** porcentaje global calculado sobre documentos
    obligatorios y no EMSIPOR.
- **Clientes activos:** empresas aprobadas con suscripción activa o en trial.
- **Evolución mensual:** series mensuales de actividad global y MRR de los
    últimos 12 meses.
- **MRR:** valor actual disponible y evolución mensual desde los snapshots
    comerciales existentes.
- **Documentos pendientes y vencidos:** se separaron explícitamente los
    estados `falta`, `porvenc` y `venc`, evitando presentarlos como un único
    indicador ambiguo.
- **Actividad global completa:** total histórico, actividad de los últimos 30
    días, distribución por módulo y tipo, últimos eventos registrados y
    clientes con baja actividad.
- **Sesiones y tiempo de uso:** sesiones vigentes, usuarios con actividad y
    tiempo promedio estimado a partir del intervalo entre el primer y último
    evento de cada usuario durante los últimos 30 días.
- **Documentos procesados:** revisiones IA totales, completadas, en proceso,
    pendientes y fallidas.

El dashboard se implementó en `/admin/plataforma` y ahora `/admin` lo utiliza
como pantalla inicial. La interfaz reutiliza el layout visual de Ops con
tarjetas KPI, gráficos mensuales, tablas de actividad y desglose operativo.
El tiempo de uso se identifica como estimado porque el modelo actual no
registra el inicio y cierre exactos de cada sesión; para obtener una duración
real por sesión sería necesario añadir telemetría de inicio, actividad y
cierre de sesión.

#### Gestión global de empresas: cumplimiento de la tarea

Se reforzó la gestión global de empresas dentro de `/admin/plataforma` y se
ajustó el contrato de `GET /api/v1/admin/companies` para entregar únicamente
información operativa necesaria para la consola administrativa.

Los cambios realizados cubren lo siguiente:

- **Listado global:** mantiene el listado de empresas y su estado de cuenta.
- **Plan:** cada fila muestra el plan asociado o `Sin plan`.
- **Usuarios:** se muestra el total de usuarios de la empresa.
- **Nivel de actividad:** se calcula con la proporción de usuarios que
    registraron actividad durante los últimos 30 días.
- **Última actividad:** se muestra la fecha del último evento registrado.
- **Contratos y trabajadores:** ahora la tabla muestra ambos contadores por
    empresa, además del resto de indicadores operativos.
- **Aprobación y rechazo:** se conservaron las acciones para solicitudes
    pendientes y sus controles existentes.
- **Impersonación:** se mantiene la acción para entrar al contexto operativo
    de una empresa aprobada.
- **Reinicio de demo:** se mantiene disponible únicamente para empresas demo.
- **Datos innecesarios:** el backend dejó de devolver `rut` y `email` en el
    listado y en el detalle global. Esos datos ya no se renderizan ni se
    transportan como parte del contrato operativo de la consola.
- **Detalle global protegido:** el botón `Detalle` consulta
    `GET /api/v1/admin/companies/{company_id}`, protegido por la autorización
    administrativa del router. Devuelve solo métricas agregadas: plan,
    usuarios, actividad, contratos, trabajadores, equipos, documentos,
    cumplimiento y alertas activas.

El cálculo se centralizó en `_company_out()` para que el listado y el detalle
compartan las mismas reglas y no existan diferencias entre ambas vistas. La
consulta de búsqueda puede seguir usando los campos internos necesarios para
localizar una empresa, pero esos valores no forman parte de las respuestas
enviadas al frontend.

#### Buscador global: cumplimiento de la tarea

Se implementó un buscador global para la consola administrativa en
`/admin/plataforma`. Antes, la búsqueda estaba limitada a los filtros
individuales de cada listado y, en el caso de empresas, solo consideraba
nombre, RUT y email.

Los cambios realizados son:

- Se agregó `GET /api/v1/admin/search`, protegido por `require_admin`.
- La búsqueda ahora cubre cuatro tipos de resultado: **empresas**,
    **contratos**, **trabajadores** y **usuarios**.
- Las empresas se pueden localizar internamente por nombre, RUT o email, pero
    esos campos no se devuelven en la respuesta.
- Los contratos se buscan por nombre o código.
- Los trabajadores se buscan por nombre o cargo.
- Los usuarios se buscan por nombre o email, pero el email nunca se expone en
    el resultado.
- Cada resultado incluye su tipo, empresa asociada, identificador seguro,
    descripción resumida, permiso requerido y ruta de detalle permitida.
- Se definió una matriz de permisos por tipo:
    `admin.companies.read`, `admin.contracts.read`, `admin.subjects.read` y
    `admin.users.read`. Actualmente todos requieren el rol administrativo,
    pero la separación permite restringir cada categoría cuando existan roles
    más específicos.
- Los resultados no incluyen contraseñas, tokens, RUT ni emails. El acceso al
    detalle utiliza el identificador de empresa y vuelve a pasar por el
    endpoint protegido de detalle global.
- La interfaz incorpora una caja de búsqueda en el dashboard y permite abrir
    el detalle agregado de la empresa asociada a cada resultado.

Con esto se mantiene una búsqueda transversal sin mezclar permisos ni exponer
datos personales innecesarios. La búsqueda interna de RUT y email se conserva
solo como criterio de localización en la base de datos y no como información
de salida de la API.

#### Métricas SaaS: evaluación y cumplimiento de la tarea

Se revisaron las métricas SaaS existentes antes de agregar lógica nueva para
evitar duplicidad. La plataforma ya contaba con empresas activas, usuarios
activos, crecimiento mensual, MRR, churn, clientes con baja actividad y altas
o bajas en los indicadores Ops (`/admin/indicadores`). Además, el dashboard
global ya consumía desde `GET /api/v1/admin/stats` las métricas básicas de
sesiones y documentos procesados.

Los cambios necesarios se incorporaron en el contrato existente de
`GET /api/v1/admin/stats`, sin crear un endpoint SaaS paralelo:

- Se agregó originalmente un indicador heredado de **duración promedio
    estimada de sesiones** desde la vida de refresh tokens. Después se retiró
    de la interfaz para no confundirlo con tiempo activo medido; el campo
    antiguo se conserva en la API solo por compatibilidad.
- Se agregaron los **usuarios activos diarios (DAU)** y **semanales (WAU)**,
    calculados sobre usuarios que registraron eventos reales de actividad.
- Se agregaron las series históricas de DAU de 30 días y WAU de 12 semanas
    para permitir evolución y comparación temporal.
- Se mantienen métricas de documentos procesados, MRR, churn, crecimiento y
    flujo de altas/bajas. DAU/WAU y las series de adopción continúan bajo el
    alcance de sus requisitos.
- RF-MET-02 implementa telemetría de tiempo activo medido por usuario; la vista
    de Salud muestra esa duración como métrica, mientras que la duración
    estimada por sesión no se presenta en la interfaz.

El campo legado de duración promedio sigue siendo estimado y no se muestra en
la interfaz. El tiempo activo, en cambio, se mide con sesión autenticada,
pestaña visible, interacción reciente y señales periódicas; se pausa tras
cinco minutos sin actividad. La telemetría y su retención cuentan con pruebas
focalizadas, según el detalle de RF-MET-02 y DEC-05 en el SRS.

#### Alertas y salud de clientes: cumplimiento de la tarea

Se revisaron los endpoints existentes antes de agregar lógica nueva. La salud
de API, workers, base de datos e integraciones ya estaba disponible en
`GET /api/v1/admin/sistemas/estado`, los incidentes en
`GET /api/v1/admin/incidentes` y la baja actividad o morosidad en los
indicadores de clientes. Por eso se reutilizaron esos contratos y se amplió
`GET /api/v1/admin/stats` con los riesgos que faltaban.

El dashboard `/admin/plataforma` ahora incluye:

- **Empresas con baja acreditación:** empresas aprobadas con menos de 70% de
    documentos obligatorios correctos, mostrando total y documentos válidos.
- **Contratos con muchos pendientes:** contratos con tres o más documentos en
    falta o vencidos, agrupados por contrato y empresa.
- **Documentos vencidos por empresa:** agrupación de documentos vencidos para
    priorizar clientes y acciones de regularización.
- **Clientes morosos:** empresas aprobadas cuya suscripción está en estado
    `morosa`, incluyendo el plan asociado.
- **Bandeja centralizada de alertas:** alertas activas de clientes agrupadas
    en una tabla común con empresa, origen, severidad, título y fecha.
- **Salud operacional:** se mantiene la consulta de API, workers, base de
    datos e integraciones desde `/admin/sistemas/estado`, ahora visible también
    desde el dashboard global.
- **Empresas afectadas:** los componentes degradados o caídos devuelven el
    impacto global sobre las empresas aprobadas activas y la interfaz muestra
    el número de empresas afectadas.

No se creó un endpoint paralelo de alertas ni otro endpoint de salud. La
respuesta de `GET /api/v1/admin/stats` concentra los riesgos de clientes y
`GET /api/v1/admin/sistemas/estado` conserva la fuente de verdad operacional.
Actualmente los incidentes técnicos se modelan a nivel de componente, por lo
que su impacto se marca como global; para asociarlos a empresas específicas
sería necesario agregar una relación de alcance por incidente.

#### Usuarios, roles y permisos: gestión global de Admin

Sí, este alcance corresponde al nuevo `/admin`: la administración global de
usuarios y permisos no debe quedar limitada al contexto de una empresa. Se
reutilizó el modelo existente de `users`, con los roles `admin`, `company` y
`contract_admin`, junto con `company_id`, `contrato_id`, `activo` y
`last_login_at`.

Se implementó lo siguiente:

- **Listado global de usuarios:** `GET /api/v1/admin/users`, con usuario,
    email, rol, empresa, contrato, estado y último acceso.
- **Cambio de rol:** `PATCH /api/v1/admin/users/{user_id}` permite cambiar
    entre `admin`, `company` y `contract_admin`.
- **Asignación por empresa:** los roles `company` y `contract_admin` exigen
    una empresa válida.
- **Asignación por contrato:** `contract_admin` exige además un contrato que
    pertenezca a la empresa seleccionada. El rol `company` elimina el alcance
    de contrato y `admin` queda sin empresa ni contrato.
- **Revocación:** `POST /api/v1/admin/users/{user_id}/revoke` desactiva la
    cuenta sin borrar la identidad ni su historial. No se permite que un
    administrador revoque su propia cuenta.
- **Catálogo de asignación:** `GET /api/v1/admin/users/catalog` entrega solo
    empresas aprobadas y sus contratos para construir los selectores de la
    consola.
- **Último acceso:** se muestra `last_login_at`, con el valor `Nunca` cuando
    la cuenta todavía no ha iniciado sesión.
- **Auditoría:** `GET /api/v1/admin/users/audit` consulta los cambios de rol,
    empresa, contrato y activación registrados en `actividad`.
- **Interfaz:** `/admin/usuarios` ahora incluye la tabla de administración
    global, controles de rol y alcance, revocación y bandeja de auditoría,
    además de conservar sus métricas analíticas de usuarios.

Todos los endpoints nuevos están protegidos por `require_admin`. Las reglas
de validación impiden contratos de otra empresa, roles incompletos y la
auto-revocación del administrador actual. La auditoría conserva quién ejecutó
el cambio, qué usuario fue afectado, qué campos cambiaron y cuándo ocurrió.

#### Auditoría y trazabilidad: cumplimiento de la tarea

El backend ya utilizaba la tabla append-only `actividad`, pero la nueva
interfaz no tenía una consulta global. Se agregó una vista administrativa
dedicada en `/admin/auditoria`, reutilizando esa misma fuente de trazabilidad
para no duplicar registros ni crear otro sistema de auditoría.

Se implementó:

- `GET /api/v1/admin/audit`, protegido por `require_admin`, con filtros por
    módulo, tipo, actor, rango de fechas y búsqueda textual.
- Consulta global de quién ejecutó una acción registrada, empresa afectada,
    módulo, entidad, descripción y fecha. Los inicios de sesión no se guardan
    todavía como eventos históricos globales; `last_login_at` conserva solo el
    último acceso de cada usuario.
- Visualización de acciones de creación, modificación y eliminación que ya
    quedan registradas por los módulos de empresas, usuarios, contratos,
    documentos, personal, integraciones, reportes y demás dominios.
- Registro explícito de descargas de archivos documentales como eventos de
    `visualizacion`, incluyendo actor, empresa, documento y nombre del archivo.
- Registro de descargas documentales con motivo obligatorio (mínimo 12
    caracteres), guardado como metadata de auditoría y visible en la vista
    global.
- La auditoría de cambios de permisos queda relacionada con usuario afectado,
    actor administrativo, campos modificados y fecha mediante el módulo
    `usuarios`.
- La interfaz `/admin/auditoria` muestra el historial global con filtro por
    empresa, módulo o descripción.

La auditoría conserva los datos históricos y no permite edición ni eliminación
desde la API. Los eventos ejecutados por procesos automáticos o IA aparecen
con actor `Sistema`; el email del actor y la metadata completa no se devuelven
por defecto para reducir exposición de datos personales. La consulta continúa
limitada al rol `admin`, ya que contiene actividad transversal de las empresas.

#### Seguridad y aislamiento: revisión y cambios

Se revisaron los controles existentes antes de modificar el acceso. La base ya
aplica aislamiento por `company_id` mediante RLS y validaciones explícitas;
`contract_admin` queda restringido por `contrato_id`; las rutas administrativas
exigen `require_admin`; y las descargas usan URLs firmadas de corta duración
después de validar que el blob pertenece al documento, empresa y alcance de
contrato solicitado.

Cambios completados para cerrar parte de las brechas:

- **Auditoría unificada:** `/admin/auditoria` consume
    `GET /api/v1/admin/audit`, que consulta el registro append-only existente.
    Permite filtrar por búsqueda, módulo, tipo de acción y fechas.
- **Motivo para documentos sensibles:** toda descarga de un archivo documental
    exige un motivo de al menos 12 caracteres. El motivo queda en metadata de
    auditoría, junto al actor, empresa, documento y archivo. Se aplica a todas
    las descargas porque el modelo actual no clasifica documentos por nivel de
    sensibilidad.
- **Exportaciones:** se mantienen los límites existentes de alcance por
    empresa y contrato, la exclusión de `contract_admin` de reportes globales y
    el límite de filas para exportación síncrona. Se registra tanto la
    generación de la exportación como la descarga del reporte generado.
- **Datos personales por defecto:** la gestión global de empresas ya omite
    RUT y email en sus respuestas; el buscador puede usar esos campos como
    criterio interno sin devolverlos. La lista global de usuarios oculta el
    email y la auditoría no expone email ni metadata completa en el feed.

Brechas que permanecen y no deben considerarse resueltas:

- **Permisos Admin granulares:** la autorización sigue siendo de rol único
    `admin`. Las etiquetas de permiso del buscador son informativas; no existe
    todavía una matriz persistida de capacidades por administrador. Para
    aplicar mínimo privilegio real se necesita definir capacidades, asignarlas
    a cuentas Admin y verificarlas en cada endpoint.
- **Inicios de sesión históricos:** `last_login_at` conserva solo el último
    acceso por usuario. La tabla `actividad` requiere `company_id`, por lo que
    no puede registrar correctamente inicios de sesión de administradores sin
    empresa. Una auditoría completa de autenticación requiere un registro de
    seguridad global que admita eventos sin tenant.
- **Concesión temporal de lectura ADMIN:** la vista de empresas ofrece
    “Autorizar lectura y ver (1 h)”, solicita motivo y concede acceso limitado
    a personal y documentos de una empresa; el usuario confirmó que el
    recorrido funciona y queda auditado. La concesión no añade escritura ni
    bloquea permisos ADMIN ordinarios. Siguen pendientes la revisión de otras
    lecturas sensibles y el listado global de usuarios, que permanece en RF-USU.

La auditoría global oculta PII por defecto, pero las pantallas de gestión de
cuentas que necesiten identificar un usuario deben incorporar un flujo
explícito y auditado para revelar su correo. La asignación de permisos Admin
por capacidad y el registro de login global quedan como siguientes cambios de
modelo, no como funcionalidades ya disponibles.

#### Sesión única para Admin y Ops

Se eliminó el segundo inicio de sesión de la consola Ops. El acceso a `/admin`
ahora reutiliza la sesión creada por el login general de la plataforma:

- La consola consulta el mismo access token, refresh token y usuario que usa el
    resto del frontend; no mantiene claves ni credenciales separadas para Ops.
- Al entrar o recargar una vista Admin, la guardia renueva la sesión existente
    y verifica que el rol sea `admin`.
- Si no hay sesión o esta expiró, se redirige al login general `/login`. Si la
    sesión pertenece a un usuario que no es administrador, se redirige a
    `/dashboard`.
- Se eliminó la pantalla `/ops/login` y el rewrite `/admin/login` que llevaba
    al login separado.
- Los errores 401 de la API administrativa vuelven al login general, no a una
    pantalla de autenticación Ops.

Con esto el administrador inicia sesión una sola vez desde la entrada normal y
accede a las vistas unificadas de `/admin` con la misma identidad y ciclo de
renovación de sesión del portal.

#### Reorganización de módulos Admin

Se reorganizó la consola administrativa para distribuir las funciones según su
objetivo y reducir la concentración de información que existía en Plataforma.
La navegación de `/admin` queda estructurada en ocho módulos:

- **Dashboard global** (`/admin/dashboard`): resumen de empresas, contratos,
    trabajadores, usuarios, acreditación, estados documentales y actividad de
    la plataforma. Muestra riesgos de forma resumida y enlaza a su gestión.
- **Gestión global de empresas** (`/admin/empresas`): listado y estado de las
    empresas, plan, nivel de actividad, última actividad, contratos,
    trabajadores, aprobación, rechazo, impersonación, reinicio de demo y
    detalle global agregado.
- **Buscador global** (`/admin/busqueda`): búsqueda independiente de empresas,
    contratos, trabajadores y usuarios, con acceso a la ficha agregada de la
    empresa relacionada.
- **Métricas SaaS** (`/admin/metricas`): MRR, churn, NRR, altas/bajas,
    crecimiento, clientes activos, sesiones, DAU/WAU, duración estimada y
    documentos procesados. MRR y clientes activos se presentan aquí como su
    vista analítica principal y se quitaron de Empresas para no duplicarlos.
- **Alertas y salud de clientes** (`/admin/salud`): baja acreditación,
    contratos con documentos pendientes, vencimientos por empresa, clientes
    morosos, alertas centralizadas y un resumen de estado operacional.
- **Usuarios, roles y permisos** (`/admin/usuarios`): administración global
    de usuarios, roles, empresa, contrato, revocación, último acceso y
    auditoría de cambios de permisos. La analítica que antes compartía esta
    pantalla queda en Métricas SaaS.
- **Sistemas y procesos** (`/admin/sistemas`): se conserva como módulo propio
    para disponibilidad, procesos e incidentes técnicos.
- **Auditoría y trazabilidad** (`/admin/auditoria`): se conserva como módulo
    propio para consultar eventos globales.

La vista anterior `/admin/plataforma` redirige a `/admin/empresas`, y
`/admin/indicadores` redirige a `/admin/metricas` para mantener compatibilidad
con enlaces previos. Las rutas Ops antiguas de Plataforma, Usuarios e
Indicadores también redirigen a sus destinos Admin. `/admin` y la entrada Ops
abren ahora el Dashboard global.

## Cambios a la fecha — 16-11-2026

El documento funcional vigente es el [SRS v0.97](documentacion/SRS.md). Esta
sección resume los cambios relevantes y el estado conocido a la fecha; no
sustituye los criterios, pendientes ni evidencias detallados en el SRS y la
[validación actual](documentacion/VALIDACION_ACTUAL.md).

**Resumen del corte:** la suma de las 37 fichas es **83,7% (3098/37)** y el
promedio de las ocho prioridades ADMIN, **81,0%**; P0/P1/P2: 81,7%, 84,7% y
83,3%. RF-DAS-01 queda IV/100%; RNF-SEG-01, IV/100% en el entorno destino; y
RF-SEG-02, PAR/95% tras confirmar el recorrido de concesión y su auditoría,
incluida la exportación global y por empresa.
RNF-PER-01 queda IV/100% para la carga local sintética acordada: siete rutas
cumplieron p95 ≤ 800 ms y cero errores, con p95 máximo de 729,5 ms. Esta prueba
no es SLA ni certificación de producción. Las suites focalizadas de seguridad
(76/76) y acceso sensible (88/88) pasaron; la suite backend completa más
reciente pasó 492/492 el 16-11. Otros controles de seguridad,
privacidad/retención, auditoría, SMTP real, recuperación y continuidad siguen
pendientes; producción permanece **NO-GO**.

### Funcionalidad y cambios recientes

- Plataforma web Next.js y API FastAPI con PostgreSQL, autenticación JWT/refresh,
  roles de ADMIN, empresa y administrador de contrato, y aislamiento multiempresa.
- Portal de empresa para gestionar contratos, personal, equipos, documentos,
  requisitos, alertas, calendario, reportes, cuentas asociadas y responsables
  de contrato. `/gestion-cuentas` administra roles y estados de cuentas del
    tenant. El panel de responsables permite asignar cuentas `company` y
    `contract_admin`; una cuenta `company` pasa a alcance de contrato con
    confirmación doble y siempre debe quedar otro `company` activo.
- Consola ADMIN bajo `/admin` para empresas, buscador global, métricas, usuarios,
  auditoría, sistemas, procesos e incidentes. La API administrativa actual usa
  `/api/v1/admin`; mantiene rutas Ops anteriores por compatibilidad.
- El buscador global permite combinar términos parciales de distintos campos
  del mismo resultado y su empresa relacionada. Su explorador permite activar
  o quitar referencias de empresas, cargos, contratos, tipos y marcas de
  equipos desde chips en la barra. La ficha de un resultado se expande debajo
  de su fila; solo queda una abierta y se descartan respuestas tardías al
  cambiar la búsqueda o selección.
- El registro solicita el nombre del usuario inicial, separado de la razón
    social. «Mi perfil» permite editar el nombre sin contraseña; para cambiar
    correo exige contraseña actual y confirmación de un enlace de un solo uso,
    con token hasheado y vencimiento. Si SMTP no está disponible, el correo no
    cambia. El cambio de contraseña es un flujo separado. El perfil está
    disponible en el portal (`/perfil`) y en la consola interna ADMIN
    (`/admin/perfil`), ambos usando `/auth/me`. Al usar «Ver como empresa»,
    ADMIN conserva su identidad administrativa, pero la vista de empresa muestra
    el perfil de esa empresa (nombre y correo editables; RUT y estado solo lectura),
    no el perfil personal. También puede gestionar responsables de contrato en
    el contexto seleccionado. La invitación/aceptación de cuentas existentes
    sigue pendiente.
- RF-MET-02 implementa telemetría real de tiempo activo: sesión autenticada,
  pestaña visible e interacción reciente, pausa tras cinco minutos inactivo y
  heartbeat cada 60 segundos bajo esas condiciones. Registra sesiones lógicas
  y agregados diarios, no cada ping; la retención identificable es de 90 días
  y la agregada de 12 meses conforme a DEC-08. DEC-05 define los períodos,
  minutos por usuario único y suma de sesiones simultáneas. Las 28 pruebas
  focalizadas y el build frontend pasaron; quedan la revisión visual específica
  y la aplicación de la migración en el entorno destino. La duración promedio
  estimada por sesión se retiró de la interfaz.
- **DEC-08 acordada el 09-11-2026 como política interna:** guardar solo
  metadatos de auditoría necesarios, excluir secretos y contenido documental,
  limitar auditoría a ADMIN autorizado y auditar sus consultas. Retención:
  auditoría 12 meses, logs técnicos 90 días, telemetría identificable 90 días
  y métricas agregadas no identificables 12 meses. Aplicar hacia adelante y
  revisar históricos antes de producción. La migración 16 implementa la poda
  prospectiva de base de datos. El job se reporta ejecutado localmente `ok` con
  cero filas podadas; faltan evidencia de Log Analytics, revisión histórica y
  aprobación de aplicabilidad por producción. No constituye aprobación legal.
- **Bloqueo P0 de producción con datos reales:** verificar que la política
  aplica al entorno/contrato, acreditar retención operativa y documentar el
  tratamiento de históricos en `documentacion/VALIDACION_ACTUAL.md`.
- DEC-10 exige autorización por contrato en la API y credenciales PostgreSQL
  de mínimo privilegio. El usuario confirmó en el entorno destino roles
  separados, RLS efectivo con roles reales, denegaciones y secretos externos.
  RLS contractual sigue condicionado a DEC-10: no se adoptó o, si se adoptó,
  sus pruebas SQL directas fueron validadas. El Compose local de desarrollo
  sigue usando un rol elevado.
- DEC-01/02 acuerdan operaciones ADMIN ordinarias y agregadas, acceso sensible
  temporal y auditado, protección del último ADMIN activo, y un buscador de
  cinco categorías que excluye administradores de plataforma y usuarios sin
  empresa y no muestra documentos en las fichas. Los controles de búsqueda y
  concesión cuentan con validación focalizada; las matrices completas de
  capacidades y lecturas sensibles restantes siguen pendientes.
- DEC-03 separa solicitudes registradas (embudo), empresas aprobadas (adopción)
  y clientes activos (empresa aprobada con suscripción activa/trial); también
  distingue cuentas habilitadas de usuarios con actividad. Cada métrica debe
  exponer definición, período, universo, denominador cuando aplique y zona
  horaria. DAU/WAU cuenta usuarios únicos de empresas con actividad humana,
  excluye ADMIN de plataforma y eventos automáticos, y usa America/Santiago.
  `past_due` se muestra aparte como pago atrasado y otros estados no activos/
  trial como «otro estado/no activo»; ninguno cuenta como cliente activo. MRR
  y crecimiento comercial quedan en Métricas SaaS. La aplicación y validación
  de los cálculos sigue pendiente.
- DEC-05 define la métrica de tiempo activo como minutos medidos por usuarios
  únicos, con período seleccionable de día, últimos 7 días, últimos 30 días o
  mes calendario, en límites inclusivos de días calendario en
  `America/Santiago`. Los minutos de sesiones simultáneas se suman aunque
  excedan el tiempo de reloj. La implementación está probada; la revisión
  visual específica de la tarjeta y la validación del entorno destino siguen
  pendientes según el SRS.
- DEC-04 acuerda umbrales iniciales revisables para alertas: acreditación bajo
  70%, al menos 3 documentos requeridos faltantes/vencidos en un contrato y
  30 días sin actividad humana registrada para empresas aprobadas con usuarios
  habilitados. Los casos sin usuarios o sin datos evaluables se distinguen;
  implementar y probar estos criterios sigue pendiente.
- DEC-11 precisa que las exportaciones ADMIN pueden incluir datos estructurados
  de una empresa, contrato, persona o equipo, junto con archivos documentales
  asociados. Se acordó ZIP con CSV y documentos por carpetas, relaciones
  incluidas por defecto con opción de desmarcar, motivo obligatorio y descarga
  inmediata sin conservar el ZIP tras la transferencia. No hay topes funcionales
  de filas ni tamaño: se intenta incluir todo el alcance autorizado. Si falla,
  se cancela la exportación completa, se elimina el paquete incompleto y se
  informa el error, sin reintento automático; el actor puede iniciar otro
  intento. Habrá un CSV por tipo de entidad en `/datos` y documentos bajo
  `/archivos/<tipo>/<id>/`, con nombres saneados y ruta referenciada en el CSV.
  Debe excluir secretos y respetar autorización/auditoría por recurso; falta
  validar viabilidad ante volúmenes grandes.
- **Estado actual de exportación ADMIN:** el ZIP genera CSV y JSON de las tablas
  administrativas permitidas, más `manifest.json`; no incluye archivos ni
  documentos y no implementa aún la selección por persona/contrato ni el
  paquete documental de DEC-11. En `/ops/respaldos` puede elegirse alcance
  global o una empresa. El ZIP crea una autoconcesión de exportación por una
  hora, registra el motivo, filtra los datos por empresa cuando corresponde y
  solicita revocarla al finalizar la descarga. El usuario confirmó manualmente
  que las exportaciones global y por empresa funcionan y quedan auditadas. El
  PDF sigue siendo global y agregado. Las pruebas focalizadas y el build pasaron.
- DEC-12 reemplaza la eliminación ordinaria de contratos por estados separados
  de desactivación temporal y finalización. Ambos se conservan en histórico de
  solo lectura, se excluyen de totales/alertas operacionales y no generan
  nuevas notificaciones. Las fechas continúan corriendo; al restaurar se
  recalcula el estado actual y se emiten solo avisos vigentes, sin reproducir
  individualmente notificaciones atrasadas. `company` gestiona contratos
  propios, ADMIN globalmente y `contract_admin` solo consulta el histórico en
  su alcance; cada transición exige motivo. Implementación y validación
  pendientes.
  Exportar datos no sustituye respaldar y restaurar el sistema.
- DEC-13 registra como propuesta pendiente de aprobación del cliente una
  solicitud justificada para vincular una cuenta existente a otra empresa.
  Primero acepta la persona titular y luego ADMIN revisa y decide; ambas etapas
  deben completarse dentro de los 14 días desde el envío. Rechazo o expiración
  no cambian membresía ni permisos. La alternativa recomendada es transferir:
  retirar el acceso de origen y asignar expresamente los permisos de destino,
  sin heredar contratos. Sigue pendiente de aprobación del cliente; el esquema
  actual solo admite un `company_id` y un `contrato_id` por cuenta.
- El flujo normal de registro de empresa queda pendiente de autorización
  ADMIN; al aprobarlo, la empresa y el usuario inicial quedan aprobados y el
  usuario conserva el rol `company`. La verificación manual cubrió la
  aprobación; rechazo y transiciones repetidas requieren validación separada.
- El esquema requerido por este corte de API es v20. La migración v9 incorporó
  invalidación de sesiones al cambiar el estado de acceso; la validación de
  seguridad de conexiones de producción no configura por sí sola los roles
  reales de la base de datos. Las migraciones 18, 19 y 20 añaden confirmación
  de cambio de correo, progreso de procesos y telemetría de actividad.

### Validación y límites conocidos

- La primera suite backend completa registrada en este corte obtuvo **363
  aprobadas y 0 fallidas** el 01-10-2026; cortes posteriores constan en el
  [historial de regresión](#historial-de-regresion-backend). Las pruebas de
  autenticación relacionadas con registro y perfil registraron 34/34.
- El build frontend con la ruta `/perfil` compiló, verificó tipos y generó
  **23 rutas**. La ficha expandible del buscador se documentó mediante revisión
  de código; no se registró para ese cambio una prueba automatizada ni un
  recorrido visual específico de navegador.
- El Compose local y su configuración de ngrok son para demostración, no para
  producción. El usuario confirmó roles separados y RLS efectivo en el entorno
  destino; el Compose local aún usa superusuario y no prueba ese entorno.
  Storage/correo reales y la matriz completa de aislamiento y permisos siguen
  pendientes. Consultar
  [la guía de ngrok](documentacion/LANZAMIENTO_NGROK.md) para una exposición
  temporal.
- La invitación completa de usuarios por correo, la recuperación productiva de
  contraseña, algunas integraciones externas y Celery distribuido siguen pendientes.
- El ciclo local cifrado de respaldos y restauración está cerrado: crear,
  descargar `.acb`, eliminar, importar, verificar y restaurar. RPO/RTO,
  recuperación ante pérdida total y almacenamiento externo siguen pendientes.
- El borrado actual de contratos es destructivo y elimina información asociada;
  el archivo y la restauración de contratos todavía no están implementados.
