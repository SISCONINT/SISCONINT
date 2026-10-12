"""Módulo 2: Gestión de colaboradores. Prefijo /api/v1/users."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.user_schema import ColaboradorCreateSchema, ColaboradorSchema, ColaboradorUpdateSchema
from app.services import email_service, user_service

bp = Blueprint("users", __name__, url_prefix="/users")


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


@bp.get("/<int:user_id>")
@require_permission("user:view")
def get_user(user_id: int):
    """HU_08: ficha del colaborador (formulario precargado)."""
    user = user_service.get_user(user_id)
    return ok(ColaboradorSchema().dump(user))


@bp.put("/<int:user_id>")
@require_permission("user:edit")
def update_user(user_id: int):
    """HU_08: modificar colaborador, rol y grado escalafón."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = ColaboradorUpdateSchema().load(payload)
    user = user_service.update_user(g.current_user, user_id, data)
    return ok(ColaboradorSchema().dump(user))
