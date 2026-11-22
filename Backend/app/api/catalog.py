"""Módulo 4: Catálogo de proyectos y actividades. Prefijo /api/v1/catalog."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.catalog_schema import (
    CategoriaCreateSchema,
    CategoriaQuerySchema,
    CategoriaUpdateSchema,
)
from app.services import catalog_service

bp = Blueprint("catalog", __name__, url_prefix="/catalog")


def _payload() -> dict:
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")
    return payload


@bp.get("")
@require_permission("catalog:read")
def list_categories():
    """HU_25: Consultar catálogo de proyectos y actividades (los 4 roles).

    Devuelve el árbol categoría -> subcategorías con su estatus (Activa/Inactiva).
    Query params opcionales:
      - q: búsqueda parcial por nombre (categoría o subcategoría).
      - solo_activas=true: solo entradas activas.
    """
    filtros = CategoriaQuerySchema().load(request.args.to_dict())  # errores -> 422
    data = catalog_service.list_categorias(
        q=filtros.get("q"),
        solo_activas=filtros.get("solo_activas", False),
    )
    return ok(data)


@bp.post("")
@require_permission("catalog:manage")
def create_category():
    """HU_26: Registrar categoría o subcategoría (Dueño o Administrador)."""
    data = CategoriaCreateSchema().load(_payload())
    return ok(catalog_service.create_categoria(g.current_user, data), status=201)


@bp.put("/<int:categoria_id>")
@require_permission("catalog:manage")
def update_category(categoria_id: int):
    """HU_27: Editar nombre, orden o estatus de una entrada del catálogo."""
    data = CategoriaUpdateSchema().load(_payload())
    return ok(catalog_service.update_categoria(g.current_user, categoria_id, data))


@bp.post("/<int:categoria_id>/deactivate")
@require_permission("catalog:manage")
def deactivate_category(categoria_id: int):
    """HU_28: Desactivar una entrada del catálogo (cascada en categorías raíz)."""
    return ok(catalog_service.deactivate_categoria(g.current_user, categoria_id))
