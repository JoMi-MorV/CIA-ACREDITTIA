# Consola Interna — frontend (/ops)

La última validación del frontend fue el build de producción del 03-11-2026,
que pasó. La suite backend completa registró históricamente **399 pruebas
aprobadas, 0 fallidas** el 14-10-2026; no se volvió a ejecutar en el corte más
reciente. El 03-11-2026 se aprobaron cinco regresiones focalizadas de salud
operacional. No se declara producción ni go-live con datos reales: DEC-08 y
otras brechas de seguridad siguen abiertas. La evidencia actualizada y sus
límites están en `documentacion/VALIDACION_ACTUAL.md`.

Este documento conserva la implementación original de la consola de administración en **React (Next.js 14 App Router + TypeScript + Tailwind)**, pero la navegación pública actual del proyecto ya no se limita a `/ops`. Las rutas visibles vigentes quedan bajo `/admin` (por ejemplo, `/admin/usuarios`, `/admin/sistemas`, `/admin/metricas`), y la API administrativa se publica bajo `/api/v1/admin`. Se conservan rutas Ops anteriores bajo `/api/v1/admin/ops` por compatibilidad histórica.

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
| `app/ops/perfil/page.tsx` | Perfil personal de ADMIN: nombre, correo, contraseña y validación de la sesión actual |
| `lib/ops/auth.ts` | Sesión JWT compartida con el portal (access en memoria + refresh en localStorage) |
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
No se debe asumir que `/ops` es una ruta pública disponible; las rutas visibles
se sirven bajo `/admin` mediante rewrites de Next.js. La consola incluye
`/admin/perfil` para que el ADMIN gestione los datos personales y la contraseña
de su propia cuenta mediante `GET/PATCH /api/v1/auth/me`. Esta ruta es
independiente del perfil de empresa mostrado durante la impersonación.
En modo demo el login acepta `admin@acredittia.cl` con cualquier contraseña.

## Notas de diseño que conviene conocer

* La consola integrada comparte la sesión del portal: utiliza las claves
  `acredittia_token`, `acredittia_refresh` y `acredittia_user` de `lib/api.ts`.
  Mantiene su propio tema y idioma, pero no establece una segunda identidad de
  usuario ni un segundo flujo de login.
* La guardia del layout hace el canje refresh→access **antes** de renderizar
  las vistas; si el refresh no es válido o el rol no es admin, siempre termina
  en `/login`. Las rutas públicas usan `/admin` y los archivos internos viven
  bajo `/ops`, resueltos mediante rewrites de Next.js.
* Los umbrales visuales (colores de estado, pills) son los mismos del
  wireframe aprobado; la paleta categórica azul/cobre/teal/violeta está
  validada para daltonismo en ambos temas.
* Backend requerido en la implementación original: módulo
  `codigo_administracion`. Actualmente las rutas principales están integradas
  bajo `/api/v1/admin`; las rutas `/api/v1/admin/ops/*` se conservan para
  compatibilidad. Cualquier discrepancia de contrato aparece como mensaje de
  error del backend en la tarjeta correspondiente (formato
  `{error:{code,message}}`).
