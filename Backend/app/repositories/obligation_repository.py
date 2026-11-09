from sqlalchemy import select

from app.core.pagination import PER_PAGE
from app.extensions import db
from app.models.obligation import Obligacion


def search(*, cliente_id: int | None, solo_activas: bool, page: int):
    stmt = select(Obligacion).where(Obligacion.deleted_at.is_(None))
    if cliente_id:
        stmt = stmt.where(Obligacion.cliente_id == cliente_id)
    if solo_activas:
        stmt = stmt.where(Obligacion.activa.is_(True))
    stmt = stmt.order_by(Obligacion.dia_limite, Obligacion.nombre)
    return db.paginate(stmt, page=page, per_page=PER_PAGE, max_per_page=PER_PAGE, error_out=False)


def get_by_id(obligacion_id: int) -> Obligacion | None:
    stmt = select(Obligacion).where(Obligacion.id == obligacion_id, Obligacion.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()
