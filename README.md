# Consola Interna de Administración — código backend

Tenemos la carpeta BASE donde esta el código de la plataforma base que nos paso la empresa.
Y esta la carpeta codigo_adminitracion con lo que quieren que sea desarrollado. 

## Implementación de la Especificación de API — Consola Interna v1.0
(Acredittia_Especificacion_API_Consola_Interna.docx): 20 endpoints bajo
/api/v1/admin/ops, 7 tablas nuevas, procedimientos almacenados PL/pgSQL,
índices y 4 jobs de fondo. Módulo drop-in para app/backend.
Cambios y Versión Actual (Esquema v7)

    Base de datos: Se han incorporado los scripts de migración de la consola interna (07_consola_interna.sql y 08_funciones_consola.sql), estableciendo el esquema en Versión 7. Esto incluye las tablas ops_*, métricas mensuales, triggers, índices, RLS de solo-admin y funciones PL/pgSQL de agregación (MRR, churn, estado de cuenta).

    Backend (app/backend):

        Integración del router admin_ops bajo el prefijo de la API (/api/v1/admin/ops).

        Configuración de tareas de fondo en Celery (worker/ops_tasks.py) para los jobs de monitoreo, métricas y heartbeats.

        Incorporación de las 6 sondas de salud (db, api, workers, storage, ia, integraciones) y detección automática de incidentes.

## Ejecutar en local

Requisitos: Docker Desktop.
Bash

cd app
docker compose up --build

## ⚠️ Problemas Encontrados y Notas de Configuración

    Actualización de versión esperada (config.py): Durante la puesta en marcha, la API fallaba al iniciar con un error de validación de esquema ("Esquema en versión 7, se esperaba 6"). Esto ocurría porque en la guía de instalación original no se especificaba que en el archivo config.py era necesario actualizar explícitamente el dígito de la variable de configuración de 6 a 7:
    Python

    schema_version_esperada: int = 7  # <-- Debe actualizarse a 7 tras aplicar los scripts
=======
# CIA-ACREDITTIA
Desarrollo de la consola interna de administración de la plataforma Acredittia
