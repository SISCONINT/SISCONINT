"""Módulo 5: Tareas. Prefijo /api/v1/tasks. HU_29-33 (alta, listado, detalle, edición y borrado)."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.tarea_detail_schema import TareaDetailSchema
from app.schemas.tarea_list_schema import TareaListItemSchema, TareaListQuerySchema
from app.schemas.tarea_schema import TareaCreateSchema, TareaUpdateSchema
from app.services import task_service

bp = Blueprint("tasks", __name__, url_prefix="/tasks")


@bp.get("")
@require_permission("task:list")
def list_tasks():
    """HU_30: Consultar el listado de tareas (los 4 roles, con alcance RG-12).

    Filtros opcionales: cliente, responsable, estado, prioridad, categoria,
    fecha_limite_desde, fecha_limite_hasta, semaforo y page.
    """
    filtros = TareaListQuerySchema().load(request.args.to_dict())  # errores -> 422
    items, page = task_service.list_tasks(g.current_user, filtros)
    return ok(TareaListItemSchema(many=True).dump(items), meta=pagination_meta(page))


@bp.get("/<int:tarea_id>")
@require_permission("task:view")
def get_task(tarea_id: int):
    """HU_31: Consultar el detalle de una tarea (los 4 roles, con alcance RG-12).

    Devuelve todos los campos, creador, semáforo, subtareas con avance, comentarios,
    historial de estados y tiempo registrado total y por colaborador.
    """
    detalle = task_service.get_task_detail(g.current_user, tarea_id)
    return ok(TareaDetailSchema().dump(detalle))


@bp.put("/<int:tarea_id>")
@require_permission("task:edit")
def update_task(tarea_id: int):
    """HU_32: Editar tarea (Dueño, Administrador, Coordinador; el Contador solo las suyas).

    Recibe los campos modificados (los mismos del alta, sin `estado`) y devuelve la
    tarea actualizada con el mismo contrato del detalle.
    """
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = TareaUpdateSchema().load(payload)  # errores -> 422
    tarea = task_service.update_task(g.current_user, tarea_id, data)
    detalle = task_service.get_task_detail(g.current_user, tarea.id)
    return ok(TareaDetailSchema().dump(detalle))


@bp.delete("/<int:tarea_id>")
@require_permission("task:delete")
def delete_task(tarea_id: int):
    """HU_33: Eliminar tarea (Dueño, Administrador, Coordinador; el Contador solo las suyas).

    La eliminación es lógica (RG-03) y arrastra a sus subtareas y comentarios. RG-14:
    la confirmación que nombra la tarea se pide en la interfaz antes de esta llamada.
    """
    return ok(task_service.delete_task(g.current_user, tarea_id))


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
