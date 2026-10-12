from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func, or_, select

from app.extensions import db
from app.models.auth_token import EnlaceActivacion
from app.models.user import Colaborador


def get_by_email(correo: str) -> Colaborador | None:
    return db.session.execute(
        select(Colaborador).where(
            func.lower(Colaborador.correo_institucional) == correo.lower(),
            Colaborador.deleted_at.is_(None),
        )
    ).scalar_one_or_none()


def email_exists(correo: str) -> bool:
    """Compara sin distinguir mayúsculas e incluye eliminados: el índice único de la base los cuenta."""
    stmt = select(Colaborador.id).where(func.lower(Colaborador.correo_institucional) == correo.lower()).limit(1)
    return db.session.execute(stmt).first() is not None


def add(user: Colaborador) -> Colaborador:
    db.session.add(user)
    db.session.flush()  # obtiene user.id sin confirmar
    return user


def add_activation_link(link: EnlaceActivacion) -> EnlaceActivacion:
    db.session.add(link)
    return link

def _escape_like(text: str) -> str:
    """Para que %, _ y \\ escritos por el usuario se busquen como texto y no como comodines."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def search(q: str | None, rol: str | None, estatus: str, page: int, per_page: int) -> Pagination:
    """HU_06. Colaboradores no eliminados, ordenados alfabéticamente por nombre.

    q busca coincidencia parcial, sin distinguir mayúsculas, en nombre o correo.
    """
    stmt = select(Colaborador).where(Colaborador.deleted_at.is_(None), Colaborador.estatus == estatus)
    if rol:
        stmt = stmt.where(Colaborador.rol == rol)
    if q:
        pattern = f"%{_escape_like(q)}%"
        stmt = stmt.where(
            or_(
                Colaborador.nombre_completo.ilike(pattern, escape="\\"),
                Colaborador.correo_institucional.ilike(pattern, escape="\\"),
            )
        )
    stmt = stmt.order_by(func.lower(Colaborador.nombre_completo), Colaborador.id)  # id desempata: páginas estables
    return db.paginate(stmt, page=page, per_page=per_page, max_per_page=per_page, error_out=False)