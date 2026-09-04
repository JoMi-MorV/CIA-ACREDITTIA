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
Se a poblado con 3 empresas más.
Se poblo los datos sobre los planes de negocio para visualizar que empresas tiene que plan
Se corrigio `ops_tasks.py` para castear el valor UF de `double precision` a `numeric` antes de llamar a `ops_snapshot_metricas`, evitando el error de PostgreSQL al cargar los indicadores.
