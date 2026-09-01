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

## ⚠️ Problemas Encontrados y Notas de Configuración

    Actualización de versión esperada (config.py): Durante la puesta en marcha, la API fallaba al iniciar con un error de validación de esquema ("Esquema en versión 7, se esperaba 6"). Esto ocurría porque en la guía de instalación original no se especificaba que en el archivo config.py era necesario actualizar explícitamente el dígito de la variable de configuración de 6 a 7:
