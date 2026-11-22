"""Obligaciones periódicas. Prefijo /api/v1/obligations."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.obligacion_schema import (
    ObligacionCreateSchema,
    ObligacionQuerySchema,
    ObligacionUpdateSchema,
)
from app.services import obligation_service

bp = Blueprint("obligations", __name__, url_prefix="/obligations")


@bp.get("")
@require_permission("obligation:list")
def list_obligations():
    filtros = ObligacionQuerySchema().load(request.args.to_dict())
    page = obligation_service.list_obligations(filtros)
    return ok([o.to_dict() for o in page.items], meta=pagination_meta(page))


@bp.post("")
@require_permission("obligation:create")
def create_obligation():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = ObligacionCreateSchema().load(payload)
    obligacion = obligation_service.create_obligation(g.current_user, data)
    return ok(obligacion.to_dict(), status=201)


@bp.get("/<int:obligacion_id>")
@require_permission("obligation:list")
def get_obligation(obligacion_id: int):
    return ok(obligation_service.get_obligation(obligacion_id).to_dict())


@bp.put("/<int:obligacion_id>")
@require_permission("obligation:edit")
def update_obligation(obligacion_id: int):
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    data = ObligacionUpdateSchema().load(payload)
    obligacion = obligation_service.update_obligation(g.current_user, obligacion_id, data)
    return ok(obligacion.to_dict())


@bp.post("/<int:obligacion_id>/deactivate")
@require_permission("obligation:deactivate")
def deactivate_obligation(obligacion_id: int):
    obligacion = obligation_service.deactivate_obligation(g.current_user, obligacion_id)
    return ok(obligacion.to_dict())
