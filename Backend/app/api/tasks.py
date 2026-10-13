"""Módulo 5: Tareas. Prefijo /api/v1/tasks. HU_29 (POST)."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.tarea_schema import TareaCreateSchema
from app.services import task_service

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@bp.post("")
@require_permission("task:create")
def create_task():
    """HU_29: Crear tarea (Dueño, Administrador o Coordinador)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = TareaCreateSchema().load(payload)  # errores -> 422
    tarea = task_service.create_task(g.current_user, data)
    return ok(tarea.to_dict(), status=201)