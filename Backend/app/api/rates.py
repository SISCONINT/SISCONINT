"""Módulo 13: Tarifas por nivel. Prefijo /api/v1/rates. HU_57-62."""
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
    """HU_58: consultar las tarifas vigentes por nivel (Dueño o Administrador)."""
    return ok(TarifaSchema(many=True).dump(rate_service.list_rates()))


@bp.put("/<string:nivel>")
@require_permission("rate:edit")
def upsert_rate(nivel: str):
    """HU_59-60: fijar o actualizar la tarifa por hora de un nivel."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = TarifaUpsertSchema().load(payload)  # errores -> 422
    tarifa = rate_service.upsert_rate(g.current_user, nivel.upper(), data)
    return ok(tarifa.to_dict())
