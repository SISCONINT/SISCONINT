"""Minutas y acuerdos. Prefijo /api/v1/minutes."""
from flask import Blueprint, g, request

from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.minuta_schema import MinutaCreateSchema, MinutaQuerySchema, MinutaUpdateSchema
from app.services import minute_service

bp = Blueprint("minutes", __name__, url_prefix="/minutes")


def _form_data() -> dict:
    return request.form.to_dict()


@bp.get("")
@require_permission("minute:list")
def list_minutes():
    filtros = MinutaQuerySchema().load(request.args.to_dict())
    page = minute_service.list_minutes(filtros)
    return ok([m.to_dict() for m in page.items], meta=pagination_meta(page))


@bp.post("")
@require_permission("minute:create")
def create_minute():
    data = MinutaCreateSchema().load(_form_data())
    minuta = minute_service.create_minute(
        g.current_user, data, request.files.get("archivo")
    )
    return ok(minuta.to_dict(), status=201)


@bp.get("/<int:minuta_id>")
@require_permission("minute:list")
def get_minute(minuta_id: int):
    return ok(minute_service.get_minute(minuta_id).to_dict())


@bp.get("/<int:minuta_id>/download")
@require_permission("minute:list")
def download_minute(minuta_id: int):
    return minute_service.download_minute(minuta_id)


@bp.put("/<int:minuta_id>")
@require_permission("minute:edit")
def update_minute(minuta_id: int):
    data = MinutaUpdateSchema().load(_form_data())
    minuta = minute_service.update_minute(
        g.current_user, minuta_id, data, request.files.get("archivo")
    )
    return ok(minuta.to_dict())


@bp.delete("/<int:minuta_id>")
@require_permission("minute:delete")
def delete_minute(minuta_id: int):
    minute_service.delete_minute(g.current_user, minuta_id)
    return ok({"id": minuta_id})
