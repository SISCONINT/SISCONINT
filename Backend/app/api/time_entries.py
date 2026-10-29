"""Módulo 8: Registro de Tiempos. Prefijo /api/v1/time-entries. HU_49-53."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.time_entry_schema import (
    TimeEntryListQuerySchema,
    TimeEntryManualSchema,
    TimeEntrySchema,
    TimeEntryTimerResultSchema,
    TimeEntryTimerStartSchema,
    TimeEntryTimerStateSchema,
    TimeEntryTimerStopSchema,
    TimeEntryUpdateSchema,
)
from app.services import time_service

bp = Blueprint("time_entries", __name__, url_prefix="/time-entries")


def _payload() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    return payload


# ---------------------------------------------------------------------------
# HU_49-50: temporizador
# ---------------------------------------------------------------------------
@bp.get("/timer")
@require_permission("time:timer")
def get_timer():
    """HU_49-50: estado del temporizador activo (los 4 roles).

    Devuelve el temporizador con `iniciado_en` (UTC), `transcurrido` en HH:MM:SS y
    `transcurrido_segundos`. Si quedó uno activo de un día anterior, se cierra
    automáticamente a las 23:59 y viaja en `aviso_cierre_automatico`.
    """
    estado = time_service.get_timer_state(g.current_user)
    return ok(TimeEntryTimerStateSchema().dump(estado))


@bp.post("/timer")
@require_permission("time:timer")
def start_timer():
    """HU_49: iniciar temporizador en una tarea asignada y no Completada.

    Un colaborador solo puede tener un temporizador activo; si ya existe uno se
    responde 409 con sus datos para pedir que lo detenga y guarde.
    """
    data = TimeEntryTimerStartSchema().load(_payload())
    temporizador = time_service.start_timer(g.current_user, data["tarea_id"])
    estado = {"activo": temporizador, "aviso_cierre_automatico": None}
    return ok(TimeEntryTimerStateSchema().dump(estado), status=201)


@bp.post("/timer/stop")
@require_permission("time:timer")
def stop_timer():
    """HU_50: detener el temporizador y guardar el registro.

    La duración se redondea al minuto más cercano; si es menor a 1 minuto se descarta
    con aviso. Si el temporizador venía de un día anterior, se cierra automáticamente.
    """
    data = TimeEntryTimerStopSchema().load(_payload())
    resultado = time_service.stop_timer(g.current_user, data)
    return ok(TimeEntryTimerResultSchema().dump(resultado))


# ---------------------------------------------------------------------------
# HU_51-53: registros
# ---------------------------------------------------------------------------
@bp.get("")
@require_permission("time:list")
def list_entries():
    """HU_52: consultar registros de tiempo (los 4 roles, con alcance RG-12).

    Columnas: fecha, empleado, cliente, tarea, tipo y horas, más el total de horas del
    filtro en `meta`. Filtros: fecha_desde, fecha_hasta (por defecto la semana actual),
    empleado (ignorado para el Contador) y cliente. Paginación fija de 20 (RG-07).
    """
    filtros = TimeEntryListQuerySchema().load(request.args.to_dict())
    items, meta = time_service.list_entries(g.current_user, filtros)
    return ok(TimeEntrySchema(many=True).dump(items), meta=meta)


@bp.post("")
@require_permission("time:create")
def create_manual_entry():
    """HU_51: registrar tiempo manualmente (los 4 roles).

    Recibe tarea asignada al usuario, fecha (hoy por defecto), horas (0-23), minutos
    (0-59) y descripción (5-500). No se aceptan fechas futuras ni más de 24 horas por
    usuario en un mismo día.
    """
    data = TimeEntryManualSchema().load(_payload())
    registro = time_service.create_manual_entry(g.current_user, data)
    return ok(TimeEntrySchema().dump(registro), status=201)


@bp.put("/<int:registro_id>")
@require_permission("time:edit")
def update_entry(registro_id: int):
    """HU_53: editar un registro de tiempo.

    Se puede cambiar duración (horas/minutos), descripción y tarea. El autor solo
    edita sus registros del mismo día natural; Dueño y Administrador editan cualquiera.
    """
    data = TimeEntryUpdateSchema().load(_payload())
    registro = time_service.update_entry(g.current_user, registro_id, data)
    return ok(TimeEntrySchema().dump(registro))
