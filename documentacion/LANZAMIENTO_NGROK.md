# Configurar y lanzar la demo con ngrok

Guía para publicar temporalmente la aplicación web mediante ngrok desde
Windows. El túnel publica solo el frontend y no añade un segundo diálogo de
usuario/contraseña; el inicio de sesión propio de Acredittia sigue activo. Este
procedimiento es para una **demo con datos sintéticos**, no para producción.

> **Seguridad:** un token de ngrok fue compartido en el chat. Revócalo desde el
> dashboard oficial de ngrok y crea uno nuevo antes de continuar. No pegues
> tokens, contraseñas ni secretos en el chat, en este documento o en archivos
> versionados. El `.env` local está excluido de Git.

## 1. Requisitos

- Docker Desktop instalado y en ejecución.
- Cuenta de ngrok con el dominio reservado
  `unequal-unsolved-twitch.ngrok-free.dev`.
- Un token ngrok nuevo, creado después de revocar el anterior.
- PowerShell.

El Compose base usa servicios y credenciales de desarrollo, incluyendo cuentas
demo conocidas y datos de semilla. No introduzcas información real de empresas,
personas, documentos ni credenciales.

## 2. Abrir la carpeta de la aplicación

Abre PowerShell y sitúate en la carpeta `BASE\app` del repositorio:

```powershell
Set-Location "C:\Users\Amaru\Desktop\ultima acredittia\CIA-ACREDITTIA-main\BASE\app"
```

Comprueba que están los archivos:

```powershell
Get-ChildItem docker-compose.yml, docker-compose.ngrok.yml, .env.example
```

Si el repositorio está en otra ubicación, reemplaza la ruta por la ubicación
real.

## 3. Crear el archivo local `.env`

Si todavía no existe:

```powershell
Copy-Item .env.example .env
```

Abre `.env` en VS Code:

```powershell
code .env
```

Completa los valores **localmente**:

```dotenv
NGROK_AUTHTOKEN=PEGA_AQUI_EL_TOKEN_NUEVO
NGROK_DOMAIN=unequal-unsolved-twitch.ngrok-free.dev
JWT_SECRET=REEMPLAZAR_POR_SECRETO_ALEATORIO_DE_32_BYTES_O_MAS
```

Indicaciones:

- `NGROK_AUTHTOKEN`: token nuevo del dashboard de ngrok; no reutilices el
  compartido en el chat.
- `NGROK_DOMAIN`: debe coincidir exactamente con el dominio reservado en la
  cuenta de ngrok.
- `JWT_SECRET`: secreto aleatorio único de al menos 32 bytes. No uses el token
  ngrok como secreto JWT ni una contraseña de usuario.

### Generar los secretos aleatorios en PowerShell

En una ventana local de PowerShell, genera un secreto JWT con 32 bytes
criptográficamente aleatorios codificados en Base64:

```powershell
$bytes = New-Object byte[] 32
$rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $rng.GetBytes($bytes)
    [Convert]::ToBase64String($bytes)
}
finally {
    $rng.Dispose()
}
```

Copia el valor que imprime PowerShell en `JWT_SECRET` dentro de `.env`. Cada
ejecución genera un secreto distinto. No lo uses como contraseña de ngrok ni lo
compartas. Si se pierde, genera otro; las sesiones firmadas con el secreto
anterior dejarán de ser válidas.

No se configura Basic Auth de ngrok en este perfil. Por lo tanto, cualquier
persona que conozca la URL puede llegar a la pantalla de login de Acredittia.
El login de la aplicación continúa siendo obligatorio para acceder a funciones
autenticadas, pero la URL no tiene una segunda contraseña delante.

Guarda el archivo y confirma que no está versionado:

```powershell
git check-ignore .env
```

El comando debe mostrar `.env` o `BASE/app/.env`. No ejecutes comandos que
impriman el contenido completo del archivo en una consola compartida ni lo
envíes por chat.

## 4. Validar la configuración

Desde `BASE\app`, ejecuta:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml config --quiet
```

Si Compose informa que falta alguna variable, vuelve al paso 3 y verifica que
guardaste `.env` en `BASE\app` y que cada variable tiene un valor.

## 5. Construir e iniciar servicios y túnel

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml up --build -d
```

Revisa el estado:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml ps
```

Consulta los registros del túnel si algún servicio no inicia:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs --tail 100 ngrok
```

Para seguir los registros mientras inicia:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs -f ngrok
```

Usa `Ctrl+C` para salir del seguimiento de logs; esto no detiene los
contenedores.

## 6. Probar el acceso

Abre en el navegador:

```text
https://unequal-unsolved-twitch.ngrok-free.dev
```

La URL debe abrir la aplicación sin el diálogo adicional de credenciales de
ngrok. Luego ingresa desde la pantalla de login de Acredittia. La URL será
pública para quien la conozca; no compartas datos reales y no publiques ni
distribuyas cuentas demo conocidas.

El túnel dirige tráfico al frontend (`web:3000`). La aplicación usa el proxy
del frontend para las rutas de API. PostgreSQL no publica un puerto al host;
Redis, API, frontend e inspector local de ngrok quedan ligados a `127.0.0.1`.
PostgreSQL sigue disponible para los otros contenedores en la red interna de
Compose.

Si necesitas conectar una herramienta local directamente a PostgreSQL durante
desarrollo, configura temporalmente una publicación local en `docker-compose.yml`
con un puerto de host libre y limitado a `127.0.0.1`; no publiques la base de
datos en todas las interfaces para el túnel ngrok.

## 7. Detener la demo

Al terminar, desde `BASE\app`:

```powershell
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml down
```

Esto detiene los contenedores y el túnel, pero conserva los volúmenes locales.
No añadas `-v` si deseas conservar la base de datos y archivos de demo.

## 8. Incidentes y límites

- Si el token se comparte o aparece en registros/capturas, revócalo y crea otro
  en ngrok; actualiza `.env` antes de volver a iniciar.
- Al quitar Basic Auth, el endpoint del túnel queda accesible públicamente. Si
  necesitas restringir quién puede siquiera llegar al login, vuelve a activar
  una protección en ngrok o limita el acceso desde el panel de ngrok antes de
  compartir el enlace.
- La autenticación propia de Acredittia y Basic Auth del túnel son controles
  distintos. El Compose de demo usa configuración de desarrollo y cuentas
  semilla conocidas; no alojes datos reales.
- Para producción se requiere una configuración distinta: roles de base de
  datos con mínimo privilegio y RLS efectivo, secretos gestionados fuera del
  repositorio, almacenamiento privado, configuración de correo/recuperación,
  migraciones separadas y pruebas de seguridad/aislamiento. Consulta
  [DESPLIEGUE_AZURE.md](../BASE/app/backend/DESPLIEGUE_AZURE.md).
