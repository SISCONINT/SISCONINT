"""Módulo 4: Catálogo de proyectos y actividades. Prefijo /api/v1/catalog."""
from flask import Blueprint, request

from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.catalog_schema import CategoriaQuerySchema
from app.services import catalog_service

bp = Blueprint("catalog", __name__, url_prefix="/catalog")


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