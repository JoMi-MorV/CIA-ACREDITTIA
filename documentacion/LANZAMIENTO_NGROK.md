# Configurar y lanzar Acredittia con ngrok

Guía para levantar la aplicación y exponer temporalmente el frontend mediante
ngrok en **Windows PowerShell** o **Linux**. Los dos procedimientos usan
Docker Compose y los mismos servicios. El túnel expone el frontend; Next.js
redirige las llamadas de API por la red interna de Compose.

Este procedimiento es exclusivamente para una **demo con datos sintéticos**.
No lo uses para producción ni cargues información real de empresas, personas,
documentos o credenciales.

> **Seguridad:** un token de ngrok fue compartido anteriormente. Revócalo en
> el dashboard oficial de ngrok y genera uno nuevo antes de continuar. Nunca
> pegues tokens, contraseñas o secretos en el chat ni los guardes en archivos
> versionados. El archivo `.env` está excluido de Git.

## 1. Requisitos

- Docker funcionando:
  - **Windows:** Docker Desktop iniciado.
  - **Linux:** Docker Engine y el plugin Docker Compose instalados; el usuario
    debe tener permiso para ejecutar `docker`.
- Cuenta de ngrok con el dominio reservado
  `unequal-unsolved-twitch.ngrok-free.dev`.
- Un token ngrok nuevo.
- Editor de texto para modificar `.env`.

El Compose de demostración utiliza configuración de desarrollo, cuentas y
semillas conocidas. La URL del túnel es pública para quien la conozca; el login
de Acredittia sigue activo, pero ngrok no agrega Basic Auth ni otro diálogo de
credenciales.

## 2. Abrir la carpeta `BASE/app`

Sitúate en `BASE/app`, que contiene `docker-compose.yml`,
`docker-compose.ngrok.yml` y `.env.example`.

### Windows PowerShell

Abre PowerShell y usa la ruta real del repositorio:

```powershell
Set-Location "C:\Users\Amaru\Desktop\ultima acredittia\CIA-ACREDITTIA-main\BASE\app"
Get-ChildItem docker-compose.yml, docker-compose.ngrok.yml, .env.example
```

Si el repositorio está en otra ubicación, cambia la ruta de `Set-Location`.

### Linux

Desde la terminal, usa la ruta donde clonaste el repositorio:

```bash
cd "/ruta/al/repositorio/BASE/app"
ls docker-compose.yml docker-compose.ngrok.yml .env.example
```

Por ejemplo, si lo clonaste en tu carpeta de usuario:

```bash
cd "$HOME/CIA-ACREDITTIA-main/BASE/app"
```

Los pasos siguientes deben ejecutarse desde esta carpeta en ambos sistemas.

## 3. Crear y completar `.env`

Si `.env` aún no existe, copia la plantilla. Si ya existe, **no la sobrescribas**:
podrías borrar la configuración local.

### Windows PowerShell

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

También puedes abrirla en VS Code con `code .env`.

### Linux

```bash
if [ ! -f .env ]; then cp .env.example .env; fi
nano .env
```

Puedes reemplazar `nano` por tu editor de texto preferido.

Completa localmente estas tres variables:

```dotenv
NGROK_AUTHTOKEN=PEGA_AQUI_EL_TOKEN_NUEVO
NGROK_DOMAIN=unequal-unsolved-twitch.ngrok-free.dev
JWT_SECRET=PEGA_AQUI_UN_SECRETO_ALEATORIO
```

- `NGROK_AUTHTOKEN`: token nuevo de tu cuenta ngrok; no reutilices el que se
  compartió anteriormente.
- `NGROK_DOMAIN`: debe coincidir exactamente con el dominio reservado en ngrok.
- `JWT_SECRET`: secreto aleatorio propio de al menos 32 bytes. No uses el token
  ngrok, una contraseña de usuario ni el valor de ejemplo de la plantilla.

### Generar `JWT_SECRET` en Windows PowerShell

Ejecuta el bloque localmente. Imprime un secreto Base64 generado con 32 bytes
criptográficamente aleatorios:

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

Copia el resultado en `JWT_SECRET` dentro de `.env`. Si reemplazas este secreto
después de iniciar la aplicación, las sesiones existentes dejarán de ser
válidas.

### Generar `JWT_SECRET` en Linux

Con OpenSSL instalado:

```bash
openssl rand -base64 32
```

Copia el resultado en `JWT_SECRET` dentro de `.env`. No guardes el secreto en
este documento ni lo incluyas en comandos que vayas a compartir o publicar.

Guarda `.env` y comprueba que Git lo ignora. No imprimas el contenido del
archivo:

```text
Windows PowerShell: git check-ignore .env
Linux:              git check-ignore .env
```

El comando debe indicar que `.env` está ignorado. Si no lo está, detente y
comprueba `.gitignore` antes de continuar.

## 4. Validar y construir

Ejecuta desde `BASE/app`; los comandos Compose son iguales en Windows y Linux:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml config --quiet
```

Si Compose indica que falta `NGROK_AUTHTOKEN`, `NGROK_DOMAIN` o `JWT_SECRET`,
revisa que guardaste `.env` en `BASE/app` y que completaste cada variable.
No compartas la salida de comandos que pudiera incluir secretos.

Construye y levanta los servicios en segundo plano:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml up --build -d
```

Para construir y levantar los servicios en primer plano, dejando visibles en
esa terminal los mensajes de inicio de la migración, la API, el frontend y
ngrok, usa este comando en lugar del anterior:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml up --build
```

Espera a que los servicios indiquen que están listos y revisa especialmente
los mensajes de `migrate`, `api` y `ngrok`. Mantén abierta la terminal para
seguir viendo los registros. Al pulsar `Ctrl+C`, Compose detendrá los servicios;
para iniciarlos nuevamente en segundo plano, usa el comando con `-d`.

Revisa el estado:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml ps
```

Consulta los registros de ngrok y de los servicios si no arrancan:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs --tail 100 ngrok
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs --tail 100 web api migrate
```

Para seguir en tiempo real el registro de ngrok:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml logs -f ngrok
```

Pulsa `Ctrl+C` para dejar de seguir los registros; como los servicios se
iniciaron con `-d`, esto no los detiene.

## 5. Abrir y probar la aplicación

Abre en el navegador:

```text
https://unequal-unsolved-twitch.ngrok-free.dev
```

Debe aparecer el login de Acredittia, sin un segundo diálogo de autenticación
de ngrok. Inicia sesión con una cuenta válida configurada para tu entorno demo.
No compartas cuentas demo conocidas.

El servicio ngrok publica `web:3000`. Las llamadas de API se encaminan dentro
de Compose; PostgreSQL no publica un puerto al host. Redis, API y el inspector
local de ngrok están enlazados a `127.0.0.1` para limitar su acceso desde la
máquina local.

## 6. Detener la demo

Desde `BASE/app`, tanto en PowerShell como en Linux:

```bash
docker compose -f docker-compose.yml -f docker-compose.ngrok.yml down
```

Esto detiene los servicios y el túnel, pero conserva los volúmenes de base de
datos y archivos. No añadas `-v` si deseas conservar los datos de demostración.

## 7. Incidentes y límites

- Si el token se comparte o aparece en registros/capturas, revócalo en ngrok,
  crea uno nuevo y actualiza `.env`.
- Cualquier persona que conozca el enlace puede llegar al login de Acredittia.
  Si necesitas impedir incluso el acceso a esa pantalla, configura una
  protección en ngrok o limita el acceso desde su panel antes de compartir el
  enlace.
- No uses datos reales: el Compose base usa configuración de desarrollo,
  semillas y cuentas demo conocidas.
- Esta guía no configura un despliegue productivo. Producción requiere
  identidades de base de datos con mínimo privilegio y RLS efectivo, secretos
  gestionados fuera del repositorio, almacenamiento privado, correo y
  recuperación configurados, migraciones separadas y pruebas de seguridad e
  aislamiento. Consulta
  [DESPLIEGUE_AZURE.md](../BASE/app/backend/DESPLIEGUE_AZURE.md).
