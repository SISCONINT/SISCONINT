# Manual del Desarrollador — SISCONINT

**Sistema de Control Interno — Téllez Ponce & Asociados**

| Campo | Valor |
| --- | --- |
| Versión del documento | 1.0 |
| Última actualización | 19 de noviembre de 2026 |
| Audiencia | Desarrolladores, QA y DevOps del proyecto |
| Alcance | Backend Flask, frontend React, base de datos, pruebas, CI y generación de reportes PDF |

---

## Contenido

1. [Descripción general](#1-descripción-general)
2. [Stack tecnológico](#2-stack-tecnológico)
3. [Arquitectura](#3-arquitectura)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Requisitos previos](#5-requisitos-previos)
6. [Instalación y ejecución](#6-instalación-y-ejecución)
7. [Variables de entorno](#7-variables-de-entorno)
8. [Base de datos y comandos CLI](#8-base-de-datos-y-comandos-cli)
9. [Backend](#9-backend)
10. [Frontend](#10-frontend)
11. [Reportes ejecutivos en PDF](#11-reportes-ejecutivos-en-pdf)
12. [Pruebas](#12-pruebas)
13. [CI/CD y versionado](#13-cicd-y-versionado)
14. [Solución de problemas](#14-solución-de-problemas)
15. [Convenciones y checklist](#15-convenciones-y-checklist)
16. [Anexo: tablas de la base de datos](#16-anexo-tablas-de-la-base-de-datos)

---

## 1. Descripción general

SISCONINT es una aplicación web para la operación interna de un despacho contable. Cubre:

- **Colaboradores**: alta, edición, desactivación, activación por enlace y control de acceso por rol.
- **Clientes**: personas físicas y morales, contactos, régimen fiscal y permisos de atención.
- **Catálogo**: categorías de proyecto/servicio.
- **Tareas**: creación, asignación, subtareas, comentarios, tablero Kanban, semáforo de vencimiento y alertas.
- **Tiempo**: temporizador por tarea y captura manual de horas, con aprobación fuera de plazo.
- **Dashboard**: indicadores globales y dashboard personal.
- **Tarifas**: costo por hora según grado del escalafón.
- **Obligaciones**: calendario de obligaciones fiscales/legales.
- **Minutas**: registro y descarga de documentos (PDF/imagen) por cliente.
- **Plantillas de notificación**: correos editables.
- **Calendario**: consolidado de tareas y obligaciones.
- **Reportes ejecutivos**: resumen del periodo con exportación a PDF.
- **Notificaciones**: asignaciones, recordatorios de vencimiento y avisos internos.

La autenticación es **JWT transportado en cookies httpOnly** con protección CSRF de doble token. La autorización se resuelve en el backend mediante una matriz de permisos por rol; el frontend solo oculta opciones de UI y aplica guardas de navegación.

---

## 2. Stack tecnológico

### Backend

| Componente | Versión / tecnología |
| --- | --- |
| Lenguaje | Python 3.12 |
| Framework | Flask 3.0.3 |
| ORM | Flask-SQLAlchemy 3.1.1 (SQLAlchemy 2.x) |
| Base de datos | PostgreSQL (driver `psycopg2-binary`) |
| Autenticación | Flask-JWT-Extended 4.6.0 |
| Validación | Marshmallow 3.21.3 |
| Contraseñas | argon2-cffi (argon2id) |
| Correo | Flask-Mail 0.10.0 |
| Caché / blocklist | Redis 5 (opcional; fallback en memoria) |
| Servidor WSGI | Gunicorn 22 |
| Pruebas | pytest 8.2.2 |
| CORS | Flask-Cors 4.0.1 |

### Frontend

| Componente | Versión / tecnología |
| --- | --- |
| Framework | React 19 |
| Build tool | Vite 8 |
| Lenguaje | TypeScript 6 |
| Estilos | Tailwind CSS 4 (`@tailwindcss/vite`) |
| Routing | React Router 7 (`createBrowserRouter`) |
| Datos remotos | TanStack Query 5 |
| Estado global | Zustand 5 |
| HTTP | Axios 1.20 |
| Formularios | react-hook-form 7 + Zod 4 |
| Iconos | lucide-react |
| PDF | jsPDF 4 (gráficas vectoriales, sin capturas) |

### Tooling del repositorio

- **pnpm 11** como gestor de paquetes Node.
- **semantic-release** con `@semantic-release/changelog` y `@semantic-release/git`.
- GitHub Actions para publicación de releases.

---

## 3. Arquitectura

```
┌────────────────────────────┐        HTTPS / cookies httpOnly
│  Navegador                 │  ───────────────────────────────┐
│  React 19 + Vite           │                                 │
│  TanStack Query + Zustand  │  ◀──────────────┐               │
└────────────────────────────┘                 │               │
        │  fetch/axios (/api/v1)               │               │
        ▼                                      │               │
┌────────────────────────────┐        ┌────────┴────────────┐  │
│  Proxy de desarrollo Vite  │        │  CORS + CSRF        │  │
│  /api → 127.0.0.1:5000     │        │  (Flask-Cors/JWT)   │  │
└────────────┬───────────────┘        └────────┬────────────┘  │
             ▼                                 ▼               │
      ┌─────────────────────────────────────────────────┐      │
      │  API Flask  /api/v1                             │      │
      │  Blueprints → permisos → servicios → modelos    │      │
      └───────────────┬─────────────────────────────────┘      │
                      │ SQLAlchemy                              │
                      ▼                                         │
      ┌──────────────────────────────┐   ┌──────────────────┐  │
      │  PostgreSQL                  │   │  Redis (opcional) │  │
      │  tablas del dominio          │   │  jti revocados    │  │
      └──────────────────────────────┘   └──────────────────┘  │
                                                                │
      ┌──────────────────────────────┐                          │
      │  SMTP (Flask-Mail)           │ ◀────────────────────────┘
      │  activaciones y avisos       │
      └──────────────────────────────┘
```

### Capas del backend

```
app/api/*.py          Blueprints: rutas HTTP, lectura de parámetros, respuestas
app/core/*.py         Permisos, seguridad, errores, paginación, semáforo, auditoría
app/services/*.py     Lógica de negocio reutilizable (notificaciones, correo)
app/models/*.py       Modelos SQLAlchemy y constantes de dominio
app/schemas/*.py      Validación/serialización con Marshmallow
app/extensions.py     Instancias de db, jwt, mail, cors
app/config.py         Configuración por entorno
```

Flujo típico de una petición:

1. Llega la solicitud a `/api/v1/<blueprint>/...`.
2. El decorador `@require_permission("...")` verifica el JWT y carga al usuario activo.
3. Se valida el cuerpo con un esquema Marshmallow.
4. El endpoint consulta o modifica modelos y confirma la transacción.
5. Se responde con el sobre `{ "data": ..., "meta": ... }` o con el contrato de error.

### Capas del frontend

```
src/app/              Router, layouts, providers
src/features/         Módulos por dominio (auth, users, clients, tasks, ...)
src/shared/           API client, auth store, permisos/navegación, componentes, utilidades
src/types/            Tipos globales
src/assets/           Recursos estáticos
```

Cada feature agrupa: `api/` (funciones y hooks), `components/`, `pages/`, `schemas/`, `types.ts` e `index.ts` como barrera de exportación.

---

## 4. Estructura del repositorio

```
SISCONINT/
├─ Backend/
│  ├─ app/
│  │  ├─ api/                 # 15 blueprints (auth, users, clients, tasks, ...)
│  │  ├─ core/                # permisos, seguridad, errores, paginación, semáforo
│  │  ├─ models/              # modelos y constantes
│  │  ├─ schemas/             # esquemas Marshmallow
│  │  ├─ services/            # notificaciones, correo, auditoría
│  │  ├─ __init__.py          # create_app()
│  │  ├─ config.py            # configuración por entorno
│  │  ├─ cli.py               # comandos flask
│  │  └─ extensions.py        # db, jwt, mail, cors
│  ├─ tests/                  # pytest (HU_xx y endpoints MVP)
│  ├─ uploads/                # archivos de minutas (no versionar)
│  ├─ requirements.txt
│  ├─ wsgi.py                 # app = create_app()
│  └─ .env                    # configuración local (no versionar)
├─ Frontend/
│  ├─ public/                 # logos y recursos servidos tal cual
│  ├─ src/
│  │  ├─ app/                 # router, layouts, providers
│  │  ├─ features/            # módulos funcionales
│  │  ├─ shared/              # api, auth, componentes, utilidades, estilos
│  │  ├─ assets/
│  │  └─ types/
│  ├─ pdf-preview.html        # vista previa de desarrollo del PDF
│  ├─ package.json
│  └─ vite.config.ts
├─ docs/
│  └─ MANUAL_DESARROLLADOR.md # este documento
├─ .github/workflows/release.yml
├─ .releaserc.json
├─ CHANGELOG.md
├─ package.json               # semantic-release (raíz)
└─ pnpm-lock.yaml
```

> **Nota:** no hay migraciones Alembic. El esquema se crea con `flask init-db`, que ejecuta `db.create_all()` y **no borra ni altera** tablas existentes.

---

## 5. Requisitos previos

| Herramienta | Versión recomendada | Verificación |
| --- | --- | --- |
| Python | 3.12 | `python --version` |
| Node.js | 20 o superior (CI usa 26) | `node --version` |
| pnpm | 11.x | `pnpm --version` |
| PostgreSQL | 14 o superior | `psql --version` |
| Redis | Opcional en desarrollo | `redis-cli ping` |

En Windows, los comandos de activación del entorno virtual usan PowerShell:

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Si la política de ejecución bloquea el script de activación:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

---

## 6. Instalación y ejecución

### 6.1 Backend

```powershell
cd Backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 1) Configura Backend/.env (ver sección 7)
# 2) Crea las tablas
flask --app wsgi init-db

# 3) Crea el primer Dueño (sin contraseña)
flask --app wsgi seed-owner

# 4) Define su contraseña (política RG-05)
flask --app wsgi set-password

# 5) Levanta el servidor de desarrollo
flask --app wsgi run --debug --port 5000
```

También puedes ejecutar `python wsgi.py`, que arranca en el puerto 5000.

Verificación rápida:

```powershell
Invoke-WebRequest http://127.0.0.1:5000/health
# {"status":"ok"}
```

### 6.2 Frontend

```powershell
cd Frontend
pnpm install
pnpm dev
```

Vite sirve en `http://localhost:5173` y redirige `/api` a `http://127.0.0.1:5000` (ver `vite.config.ts`).

### 6.3 Vista previa del reporte PDF (puerto 5199)

```powershell
# Desde la raíz del repositorio
pnpm --dir Frontend pdf:preview
```

Abre `http://localhost:5199/pdf-preview.html`. La página genera el PDF con datos de ejemplo usando la misma función que el módulo de reportes; **no requiere backend ni sesión**. El detalle está en la [sección 11](#11-reportes-ejecutivos-en-pdf).

### 6.4 Orden recomendado para desarrollo

1. PostgreSQL en ejecución y base creada.
2. Backend en `127.0.0.1:5000`.
3. Frontend en `localhost:5173`.
4. Iniciar sesión con el Dueño creado por CLI.

---

## 7. Variables de entorno

El backend carga `Backend/.env` automáticamente con `python-dotenv` (`load_dotenv()` en `app/config.py`). **No versionar este archivo.**

| Variable | Obligatoria | Valor por defecto | Descripción |
| --- | --- | --- | --- |
| `APP_ENV` | No | `development` | `development`, `testing` o `production`. |
| `DATABASE_URL` | Sí | — | URL de PostgreSQL. Acepta `postgres://` y `postgresql://`; se normaliza a `postgresql+psycopg2://`. |
| `DB_SSLMODE` | No | `require` | `require` para Render/cloud; usa `disable` o `prefer` en PostgreSQL local sin SSL. |
| `TEST_DATABASE_URL` | No | — | Si existe, las pruebas usan un esquema PostgreSQL aislado; si no, SQLite en memoria. |
| `JWT_SECRET_KEY` | Producción | `dev-only-secret-change-me` en desarrollo | Firma de los JWT. En producción el arranque falla si está vacía. |
| `FRONTEND_URL` | No | `http://localhost:5173` | Origen permitido por CORS y base de los enlaces de activación. |
| `COOKIE_SAMESITE` | No | `Lax` | `Lax`, `Strict` o `None` (este último exige HTTPS y `Secure`). |
| `REDIS_URL` | No | vacío | Blocklist de JWT revocados. Sin valor se usa memoria (no compartida entre procesos). |
| `MAIL_SERVER` | No | vacío | Servidor SMTP. |
| `MAIL_PORT` | No | `587` | Puerto SMTP. |
| `MAIL_USE_TLS` | No | `true` | Acepta `1/true/yes/si/sí`. |
| `MAIL_USERNAME` | No | — | Usuario SMTP. |
| `MAIL_PASSWORD` | No | — | Contraseña SMTP. |
| `MAIL_DEFAULT_SENDER` | No | `no-reply@despacho.com` | Remitente de los correos. |
| `UPLOAD_FOLDER` | No | `Backend/uploads` | Carpeta de minutas. |
| `VITE_API_URL` | No | `/api/v1` | Solo frontend. Cambia la base de la API si no se usa el proxy. |

### Ejemplo de `.env` local

```dotenv
APP_ENV=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sisconint
DB_SSLMODE=disable
JWT_SECRET_KEY=cambia-esta-clave-por-una-larga-y-aleatoria
FRONTEND_URL=http://localhost:5173
COOKIE_SAMESITE=Lax
REDIS_URL=
MAIL_SERVER=
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_DEFAULT_SENDER=no-reply@despacho.com
```

### Notas de seguridad

- `JWT_COOKIE_SECURE = True` en la configuración base; en desarrollo se desactiva porque se usa `http://localhost`.
- `JWT_ACCESS_TOKEN_EXPIRES = 15 min` y `JWT_REFRESH_TOKEN_EXPIRES = 30 min`.
- La cookie de refresh solo se envía a `/api/v1/auth` (`JWT_REFRESH_COOKIE_PATH`).
- La política de contraseñas exige mínimo 10 caracteres, mayúscula, minúscula, número, símbolo y que no sea igual al correo.

---

## 8. Base de datos y comandos CLI

### 8.1 Comandos disponibles

| Comando | Qué hace |
| --- | --- |
| `flask --app wsgi init-db` | Crea las tablas que falten (`db.create_all()`). Idempotente. |
| `flask --app wsgi seed-owner` | Crea el primer usuario con rol `DUENO` (sin contraseña). Pide nombre, correo y teléfonos. |
| `flask --app wsgi set-password` | Asigna o restablece la contraseña con hash argon2 y valida la política. |
| `flask --app wsgi dev-token --correo X` | Imprime un access token para probar con `Authorization: Bearer`. Deshabilitado en producción. |
| `flask --app wsgi recordatorios-vencimiento` | Crea notificaciones de tareas que vencen mañana. Pensado para cron a las 08:00. |
| `flask --app wsgi purgar-notificaciones` | Elimina notificaciones con más de 90 días. |

### 8.2 Crear la base de datos

```sql
CREATE DATABASE sisconint;
```

```powershell
cd Backend
flask --app wsgi init-db
flask --app wsgi seed-owner
flask --app wsgi set-password
```

### 8.3 Probar la API sin frontend

```powershell
$token = flask --app wsgi dev-token --correo dueno@despacho.com
Invoke-RestMethod http://127.0.0.1:5000/api/v1/auth/me `
  -Headers @{ Authorization = "Bearer $token" }
```

> `dev-token` usa la ubicación `headers`, habilitada además de `cookies` para facilitar pruebas automatizadas. En el navegador la sesión viaja por cookies.

---

## 9. Backend

### 9.1 Fábrica de la aplicación

`Backend/app/__init__.py` expone `create_app(config_name=None, overrides=None)`:

- Carga la configuración según `APP_ENV` (`development`, `testing`, `production`).
- Valida que exista `JWT_SECRET_KEY` en producción y `DATABASE_URL` en todos los entornos.
- Inicializa SQLAlchemy, JWT, Mail, CORS y la blocklist de tokens.
- Registra el blueprint raíz `/api/v1` y el endpoint `GET /health`.
- Aplica `strict_slashes = False` para tolerar barras finales.

Las pruebas usan `overrides` para apuntar a un esquema PostgreSQL aislado sin tocar `public`.

### 9.2 Contrato de respuestas

**Éxito:**

```json
{
  "data": { "...": "..." },
  "meta": { "page": 1, "per_page": 20, "total": 42, "pages": 3 }
}
```

`meta` solo aparece en listados paginados. El helper es `app.core.responses.ok(data, status, meta)`.

**Error:**

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Revisa los campos marcados",
    "fields": { "correo_institucional": ["Ya está registrado"] }
  }
}
```

Códigos habituales: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `CONFLICT`, `VALIDATION_ERROR`, `ACCOUNT_DISABLED`, `ACCOUNT_LOCKED`, `TIMER_ACTIVE`.

Los errores de Marshmallow se convierten automáticamente a `fields`. Si hay `retry_after_seconds`, también se envía la cabecera `Retry-After`.

### 9.3 Paginación y búsqueda

- `app/core/pagination.py` fija **20 registros por página**; el cliente no puede cambiarlo.
- Los listados aceptan `page` y, según el módulo, `search`, filtros y ordenamientos.
- La búsqueda usa `app/core/sql.py::escape_like` para que `%`, `_` y `\` se traten como texto.
- El frontend consume `data` + `meta` mediante `Paginated<T>`.

### 9.4 Autenticación y sesión

1. `POST /api/v1/auth/login` recibe `correo_institucional` y `password`.
2. Se valida la contraseña con argon2 y se revisan bloqueos por intentos fallidos (5 fallos → 15 minutos).
3. Se emiten access y refresh token en cookies httpOnly:
   - `SISCONNI_access_token` — 15 minutos, path `/`.
   - `SISCONNI_refresh_token` — 30 minutos, path `/api/v1/auth`.
   - `csrf_access_token` — cookie legible por JS para el doble token CSRF.
4. El frontend envía `X-CSRF-TOKEN` en `POST/PUT/PATCH/DELETE` leyendo `csrf_access_token`.
5. `GET /auth/me` reconstruye la sesión al cargar la app (`AuthBootstrap` en `providers.tsx`).
6. `POST /auth/logout` revoca el `jti` en Redis o memoria y borra las cookies. Si hay un temporizador activo responde `409 TIMER_ACTIVE`.
7. `POST /auth/activate` consume un enlace de un solo uso (48 h) y define la contraseña.

> El endpoint `POST /auth/refresh` existe en el backend, pero el cliente Axios **no renueva automáticamente**: al recibir `401` limpia la sesión y los guards redirigen a `/login`.

**Blocklist de tokens:** con `REDIS_URL` se comparte entre procesos; sin Redis se usa memoria por proceso (suficiente en desarrollo y pruebas). Al cambiar el rol de un colaborador se incrementa su "generación" para invalidar sesiones vigentes.

### 9.5 Autorización: roles y matriz de permisos

Roles del sistema (`Backend/app/models/user.py`):

| Rol | Descripción |
| --- | --- |
| `DUENO` | Socio Director. Acceso total. |
| `ADMINISTRADOR` | Gestión operativa y administrativa; no edita ni asigna Dueño/Administrador. |
| `COORDINADOR` | Operación, tareas, clientes en consulta, reportes y alertas. |
| `CONTADOR` | Operación sobre sus tareas, tiempos y notificaciones; dashboard personal. |

La fuente de verdad es `Backend/app/core/permissions.py` (`PERMISSIONS`). El decorador `@require_permission("modulo:accion")` verifica JWT + usuario activo + rol.

Leyenda: **D** Dueño, **A** Administrador, **C** Coordinador, **Ct** Contador.

| Permiso | D | A | C | Ct | Módulo |
| --- | :-: | :-: | :-: | :-: | --- |
| `user:create`, `user:list`, `user:view`, `user:edit`, `user:deactivate` | ✓ | ✓ | — | — | Colaboradores |
| `user:options` | ✓ | ✓ | ✓ | ✓ | Selectores |
| `client:create`, `client:edit`, `client:deactivate` | ✓ | ✓ | — | — | Clientes |
| `client:list`, `client:view` | ✓ | ✓ | ✓ | ✓ | Clientes |
| `catalog:read` | ✓ | ✓ | ✓ | ✓ | Catálogo |
| `catalog:manage` | ✓ | ✓ | — | — | Catálogo |
| `task:create` | ✓ | ✓ | ✓ | — | Tareas |
| `task:list`, `task:view`, `task:edit`, `task:delete`, `task:board`, `task:move`, `task:subtask`, `task:comment` | ✓ | ✓ | ✓ | ✓ | Tareas |
| `task:alerts` | ✓ | ✓ | ✓ | — | Alertas |
| `time:timer`, `time:create`, `time:list`, `time:edit` | ✓ | ✓ | ✓ | ✓ | Tiempo |
| `dashboard:view` | ✓ | ✓ | ✓ | — | Dashboard global |
| `dashboard:personal` | — | — | — | ✓ | Dashboard personal |
| `report:view` | ✓ | ✓ | ✓ | — | Reportes |
| `calendar:view` | ✓ | ✓ | ✓ | ✓ | Calendario |
| `rate:list`, `rate:edit` | ✓ | ✓ | — | — | Tarifas |
| `obligation:list` | ✓ | ✓ | ✓ | ✓ | Obligaciones |
| `obligation:create`, `obligation:edit` | ✓ | ✓ | ✓ | — | Obligaciones |
| `obligation:deactivate` | ✓ | ✓ | — | — | Obligaciones |
| `minute:list`, `minute:create`, `minute:edit` | ✓ | ✓ | ✓ | ✓ | Minutas |
| `minute:delete` | ✓ | ✓ | ✓ | — | Minutas |
| `template:list`, `template:edit` | ✓ | ✓ | — | — | Plantillas |
| `notification:list`, `notification:read`, `notification:read-all` | ✓ | ✓ | ✓ | ✓ | Notificaciones |

Reglas adicionales:

- `ROLES_PROTECTED_FROM_ADMIN = {DUENO, ADMINISTRADOR}`: el Administrador no puede editar ni desactivar a esos usuarios.
- `ASSIGNABLE_ROLES`: el Dueño asigna cualquier rol; el Administrador solo `COORDINADOR` y `CONTADOR`.
- Cada usuario solo consulta y marca **sus propias** notificaciones.

### 9.6 Catálogo de endpoints

Prefijo común: `/api/v1`. Todas las rutas salvo `login`, `refresh` y `activate` exigen JWT.

#### Autenticación — `/auth`

| Método | Ruta | Permiso | Descripción |
| --- | --- | --- | --- |
| POST | `/auth/login` | Público | Inicia sesión y emite cookies. |
| POST | `/auth/refresh` | Refresh cookie | Renueva el access token. |
| GET | `/auth/me` | JWT | Usuario de la sesión actual. |
| POST | `/auth/logout` | JWT | Revoca tokens y cierra sesión. |
| POST | `/auth/activate` | Público | Activa cuenta con token de un solo uso. |

#### Colaboradores — `/users`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/users` | `user:list` |
| POST | `/users` | `user:create` |
| GET | `/users/options` | `user:options` |
| GET | `/users/<id>` | `user:view` |
| PUT | `/users/<id>` | `user:edit` |
| GET | `/users/<id>/deactivation-impact` | `user:deactivate` |
| POST | `/users/<id>/deactivate` | `user:deactivate` |

#### Clientes — `/clients`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/clients` | `client:list` |
| POST | `/clients` | `client:create` |
| GET | `/clients/options` | `client:list` |
| GET | `/clients/<id>` | `client:view` |
| PUT | `/clients/<id>` | `client:edit` |
| POST | `/clients/<id>/deactivate` | `client:deactivate` |

#### Catálogo — `/catalog`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/catalog` | `catalog:read` |
| POST | `/catalog` | `catalog:manage` |
| PUT | `/catalog/<id>` | `catalog:manage` |
| POST | `/catalog/<id>/deactivate` | `catalog:manage` |

#### Tareas — `/tasks`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/tasks` | `task:list` |
| POST | `/tasks` | `task:create` |
| GET | `/tasks/board` | `task:board` |
| GET | `/tasks/options` | `task:view` |
| GET | `/tasks/alerts` | `task:alerts` |
| GET | `/tasks/<id>` | `task:view` |
| PUT | `/tasks/<id>` | `task:edit` |
| PATCH | `/tasks/<id>/estado` | `task:move` |
| DELETE | `/tasks/<id>` | `task:delete` |
| POST | `/tasks/<id>/subtasks` | `task:subtask` |
| PUT | `/tasks/<id>/subtasks/<sub>` | `task:subtask` |
| DELETE | `/tasks/<id>/subtasks/<sub>` | `task:subtask` |
| POST | `/tasks/<id>/comments` | `task:comment` |
| PUT | `/tasks/<id>/comments/<comment>` | `task:comment` |
| DELETE | `/tasks/<id>/comments/<comment>` | `task:comment` |

#### Tiempo — `/time-entries`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/time-entries/timer` | `time:timer` |
| POST | `/time-entries/timer` | `time:timer` |
| POST | `/time-entries/timer/stop` | `time:timer` |
| GET | `/time-entries` | `time:list` |
| POST | `/time-entries` | `time:create` |
| PUT | `/time-entries/<id>` | `time:edit` |

#### Dashboard — `/dashboard`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/dashboard` | `dashboard:view` |
| GET | `/dashboard/me` | `dashboard:personal` |

#### Tarifas — `/rates`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/rates` | `rate:list` |
| PUT | `/rates/<nivel>` | `rate:edit` |

#### Obligaciones — `/obligations`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/obligations` | `obligation:list` |
| POST | `/obligations` | `obligation:create` |
| GET | `/obligations/<id>` | `obligation:list` |
| PUT | `/obligations/<id>` | `obligation:edit` |
| POST | `/obligations/<id>/deactivate` | `obligation:deactivate` |

#### Minutas — `/minutes`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/minutes` | `minute:list` |
| POST | `/minutes` | `minute:create` |
| GET | `/minutes/<id>` | `minute:list` |
| GET | `/minutes/<id>/download` | `minute:list` |
| PUT | `/minutes/<id>` | `minute:edit` |
| DELETE | `/minutes/<id>` | `minute:delete` |

Las minutas se envían como `multipart/form-data`; el límite es de **10 MB** (`MAX_CONTENT_LENGTH`).

#### Plantillas — `/templates`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/templates` | `template:list` |
| POST | `/templates` | `template:edit` |
| PUT | `/templates/<id>` | `template:edit` |

#### Calendario — `/calendar`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/calendar` | `calendar:view` |

#### Reportes — `/reports`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/reports/summary` | `report:view` |

Parámetros: `periodo` (`MES_ACTUAL`, `MES_ANTERIOR`, `TRIMESTRE`, `ANIO`, `PERSONALIZADO`), `fecha_desde`, `fecha_hasta`, `cliente`, `colaborador`.

#### Notificaciones — `/notifications`

| Método | Ruta | Permiso |
| --- | --- | --- |
| GET | `/notifications` | `notification:list` |
| PATCH | `/notifications/<id>/leida` | `notification:read` |
| PATCH | `/notifications/leidas` | `notification:read-all` |

### 9.7 Reglas de negocio relevantes

**Semáforo de vencimiento** (`app/core/semaforo.py`):

| Color | Condición |
| --- | --- |
| `VERDE` | Faltan 3 días o más. |
| `AMARILLO` | Faltan 1 o 2 días. |
| `ROJO` | Vence hoy o ya venció. |
| `GRIS` | Tarea `COMPLETADO`. |

Siempre se calcula en el servidor con la zona `America/Mexico_City` y días naturales; el cliente no lo envía.

**Estados de tarea:** `POR_HACER`, `EN_PROGRESO`, `EN_REVISION`, `COMPLETADO`. El cambio de estado se hace con `PATCH /tasks/<id>/estado` y queda en `historial_estado_tarea`.

**Temporizador:** solo puede existir uno activo por colaborador (`temporizador_activo`). Al detenerlo se crea un `registro_tiempo`. No se permite cerrar sesión con temporizador activo.

**Notificaciones:** se generan al asignar tareas, al acercarse la fecha límite y por eventos del sistema. La purga elimina registros con más de 90 días.

**Auditoría:** las operaciones sensibles escriben en `bitacora_auditoria` mediante `app/core/audit.py`.

---

## 10. Frontend

### 10.1 Arranque y providers

- `src/main.tsx` monta `<App />` en `#root` y carga `style.css`.
- `src/app/App.tsx` envuelve el router con `Providers`.
- `Providers` incluye TanStack Query (`retry: 1`, sin refetch al enfocar) y `AuthBootstrap`, que llama a `authApi.me()` para recuperar la sesión.

### 10.2 Rutas principales

| Ruta | Página | Acceso |
| --- | --- | --- |
| `/login` | Login | Solo invitados (`GuestOnly`). |
| `/activar` | Activación de cuenta | Público. |
| `/dashboard` | Dashboard | Autenticado. |
| `/colaboradores` | Lista de colaboradores | Dueño, Administrador. |
| `/colaboradores/nuevo` | Alta de colaborador | Dueño, Administrador. |
| `/colaboradores/:id` | Edición | Dueño, Administrador. |
| `/clientes` | Clientes | Autenticado. |
| `/clientes/nuevo` | Alta de cliente | Dueño, Administrador. |
| `/clientes/:id` | Ficha de cliente | Autenticado. |
| `/catalogo` | Catálogo | Autenticado. |
| `/tareas`, `/tareas/:id` | Tareas y detalle | Autenticado. |
| `/tablero` | Kanban | Autenticado. |
| `/calendario` | Calendario | Autenticado. |
| `/obligaciones` | Obligaciones | Autenticado. |
| `/minutas` | Minutas | Autenticado. |
| `/tiempos` | Registro de tiempo | Autenticado. |
| `/tarifas` | Tarifas | Dueño, Administrador. |
| `/reportes` | Reportes ejecutivos | Dueño, Administrador, Coordinador. |
| `/plantillas` | Plantillas de correo | Dueño, Administrador. |
| `/alertas` | Alertas | Dueño, Administrador, Coordinador. |
| `/notificaciones` | Notificaciones | Autenticado. |
| `/configuracion`, `/soporte` | Placeholders | Autenticado. |

Las rutas no implementadas de `NAV_SECTIONS` se registran automáticamente como `PagePlaceholder` con su guarda de rol.

### 10.3 Guardas y navegación

- `RequireAuth`: espera a que `status` deje de ser `checking`; si es `anonymous`, redirige a `/login`.
- `GuestOnly`: si ya hay sesión, redirige a `/dashboard`.
- `RequireRole`: valida el rol antes de renderizar la página; no sustituye la autorización del backend.
- `NAV_SECTIONS` (`shared/auth/permissions.ts`) define secciones, etiquetas, iconos y roles visibles en el sidebar.

> **Regla de oro:** toda regla de acceso debe existir en el backend. Las guardas del frontend solo mejoran la experiencia; nunca son la única barrera.

### 10.4 Cliente HTTP

`src/shared/api/client.ts`:

- `baseURL`: `VITE_API_URL` o `/api/v1`.
- `withCredentials: true` para enviar y recibir cookies.
- Interceptor de solicitud: en métodos no seguros copia `csrf_access_token` a `X-CSRF-TOKEN`.
- Interceptor de respuesta: convierte cualquier error en `ApiError` con `status`, `code`, `message`, `fields` y `retryAfter`.
- Un `401` fuera de `/auth/login` limpia el estado de sesión.

Las features consumen la API con TanStack Query. Ejemplo de listado paginado:

```ts
const { data, isLoading } = useQuery({
  queryKey: ["tasks", page, search],
  queryFn: () => api.get<Paginated<Task>>("/tasks", { params: { page, search } }),
});
```

### 10.5 Estado de autenticación

`useAuthStore` (Zustand) expone:

```ts
interface AuthState {
  user: AuthUser | null;      // { id, nombre, rol }
  status: "checking" | "authenticated" | "anonymous";
  setUser: (u: AuthUser) => void;
  clear: () => void;
}
```

No se persiste en `localStorage`: la fuente de verdad es la cookie httpOnly y `GET /auth/me`.

### 10.6 Estilos e identidad

- Tailwind 4 con tokens propios: `navy-900`, `gold-300`, `ink`, `muted`, `line`, `surface`, `app`.
- Tipografías: Inter (texto) y Montserrat (títulos), cargadas desde Google Fonts en `index.html`.
- Logo y marca en `Frontend/public/logo-tellez-ponce.png` y `logo-tellez-ponce-mark.png`.
- Componentes compartidos en `src/shared/components/`: `PageHeader`, `Notice`, `LoadingState`, `ErrorState`, `PagePlaceholder`, badges, etc.

---

## 11. Reportes ejecutivos en PDF

### 11.1 Flujo funcional

1. El usuario entra a `/reportes` y elige periodo, cliente y colaborador.
2. `GET /api/v1/reports/summary` devuelve `ReportData` (KPIs, horas, estados, distribuciones y costo estimado).
3. La página muestra tarjetas y gráficas.
4. Al pulsar **Exportar PDF**, `exportReportPdf(data)` genera y descarga el archivo.
5. El PDF es vectorial: no usa capturas del DOM, por lo que el texto y las gráficas siempre salen nítidos.

### 11.2 Archivos clave

| Archivo | Responsabilidad |
| --- | --- |
| `Frontend/src/features/reports/pdf/reportPdf.ts` | Clase `ReportPdf`, portada, KPIs, dona de estados, barras, tablas, notas y paginación. Exporta `buildReportPdf`, `exportReportPdf` y `reportPdfFileName`. |
| `Frontend/src/features/reports/types.ts` | Contrato `ReportData` y tipos de filas. |
| `Frontend/src/features/reports/pages/pages.tsx` | Filtros, consulta y botón de exportación. |
| `Frontend/public/logo-tellez-ponce.png` | Logo completo para portada. |
| `Frontend/public/logo-tellez-ponce-mark.png` | Isotipo para encabezados y favicon. |

### 11.3 API del generador

```ts
// Construye el documento sin descargarlo
const { doc, fileName } = await buildReportPdf(data);
doc.output("bloburl"); // URL para un iframe
doc.save(fileName);    // descarga

// Genera y descarga en una sola llamada
await exportReportPdf(data);
```

`buildReportPdf` importa `jspdf` de forma dinámica, de modo que el bundle inicial no carga la librería hasta que se necesita.

### 11.4 Vista previa en el puerto 5199

La página `Frontend/pdf-preview.html` permite revisar el diseño del PDF sin backend, sin login y sin datos reales.

```powershell
pnpm --dir Frontend pdf:preview
```

- URL: `http://localhost:5199/pdf-preview.html`
- El script `pdf:preview` ejecuta `vite --port 5199 --strictPort`, así que falla de inmediato si el puerto está ocupado.
- La página usa un objeto `sample` con la misma forma que `ReportData` y llama a `buildReportPdf(sample)`.
- El resultado se muestra en un `<iframe>` y el botón **Descargar PDF** guarda el archivo con el nombre real del reporte.
- **Regenerar** vuelve a construir el documento (útil al ajustar estilos o saltos de página).
- Los logos se cargan desde `public/`, por lo que la vista previa requiere que Vite sirva la raíz del frontend.

Para actualizar los datos de ejemplo, edita el objeto `sample` dentro de `pdf-preview.html`. Mantén los nombres de propiedad de `ReportData` para no romper el generador.

> Esta página es una herramienta de desarrollo. No se incluye en la navegación ni requiere autenticación; no debe publicarse como parte del producto.

### 11.5 Puntos a cuidar al modificar el PDF

- Unidades en milímetros (A4 vertical: 210 × 297).
- Márgenes y límite inferior en `PAGE` (`margin: 14`, `bottom: 275`).
- Usa `ensureSpace()` antes de dibujar bloques para evitar saltos prematuros.
- Las gráficas se dibujan con primitivas de jsPDF (`circle`, `rect`, `line`), no con imágenes.
- Los acentos deben codificarse correctamente; el documento está en español.
- Verifica el resultado con la vista previa después de cada cambio de layout.

---

## 12. Pruebas

### 12.1 Ejecución

```powershell
cd Backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Para un módulo o prueba concreta:

```powershell
pytest tests/test_hu30_list_tasks.py -q
pytest tests/test_hu49_timer_start.py::test_nombre -q
```

### 12.2 Configuración de la base de pruebas

`Backend/tests/conftest.py`:

- Si `TEST_DATABASE_URL` apunta a PostgreSQL, crea un **esquema aislado** `test_<uuid>`, ajusta `search_path` y lo elimina al final. No toca `public`.
- Si no existe, usa **SQLite en memoria** (`sqlite://`), suficiente para la mayoría de pruebas.
- Cada prueba crea las tablas, trunca los datos y las vuelve a limpiar.

Fixtures principales:

| Fixture | Uso |
| --- | --- |
| `app` | Aplicación en modo `testing` con base limpia. |
| `client` | Cliente de pruebas de Flask. |
| `make_user` | Crea un colaborador con rol, estatus y contraseña. |
| `auth_headers` | Genera `Authorization: Bearer` para un usuario. |
| `valid_payload` | Payload válido de alta de colaborador. |

### 12.3 Cobertura funcional

Las pruebas están organizadas por historia de usuario (`test_huXX_...`), además de `test_mvp_endpoints.py`. Cubren autenticación, colaboradores, tareas, Kanban, tiempos, semáforo, notificaciones, dashboards y endpoints base.

### 12.4 Calidad del frontend

```powershell
pnpm --dir Frontend lint
pnpm --dir Frontend build
```

`build` ejecuta `tsc -b` y `vite build`; ambos deben terminar sin errores antes de abrir un PR.

---

## 13. CI/CD y versionado

### 13.1 Release automatizado

`.github/workflows/release.yml` se ejecuta en push a `main` y `develop`:

1. Checkout con historial completo.
2. Instala pnpm 11 y Node 26.
3. `pnpm install --frozen-lockfile`.
4. `pnpm exec semantic-release` con `GITHUB_TOKEN`.

Configuración en `.releaserc.json`:

- `main` → versión estable.
- `develop` → prerelease `beta`.
- Actualiza `CHANGELOG.md`, crea el tag/release y publica notas en GitHub.

### 13.2 Convención de commits

Se usa **Conventional Commits**, porque semantic-release deriva la versión del historial:

| Prefijo | Efecto |
| --- | --- |
| `feat:` | Nueva funcionalidad (minor). |
| `fix:` | Corrección (patch). |
| `perf:` | Mejora de rendimiento (patch). |
| `refactor:`, `docs:`, `test:`, `chore:`, `ci:` | Sin release por sí solos. |
| `feat!:` o `BREAKING CHANGE:` | Cambio incompatible (major). |

Ejemplos:

```
feat(reportes): exportar resumen ejecutivo en PDF
fix(auth): renovar correctamente la cookie csrf
docs(manual): documentar vista previa del PDF
```

> El workflow actual **no ejecuta pruebas**. Ejecuta `pytest`, `lint` y `build` localmente antes de integrar.

### 13.3 Monitoreo de disponibilidad (Better Stack)

`.github/workflows/betterstack-monitors.yml` sincroniza los monitores de Better Stack Uptime con `monitoring/betterstack/monitors.json` (frontend en Netlify, backend + PostgreSQL en Render y el proxy `/api/*` de Netlify). Las alertas llegan a Slack por la integración de Better Stack.

El backend expone dos endpoints sin sesión: `GET /health` (liveness) y `GET /api/v1/health` (verifica la base de datos; 503 si no responde).

Pasos de configuración, variables (`BETTERSTACK_API_TOKEN`, `FRONTEND_URL`) y cómo probar la alerta: **[docs/MONITOREO.md](MONITOREO.md)**.

---

## 14. Solución de problemas

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| El login devuelve `502` en el frontend | El backend no está corriendo o el proxy apunta a otro puerto. | Levanta `flask --app wsgi run --port 5000` y revisa `vite.config.ts`. |
| `DATABASE_URL no está configurada` | Falta `Backend/.env` o la variable está vacía. | Crea el `.env` y reinicia el proceso. |
| Error SSL al conectar a PostgreSQL local | `DB_SSLMODE=require` contra un servidor sin SSL. | Usa `DB_SSLMODE=disable` o `prefer`. |
| `JWT_SECRET_KEY es obligatorio en producción` | `APP_ENV=production` sin secreto. | Define un secreto largo y aleatorio. |
| `401` en `POST/PUT/PATCH/DELETE` pero `GET` funciona | Falta la cabecera CSRF. | Envía `X-CSRF-TOKEN` con el valor de `csrf_access_token`. |
| La sesión se pierde a los 15 minutos | El access token expiró y no hay refresh automático. | Inicia sesión de nuevo o implementa renovación en el interceptor. |
| CORS bloquea las cookies | `FRONTEND_URL` no coincide con el origen real. | Ajusta `FRONTEND_URL` (sin barra final). |
| El logout responde `409 TIMER_ACTIVE` | Hay un temporizador corriendo. | Detén y guarda el temporizador antes de salir. |
| Error al subir una minuta | Archivo mayor a 10 MB. | Reduce el tamaño o ajusta `MAX_CONTENT_LENGTH`. |
| El PDF no muestra logos en la vista previa | Los archivos no están en `Frontend/public/` o Vite no sirve la raíz del frontend. | Verifica las rutas y ejecuta la vista previa desde `Frontend`. |
| `--strictPort` falla al iniciar 5199 | El puerto está ocupado. | Libera el puerto o cambia el script temporalmente. |
| Las tablas no existen | No se ejecutó `init-db`. | `flask --app wsgi init-db`. |
| Un cambio de esquema no se refleja | No hay migraciones; `create_all` no altera tablas. | Aplica el `ALTER TABLE` manualmente o recrea la tabla en desarrollo. |
| Las notificaciones de vencimiento no aparecen | El comando programado no se ejecutó. | Programa `flask --app wsgi recordatorios-vencimiento` a las 08:00. |

---

## 15. Convenciones y checklist

### 15.1 Backend

- Un blueprint por módulo en `app/api/` con `url_prefix` propio.
- Registrar el blueprint en `app/api/__init__.py`.
- Proteger cada endpoint con `@require_permission("...")`; añadir el permiso a `PERMISSIONS`.
- Validar la entrada con Marshmallow; no confiar en el frontend.
- Responder con `ok(...)` y lanzar errores de dominio (`NotFoundError`, `ConflictError`, etc.).
- Respetar el listado de 20 por página y escapar `LIKE`.
- Escribir en auditoría las operaciones sensibles.
- Mantener la lógica de negocio en `services/` cuando se reutilice.

### 15.2 Frontend

- Cada feature exporta su API pública desde `index.ts`.
- Usar TanStack Query para datos remotos; no duplicar estado del servidor en Zustand.
- Las claves de query deben incluir los filtros que afectan el resultado.
- Tipar respuestas con `ApiResponse<T>` / `Paginated<T>`.
- Manejar `loading`, `error` y `empty` con los componentes compartidos.
- Respetar los tokens de Tailwind y la tipografía del design system.
- Añadir la ruta en `router.tsx` y, si aplica, en `NAV_SECTIONS`.

### 15.3 Checklist antes de un PR

- [ ] `pytest -q` en `Backend` sin fallos.
- [ ] `pnpm --dir Frontend lint` sin errores.
- [ ] `pnpm --dir Frontend build` correcto.
- [ ] Endpoint nuevo protegido y documentado en este manual.
- [ ] Permiso nuevo agregado a `PERMISSIONS` y a la matriz del manual.
- [ ] Ruta nueva con guarda y entrada de navegación coherentes.
- [ ] Sin secretos ni `.env` en el commit.
- [ ] Mensaje de commit en formato Conventional Commits.
- [ ] Si se tocó el PDF, revisado en `http://localhost:5199/pdf-preview.html`.

---

## 16. Anexo: tablas de la base de datos

| Tabla | Modelo | Propósito |
| --- | --- | --- |
| `colaborador` | `Colaborador` | Usuarios, rol, estatus, grado y datos de contacto. |
| `cliente` | `Cliente` | Personas físicas/morales. |
| `cliente_regimen` | `ClienteRegimen` | Régimen fiscal por cliente. |
| `regimen_fiscal` | `RegimenFiscal` | Catálogo de regímenes (SAT). |
| `contacto_cliente` | `ContactoCliente` | Contactos del cliente. |
| `permiso_atencion_cliente` | `PermisoAtencionCliente` | Acceso puntual de un colaborador a un cliente. |
| `categoria_proyecto` | `CategoriaProyecto` | Catálogo de servicios/proyectos. |
| `tarea` | `Tarea` | Tareas, asignación, fechas y estado. |
| `subtarea` | `Subtarea` | Checklist de una tarea. |
| `comentario` | `Comentario` | Comentarios de tareas. |
| `historial_estado_tarea` | `HistorialEstadoTarea` | Trazabilidad de cambios de estado. |
| `registro_tiempo` | `RegistroTiempo` | Horas capturadas por tarea y colaborador. |
| `temporizador_activo` | `TemporizadorActivo` | Temporizador en curso (uno por colaborador). |
| `permiso_fuera_plazo` | `PermisoFueraPlazo` | Autorización para capturar tiempo extemporáneo. |
| `tarifa_nivel` | `TarifaNivel` | Costo por hora según grado. |
| `obligacion` | `Obligacion` | Obligaciones fiscales/legales y vencimientos. |
| `minuta` | `Minuta` | Documentos adjuntos por cliente. |
| `notificacion` | `Notificacion` | Avisos internos por usuario. |
| `plantilla_notificacion` | `PlantillaNotificacion` | Plantillas de correo. |
| `envio_correo` | `EnvioCorreo` | Bitácora de envíos. |
| `enlace_activacion` | `EnlaceActivacion` | Tokens de activación de cuenta. |
| `codigo_recuperacion` | `CodigoRecuperacion` | Códigos de recuperación de contraseña. |
| `intento_login` | `IntentoLogin` | Intentos fallidos y bloqueos. |
| `bitacora_auditoria` | `BitacoraAuditoria` | Auditoría de operaciones sensibles. |

---

### Recursos relacionados

- `README.md` — inicio rápido y enlaces.
- `CHANGELOG.md` — historial de versiones generado por semantic-release.
- `.postman/` y `postman/` — colecciones de ejemplo para probar la API.
- `Backend/tests/` — ejemplos vivos del contrato de cada endpoint.

---

*Documento mantenido por el equipo de SISCONINT. Si agregas un módulo, un permiso o una variable de entorno, actualiza este manual en el mismo pull request.*
