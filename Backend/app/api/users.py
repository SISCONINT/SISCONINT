"""Módulo 2: Gestión de colaboradores. Prefijo /api/v1/users."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.user_list_schema import ColaboradorListItemSchema, ColaboradorListQuerySchema
from app.schemas.user_schema import ColaboradorCreateSchema, ColaboradorSchema
from app.services import email_service, user_service

bp = Blueprint("users", __name__, url_prefix="/users")


@bp.get("")
@require_permission("user:list")
def list_users():
    """HU_06: Consultar la lista de colaboradores (Dueño o Administrador).

    Parámetros opcionales: q (nombre o correo), rol, estatus (por defecto ACTIVO), page.
    """
    filters = ColaboradorListQuerySchema().load(request.args.to_dict())  # errores -> 422
    page = user_service.list_users(filters)
    return ok(ColaboradorListItemSchema(many=True).dump(page.items), meta=pagination_meta(page))


@bp.post("")
@require_permission("user:create")
def create_user():
    """HU_05: Registrar colaborador (Dueño o Administrador)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = ColaboradorCreateSchema().load(payload)  # RG-09 / RG-10; errores -> 422
    user, token = user_service.register_user(g.current_user, data)
    email_sent = email_service.send_activation_email(user, token)

    body = ColaboradorSchema().dump(user)
    body["correo_activacion_enviado"] = email_sent
    return ok(body, status=201)