from flask_sqlalchemy.pagination import Pagination
from sqlalchemy import func, or_, select

from app.extensions import db
from app.models.auth_token import EnlaceActivacion
from app.models.user import ESTATUS_ACTIVO, ROL_CONTADOR, ROL_COORDINADOR, Colaborador


def get_by_id(user_id: int) -> Colaborador | None:
    user = db.session.get(Colaborador, user_id)
    if user is None or user.deleted_at is not None:
        return None
    return user


# def get_by_email(correo: str) -> Colaborador | None:
#     return db.session.execute(
#         select(Colaborador).where(
#             func.lower(Colaborador.correo_institucional) == correo.lower(),
#             Colaborador.deleted_at.is_(None),
#         )
#     ).scalar_one_or_none()

def get_by_email(correo: str) -> Colaborador | None:
    """Busca y retorna un colaborador por su correo institucional."""
    stmt = select(Colaborador).where(func.lower(Colaborador.correo_institucional) == correo.lower())
    return db.session.execute(stmt).scalar_one_or_none()


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


def _reassign_targets_stmt(exclude_id: int):
    """HU_09. Quién puede recibir clientes y tareas: Contador o Coordinador Activo."""
    return select(Colaborador).where(
        Colaborador.id != exclude_id,
        Colaborador.rol.in_((ROL_CONTADOR, ROL_COORDINADOR)),
        Colaborador.estatus == ESTATUS_ACTIVO,
        Colaborador.deleted_at.is_(None),
    )


def list_reassign_targets(exclude_id: int) -> list[Colaborador]:
    stmt = _reassign_targets_stmt(exclude_id).order_by(func.lower(Colaborador.nombre_completo), Colaborador.id)
    return list(db.session.execute(stmt).scalars())


def get_reassign_target(target_id: int, exclude_id: int) -> Colaborador | None:
    stmt = _reassign_targets_stmt(exclude_id).where(Colaborador.id == target_id)
    return db.session.execute(stmt).scalar_one_or_none()
