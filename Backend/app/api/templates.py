"""Plantillas de correo. Prefijo /api/v1/templates."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.plantilla_schema import PlantillaCreateSchema, PlantillaUpdateSchema
from app.services import template_service

bp = Blueprint("templates", __name__, url_prefix="/templates")


@bp.get("")
@require_permission("template:list")
def list_templates():
    return ok([t.to_dict() for t in template_service.list_templates()])


@bp.post("")
@require_permission("template:edit")
def create_template():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = PlantillaCreateSchema().load(payload)
    plantilla = template_service.create_template(g.current_user, data)
    return ok(plantilla.to_dict(), status=201)


@bp.put("/<int:plantilla_id>")
@require_permission("template:edit")
def update_template(plantilla_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = PlantillaUpdateSchema().load(payload)
    plantilla = template_service.update_template(g.current_user, plantilla_id, data)
    return ok(plantilla.to_dict())
