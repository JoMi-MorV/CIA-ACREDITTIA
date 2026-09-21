# Consola Interna de Administración — código backend

Tenemos la carpeta BASE donde esta el código de la plataforma base que nos paso la empresa.
Y esta la carpeta codigo_adminitracion con lo que quieren que sea desarrollado. 

## Implementación de la Especificación de API — Consola Interna v1.0
(Acredittia_Especificacion_API_Consola_Interna.docx): 20 endpoints bajo
/api/v1/admin/ops, 2 tablas nuevas, procedimientos almacenados PL/pgSQL,
índices.

## Ejecutar en local

Requisitos: Docker Desktop.
Bash

cd app
docker compose up --build



## ⚠️ Problemas Encontrados y Notas de Configuración Backend

    Actualización de versión esperada (config.py): Durante la puesta en marcha, la API fallaba al iniciar con un error de validación de esquema ("Esquema en versión 7, se esperaba 6"). Esto ocurría porque en la guía de instalación original no se especificaba que en el archivo config.py era necesario actualizar explícitamente el dígito de la variable de configuración de 6 a 7:


### Cambios 01-09-2026
Se Instalo el fronted tal como se especifica en README_ops_Front
Se Instalo el backend tal como se especifica en README_ops_Back
Ambos con ajustes
Se dejo el Mock=0 (.env.local) y esta funcionando con la poblacion de datos actual que es 1.

### Cambios 04-09-2026
Poblacion de datos a traves de seeds.py para sistema y procesos.
Se poblaron 16 empresas demo con industrias, usuarios y antigüedades diferentes para
que los filtros y el resumen de clientes se parezcan a un entorno de producción.
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
