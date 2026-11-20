# SISCONINT

Sistema de Control Interno para **Téllez Ponce & Asociados**. Centraliza colaboradores, clientes, tareas, tiempos, obligaciones, minutas, notificaciones y reportes ejecutivos en una sola aplicación web.

## Stack

- **Backend:** Flask 3 + SQLAlchemy + PostgreSQL + JWT en cookies httpOnly
- **Frontend:** React 19 + Vite + TypeScript + Tailwind CSS 4
- **Reportes:** PDF vectorial con jsPDF (logo, identidad corporativa y gráficas)

## Inicio rápido

### Backend

```powershell
cd Backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configura Backend/.env (ver el manual)
flask --app wsgi init-db
flask --app wsgi seed-owner
flask --app wsgi set-password
flask --app wsgi run --debug --port 5000
```

### Frontend

```powershell
cd Frontend
pnpm install
pnpm dev
```

Abre `http://localhost:5173`.

### Vista previa del PDF

```powershell
pnpm --dir Frontend pdf:preview
```

Abre `http://localhost:5199/pdf-preview.html` para revisar el reporte con datos de ejemplo, sin backend.

## Documentación

La guía completa de arquitectura, configuración, endpoints, permisos, pruebas y convenciones está en:

- **[docs/MANUAL_DESARROLLADOR.md](docs/MANUAL_DESARROLLADOR.md)** — manual en Markdown.
- **[docs/MANUAL_DESARROLLADOR.docx](docs/MANUAL_DESARROLLADOR.docx)** — versión Word con portada, índice y formato corporativo.

## Estructura

```
Backend/    API Flask, modelos, servicios, CLI y pruebas
Frontend/   Aplicación React (features por dominio)
docs/       Documentación técnica
```

## Roles

`DUENO`, `ADMINISTRADOR`, `COORDINADOR` y `CONTADOR`. La autorización se valida siempre en el backend mediante la matriz de `Backend/app/core/permissions.py`.

## Pruebas

```powershell
cd Backend
pytest -q

pnpm --dir Frontend lint
pnpm --dir Frontend build
```

## Licencia

Uso interno de Téllez Ponce & Asociados.
