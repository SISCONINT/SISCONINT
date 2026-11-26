# Monitoreo de disponibilidad — Better Stack (Uptime)

Etapa **Monitor** del pipeline DevOps: monitoreo 24/7 de caída de servicios con alertas a Slack.

| Etapa | Herramienta | Responsabilidad |
| --- | --- | --- |
| Monitor (Disponibilidad) | Better Stack (Uptime) | Monitoreo 24/7 de caída de servicios y alertas a Slack |

## Qué se monitorea

Los monitores están definidos como código en [`monitoring/betterstack/monitors.json`](../monitoring/betterstack/monitors.json):

| Monitor | URL | Qué detecta |
| --- | --- | --- |
| SISCONINT Frontend (Netlify) | `${FRONTEND_URL}/` | El sitio de Netlify no responde o devuelve error. |
| SISCONINT Backend API y base de datos (Render) | `https://sisconint-backend.onrender.com/api/v1/health` | Render caído **o** PostgreSQL sin responder (el endpoint devuelve 503). |
| SISCONINT Proxy Netlify hacia API | `${FRONTEND_URL}/api/v1/health` | El redirect `/api/*` de `Frontend/netlify.toml` está roto o apunta mal, aunque los dos servicios estén arriba. |

Configuración común (bloque `defaults`):

- `check_frequency: 180` — cada 3 minutos, el mínimo del plan gratuito.
- `request_timeout: 60` — Render (plan free) tarda hasta ~50 s en despertar; con menos daría falsos positivos.
- `confirmation_period: 60` — Better Stack confirma desde otra región antes de abrir el incidente.
- `recovery_period: 180` — el servicio debe estar 3 min arriba para cerrar el incidente.
- Alertas por correo activas; SMS/llamada/push apagados (son de planes de pago).

> Efecto secundario útil: como Better Stack llama al backend cada 3 minutos, el servicio de Render no entra en suspensión por inactividad (las 750 h/mes del plan free alcanzan para un servicio encendido todo el mes).

### Endpoints de salud del backend

| Ruta | Uso |
| --- | --- |
| `GET /health` | *Liveness*: el proceso Flask responde. No toca la BD. Úsalo como **Health Check Path** en Render. |
| `GET /api/v1/health` | *Readiness*: hace `SELECT 1` en PostgreSQL. `200 {"status":"ok","database":"ok"}` o `503 {"status":"error","database":"down"}`. Es el que consulta Better Stack. |

Ninguno requiere sesión. Pruebas en `Backend/tests/test_health.py`.

## Puesta en marcha (una sola vez)

### 1. Cuenta y token

1. Crea una cuenta en <https://betterstack.com/uptime> (el plan gratuito incluye 10 monitores e integración con Slack).
2. Ve a **Settings → API tokens** y copia el token del equipo (*Uptime API token*).

### 2. Conectar Slack (desde el dashboard; no hay API para esto)

1. En Slack, crea el canal de alertas, por ejemplo `#sisconint-alertas`.
2. En Better Stack: **Integrations → Slack → Add** y autoriza el workspace, eligiendo ese canal.
3. En **On-call / Escalation policies**, revisa la política por defecto del equipo: debe notificar al equipo actual. Better Stack envía a Slack cada incidente (abierto, reconocido, resuelto), con botones para reconocerlo desde el mensaje.

### 3. Variables en GitHub

En el repositorio: **Settings → Secrets and variables → Actions**.

| Tipo | Nombre | Valor |
| --- | --- | --- |
| Secret | `BETTERSTACK_API_TOKEN` | El token del paso 1. |
| Variable | `FRONTEND_URL` | URL pública de Netlify, sin barra final (p. ej. `https://sisconint.netlify.app`). |
| Variable (opcional) | `BACKEND_URL` | Solo si cambia la URL de Render. |

### 4. Crear los monitores

En **Actions → Better Stack monitors → Run workflow**. La primera vez puedes marcar *dry run* para ver qué se va a crear.

Después, el workflow corre solo cuando se hace push a `main` que modifique `monitoring/betterstack/`; en un PR solo muestra los cambios (dry run).

También se puede correr localmente:

```powershell
$env:BETTERSTACK_API_TOKEN = "..."
$env:FRONTEND_URL = "https://sisconint.netlify.app"
python monitoring/betterstack/sync_monitors.py --dry-run
python monitoring/betterstack/sync_monitors.py
```

El script es idempotente: identifica cada monitor por su nombre, crea los que faltan y actualiza solo los campos distintos. **No borra** monitores; los que existan en Better Stack y no estén en el JSON se listan al final para que se eliminen a mano si ya no se usan.

### 5. Probar la alerta

1. En Better Stack, abre un monitor y usa **Send test alert**: debe llegar el mensaje al canal de Slack.
2. Opcional, prueba real: pausa el servicio en Render (*Suspend*), espera ~5 min y confirma que se abre el incidente y llega a Slack; reanúdalo y verifica el mensaje de resolución.

### 6. Render (recomendado)

En el servicio de Render: **Settings → Health Check Path = `/health`**. Así Render no da por buena una instancia nueva que no arranca.

## Cambiar o agregar monitores

Edita `monitoring/betterstack/monitors.json`. Cada objeto acepta cualquier campo de la API de Better Stack ([Create monitor](https://betterstack.com/docs/uptime/api/create-a-new-monitor/)); lo que no pongas se toma de `defaults`. `${VAR}` se reemplaza con variables de entorno.

> Si cambias `pronounceable_name`, el script lo trata como un monitor nuevo; borra el viejo a mano en el dashboard.

## Ideas para después

- **Heartbeat** para el comando `flask recordatorios-vencimiento` (HU_66): cuando se programe el cron diario, que haga `curl` a una URL de heartbeat de Better Stack al terminar; si un día no llega, se alerta a Slack.
- **Status page** pública (Better Stack → Status pages) con estos tres monitores.
- Alertas de vencimiento de SSL/dominio (`ssl_expiration`, `domain_expiration`) si el plan lo permite.
