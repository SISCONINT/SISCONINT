from sqlalchemy import select

from app.core.pagination import PER_PAGE
from app.extensions import db
from app.models.minute import Minuta


def search(*, cliente_id: int | None, tarea_id: int | None, page: int):
    stmt = select(Minuta).where(Minuta.deleted_at.is_(None))
    if cliente_id:
        stmt = stmt.where(Minuta.cliente_id == cliente_id)
    if tarea_id:
        stmt = stmt.where(Minuta.tarea_id == tarea_id)
    stmt = stmt.order_by(Minuta.fecha_reunion.desc(), Minuta.id.desc())
    return db.paginate(stmt, page=page, per_page=PER_PAGE, max_per_page=PER_PAGE, error_out=False)


def get_by_id(minuta_id: int) -> Minuta | None:
    stmt = select(Minuta).where(Minuta.id == minuta_id, Minuta.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()
