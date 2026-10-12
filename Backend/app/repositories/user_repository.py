from sqlalchemy import func, select

from app.extensions import db
from app.models.auth_token import EnlaceActivacion
from app.models.user import ESTATUS_ACTIVO, Colaborador


def get_by_id(user_id: int) -> Colaborador | None:
    user = db.session.get(Colaborador, user_id)
    if user is None or user.deleted_at is not None:
        return None
    return user


def get_by_email(correo: str) -> Colaborador | None:
    return db.session.execute(
        select(Colaborador).where(
            func.lower(Colaborador.correo_institucional) == correo.lower(),
            Colaborador.deleted_at.is_(None),
        )
    ).scalar_one_or_none()


def email_exists(correo: str, exclude_id: int | None = None) -> bool:
    """Compara sin distinguir mayúsculas e incluye eliminados: el índice único de la base los cuenta."""
    stmt = select(Colaborador.id).where(func.lower(Colaborador.correo_institucional) == correo.lower())
    if exclude_id is not None:
        stmt = stmt.where(Colaborador.id != exclude_id)
    return db.session.execute(stmt.limit(1)).first() is not None


def count_active_with_role(rol: str) -> int:
    return db.session.scalar(
        select(func.count()).select_from(Colaborador).where(
            Colaborador.rol == rol,
            Colaborador.estatus == ESTATUS_ACTIVO,
            Colaborador.deleted_at.is_(None),
        )
    ) or 0


def add(user: Colaborador) -> Colaborador:
    db.session.add(user)
    db.session.flush()  # obtiene user.id sin confirmar
    return user


def add_activation_link(link: EnlaceActivacion) -> EnlaceActivacion:
    db.session.add(link)
    return link