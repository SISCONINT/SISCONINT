"""HU_25. Acceso a datos del catálogo de proyectos y actividades."""
from sqlalchemy import func, or_, select

from app.core.sql import escape_like
from app.extensions import db
from app.models.catalog import CategoriaProyecto


def list_categorias(q: str | None = None, solo_activas: bool = False) -> list[CategoriaProyecto]:
    """Devuelve las categorías raíz (padre_id IS NULL) con sus subcategorías cargadas.

    - Filtra deleted_at IS NULL.
    - Si solo_activas, exige activa=True en la categoría y en sus subcategorías.
    - q busca coincidencia parcial (sin distinguir mayúsculas) en el nombre de la categoría
      o de alguna de sus subcategorías; en ese caso devuelve la categoría raíz completa
      (con todas sus subcategorías activas/no eliminadas) para no romper el árbol.
    """
    stmt = (
        select(CategoriaProyecto)
        .where(
            CategoriaProyecto.padre_id.is_(None),
            CategoriaProyecto.deleted_at.is_(None),
        )
        .order_by(CategoriaProyecto.orden, func.lower(CategoriaProyecto.nombre), CategoriaProyecto.id)
    )
    if solo_activas:
        stmt = stmt.where(CategoriaProyecto.activa.is_(True))

    if q:
        pattern = f"%{escape_like(q)}%"
        # Coincide la categoría por su propio nombre...
        coincide_raiz = CategoriaProyecto.nombre.ilike(pattern, escape="\\")
        # ...o alguna de sus subcategorías no eliminadas (y activas, si solo_activas).
        sub = CategoriaProyecto.__table__.alias("sub")
        sub_cond = [
            sub.c.padre_id == CategoriaProyecto.id,
            sub.c.deleted_at.is_(None),
            sub.c.nombre.ilike(pattern, escape="\\"),
        ]
        if solo_activas:
            sub_cond.append(sub.c.activa.is_(True))
        coincide_sub = select(1).select_from(sub).where(*sub_cond).exists()
        stmt = stmt.where(or_(coincide_raiz, coincide_sub))

    raices = db.session.execute(stmt).scalars().all()

    # Carga las subcategorías en una sola consulta y respeta el filtro.
    if raices:
        ids = [c.id for c in raices]
        sub_stmt = (
            select(CategoriaProyecto)
            .where(
                CategoriaProyecto.padre_id.in_(ids),
                CategoriaProyecto.deleted_at.is_(None),
            )
            .order_by(CategoriaProyecto.orden, func.lower(CategoriaProyecto.nombre), CategoriaProyecto.id)
        )
        if solo_activas:
            sub_stmt = sub_stmt.where(CategoriaProyecto.activa.is_(True))
        for sub in db.session.execute(sub_stmt).scalars().all():
            sub.padre = next((c for c in raices if c.id == sub.padre_id), None)
            # SQLAlchemy llena la relación al asignar el objeto; lo anterior es solo por claridad.
    return raices


# ---------------------------------------------------------------------------
# HU_26-28: administración del catálogo
# ---------------------------------------------------------------------------
def get_by_id(categoria_id: int) -> CategoriaProyecto | None:
    """Categoría o subcategoría no eliminada."""
    stmt = select(CategoriaProyecto).where(
        CategoriaProyecto.id == categoria_id,
        CategoriaProyecto.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def nombre_existe(
    nombre: str, padre_id: int | None = None, exclude_id: int | None = None
) -> bool:
    """¿Ya hay una entrada no eliminada con ese nombre en el mismo nivel del árbol?

    La comparación no distingue mayúsculas para evitar duplicados como "IVA" e "iva".
    """
    stmt = select(CategoriaProyecto.id).where(
        CategoriaProyecto.deleted_at.is_(None),
        func.lower(CategoriaProyecto.nombre) == nombre.lower(),
    )
    if padre_id is None:
        stmt = stmt.where(CategoriaProyecto.padre_id.is_(None))
    else:
        stmt = stmt.where(CategoriaProyecto.padre_id == padre_id)
    if exclude_id is not None:
        stmt = stmt.where(CategoriaProyecto.id != exclude_id)
    return db.session.execute(stmt).first() is not None


def add(categoria: CategoriaProyecto) -> CategoriaProyecto:
    db.session.add(categoria)
    db.session.flush()
    return categoria


def deactivate_children(padre_id: int, cuando) -> int:
    """Desactiva en bloque las subcategorías de una categoría raíz (HU_28)."""
    from sqlalchemy import update

    result = db.session.execute(
        update(CategoriaProyecto)
        .where(
            CategoriaProyecto.padre_id == padre_id,
            CategoriaProyecto.deleted_at.is_(None),
            CategoriaProyecto.activa.is_(True),
        )
        .values(activa=False, updated_at=cuando)
    )
    return int(result.rowcount or 0)