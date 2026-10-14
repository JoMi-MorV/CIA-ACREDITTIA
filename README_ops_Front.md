# Consola Interna — frontend (/ops)

Documento de la implementación original de la consola de administración en
**React (Next.js 14 App Router + TypeScript + Tailwind)**. La consola ya está
integrada en el frontend de Acredittia: las rutas visibles actuales están bajo
`/admin` (por ejemplo, `/admin/usuarios`, `/admin/sistemas` y
`/admin/metricas`) y la API administrativa se publica bajo
`/api/v1/admin`. Se conservan rutas Ops anteriores bajo
`/api/v1/admin/ops` por compatibilidad.

Los nombres internos `app/ops`, `lib/ops` y las referencias a `/ops` de esta
guía corresponden a la estructura heredada; no describen la navegación pública
actual. Para el mapa de rutas, el arranque y las validaciones vigentes, consulta
el [README principal](README.md), el [SRS](documentacion/SRS.md) y
`documentacion/VALIDACION_ACTUAL.md`.

La especificación original contemplaba las vistas de usuarios, sistemas e
indicadores, con:

* **Autenticación JWT** — login contra `/api/v1/auth/login`; solo `role=admin`
  entra. El access token (30 min) vive **en memoria**; el refresh token
  persiste en `localStorage` y se canjea silenciosamente en cada 401 o tras un
  reload. Logout revoca el refresh en el servidor.
* **Marca Acredittia** — logo de montaña cobre (data URI, sin assets) y la
  paleta azul de la web oficial (#3D62F5/#2448E0) con acentos cobre; barra
  lateral navy en ambos temas como ancla de marca.
* **Modo claro y oscuro** — conmutador en la barra superior; sigue
  `prefers-color-scheme` hasta que el usuario elige, y persiste en
  `localStorage`. Todo el color vive en variables CSS (`ops.css`), así que los
  SVG de los gráficos se retematizan sin re-render.
* **Multidioma es / en / pt** — diccionarios en `lib/ops/i18n.tsx`, selector
  persistente, formatos de número y fecha con `Intl` (es-CL / en-US / pt-BR).
  Español es el idioma por defecto; el del navegador se respeta si es uno de
  los tres.
* **Gráficos SVG propios** (cero dependencias): línea con crosshair y tooltip,
  barras apiladas y agrupadas, tiras de disponibilidad, sparkline.
* **Modo demo** — `NEXT_PUBLIC_OPS_MOCK=1` sirve datos ficticios coherentes con
  el wireframe (incluidas las mutaciones: ejecutar/pausar procesos y resolver
  incidentes actualizan el estado en memoria). Sin esa variable, todo va a la
  API real.

## Mapa de archivos (rutas relativas a `app/frontend/`)

| Archivo | Contenido |
|---|---|
| `app/ops/layout.tsx` | Providers (tema, i18n), guardia de sesión admin, sidebar y topbar |
| `app/ops/ops.css` | Tokens de marca claro/oscuro y clases base de la consola |
| `app/ops/page.tsx` | Redirección de la ruta histórica `/ops` → `/admin/dashboard` |
| `app/ops/login/page.tsx` | Login JWT (solo admin) |
| `app/ops/salud/page.tsx` | Salud de clientes: uso/adopción, usuarios por plan/industria y riesgos desplegables con ayudas informativas |
| `app/ops/accesos/page.tsx` | Vista Usuarios: roles, empresa/contrato, revocación/reactivación y cambios confirmados con motivo |
| `app/ops/sistemas/page.tsx` | Vista Sistemas: banner, componentes, uptime 90d, incidentes (resolver), procesos (ejecutar/pausar) |
| `app/ops/indicadores/page.tsx` | Vista Indicadores: KPIs confidenciales, MRR 6/12/24M, flujo, churn vs. objetivo, desglose por plan |
| `lib/ops/auth.ts` | Sesión JWT (access en memoria + refresh en localStorage) |
| `lib/ops/api.ts` | Cliente HTTP de /admin/ops con refresh transparente en 401 |
| `lib/ops/mock.ts` | Modo demo: datos y mutaciones en memoria |
| `lib/ops/i18n.tsx` | Diccionarios es/en/pt + formatos Intl |
| `lib/ops/theme.tsx` | Tema claro/oscuro/system con persistencia |
| `components/ops/ui.tsx` | Card, KPI, pills, segmented, modal, toggles, hook useOps |
| `components/ops/charts.tsx` | Gráficos SVG (línea+crosshair, barras, uptime, sparkline) |
| `components/ops/logo.ts` | Logo Acredittia como data URI |

## Instalación (2 ediciones pequeñas)

1. **Copiar** los archivos según la tabla (respetando las rutas).

2. **`tailwind.config.ts`** — habilitar el modo oscuro por clase:

   ```ts
   const config: Config = {
     darkMode: ["class"],          // <- línea nueva
     content: [...],
   };
   ```

3. **`.env.local` en la implementación original**:

   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000   # ya existente
   NEXT_PUBLIC_OPS_MOCK=1                      # quitar para usar la API real
   ```

Estas instrucciones describen el montaje original de la consola, no una
instalación independiente de la versión integrada actual. Para ejecutar el
proyecto vigente, sigue las instrucciones del [README principal](README.md).
No se debe asumir que `/ops` es una ruta pública disponible.
En modo demo el login acepta `admin@acredittia.cl` con cualquier contraseña.

## Notas de diseño que conviene conocer

* La consola es un route group **independiente del portal** (`/ops` no usa el
  Sidebar ni la sesión de `lib/api.ts`): las claves de almacenamiento son
  propias (`ops_refresh`, `ops_user`, `ops_theme`, `ops_lang`) y no chocan con
  las del portal en el mismo navegador.
* La guardia del layout hace el canje refresh→access **antes** de renderizar
  las vistas; si el refresh no es válido o el rol no es admin, siempre termina
  en `/ops/login`.
* Los umbrales visuales (colores de estado, pills) son los mismos del
  wireframe aprobado; la paleta categórica azul/cobre/teal/violeta está
  validada para daltonismo en ambos temas.
* Backend requerido en la implementación original: módulo
  `codigo_administracion`. Actualmente las rutas principales están integradas
  bajo `/api/v1/admin`; las rutas `/api/v1/admin/ops/*` se conservan para
  compatibilidad. Cualquier discrepancia de contrato aparece como mensaje de
  error del backend en la tarjeta correspondiente (formato
  `{error:{code,message}}`).
