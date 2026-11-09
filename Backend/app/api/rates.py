"""Módulo 13: Tarifas. Prefijo /api/v1/rates. HU_57-62."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.tarifa_schema import TarifaSchema, TarifaUpsertSchema
from app.services import rate_service

bp = Blueprint("rates", __name__, url_prefix="/rates")


@bp.get("")
@require_permission("rate:list")
def list_rates():
    """HU_58: Consultar el catálogo de tarifas por colaborador (Dueño o Administrador)."""
    return ok(TarifaSchema(many=True).dump(rate_service.list_rates()))


@bp.put("/<int:colaborador_id>")
@require_permission("rate:edit")
def upsert_rate(colaborador_id: int):
    """HU_59-60: Fijar o actualizar la tarifa por hora de un colaborador."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = TarifaUpsertSchema().load(payload)  # errores -> 422
    tarifa = rate_service.upsert_rate(g.current_user, colaborador_id, data)
    return ok(tarifa.to_dict())
