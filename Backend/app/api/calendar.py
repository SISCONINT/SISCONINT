"""Calendario de vencimientos. Prefijo /api/v1/calendar."""
from flask import Blueprint, g, request

from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.calendar_schema import CalendarQuerySchema, CalendarSchema
from app.services import calendar_service

bp = Blueprint("calendar", __name__, url_prefix="/calendar")


@bp.get("")
@require_permission("calendar:view")
def get_calendar():
    """Vencimientos de tareas por fecha (los 4 roles, con alcance RG-12).

    Si no se envía rango se usa el mes actual. Filtros opcionales: cliente y
    colaborador. Devuelve los eventos y el conteo por día.
    """
    filtros = CalendarQuerySchema().load(request.args.to_dict())
    data = calendar_service.get_calendar(g.current_user, filtros)
    return ok(CalendarSchema().dump(data))
