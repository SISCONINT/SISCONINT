"""HU_25. Lógica de negocio del catálogo de proyectos y actividades (solo lectura)."""
from app.models.catalog import CategoriaProyecto
from app.repositories import catalog_repository


def list_categorias(q: str | None, solo_activas: bool) -> list[dict]:
    """Devuelve el árbol de categorías listo para serializar (categoría -> subcategorías)."""
    raices: list[CategoriaProyecto] = catalog_repository.list_categorias(q, solo_activas)
    return [c.to_dict(incluir_subcategorias=True) for c in raices]