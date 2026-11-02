"""Módulo 10: Notificaciones. Prefijo /api/v1/notifications. HU_71-73."""
from flask import Blueprint, g, request

from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.notificacion_schema import (
    NotificacionItemSchema,
    NotificacionLeidasTodasSchema,
    NotificacionLeidaSchema,
    NotificacionQuerySchema,
)
from app.services import notification_service

bp = Blueprint("notifications", __name__, url_prefix="/notifications")


@bp.get("")
@require_permission("notification:list")
def list_notifications():
    """HU_71: Consultar la bandeja de notificaciones propias (los 4 roles).

    Devuelve las notificaciones de los últimos 90 días, más recientes primero, y
    permite filtrar por leída / no leída. `meta.no_leidas` alimenta el contador del
    encabezado y no lo afecta el filtro. Paginación fija de 20 (RG-07).
    """
    filtros = NotificacionQuerySchema().load(request.args.to_dict())  # errores -> 422
    items, page, no_leidas = notification_service.list_inbox(g.current_user, filtros)
    meta = {**pagination_meta(page), "no_leidas": no_leidas}
    return ok(NotificacionItemSchema(many=True).dump(items), meta=meta)


@bp.patch("/<int:notificacion_id>/leida")
@require_permission("notification:read")
def mark_notification_read(notificacion_id: int):
    """HU_72: Marcar una notificación propia como leída.

    La interfaz llama a este endpoint al abrir la notificación o con la acción
    «Marcar como leída». Es idempotente y actualiza el contador de no leídas.
    """
    resultado = notification_service.mark_read(g.current_user, notificacion_id)
    return ok(NotificacionLeidaSchema().dump(resultado))


@bp.patch("/leidas")
@require_permission("notification:read-all")
def mark_all_notifications_read():
    """HU_73: Marcar todas las notificaciones propias como leídas.

    Solo afecta al usuario autenticado; al terminar el contador queda en 0.
    """
    resultado = notification_service.mark_all_read(g.current_user)
    return ok(NotificacionLeidasTodasSchema().dump(resultado))
