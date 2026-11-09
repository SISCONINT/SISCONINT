"""Minutas y acuerdos. Prefijo /api/v1/minutes."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.minuta_schema import MinutaCreateSchema, MinutaQuerySchema, MinutaUpdateSchema
from app.services import minute_service

bp = Blueprint("minutes", __name__, url_prefix="/minutes")


@bp.get("")
@require_permission("minute:list")
def list_minutes():
    filtros = MinutaQuerySchema().load(request.args.to_dict())
    page = minute_service.list_minutes(filtros)
    return ok([m.to_dict() for m in page.items], meta=pagination_meta(page))


@bp.post("")
@require_permission("minute:create")
def create_minute():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = MinutaCreateSchema().load(payload)
    minuta = minute_service.create_minute(g.current_user, data)
    return ok(minuta.to_dict(), status=201)


@bp.get("/<int:minuta_id>")
@require_permission("minute:list")
def get_minute(minuta_id: int):
    return ok(minute_service.get_minute(minuta_id).to_dict())


@bp.put("/<int:minuta_id>")
@require_permission("minute:edit")
def update_minute(minuta_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = MinutaUpdateSchema().load(payload)
    minuta = minute_service.update_minute(g.current_user, minuta_id, data)
    return ok(minuta.to_dict())


@bp.delete("/<int:minuta_id>")
@require_permission("minute:delete")
def delete_minute(minuta_id: int):
    minute_service.delete_minute(g.current_user, minuta_id)
    return ok({"id": minuta_id})
