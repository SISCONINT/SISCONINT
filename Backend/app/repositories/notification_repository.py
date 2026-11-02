"""HU_65-66, HU_71-73. Acceso a datos de la bandeja de notificaciones."""
from datetime import datetime

from sqlalchemy import delete, func, select, update

from app.extensions import db
from app.models.notification import Notificacion


def add(notificacion: Notificacion) -> Notificacion:
    db.session.add(notificacion)
    return notificacion


def list_for_user(
    usuario_id: int,
    *,
    leida: bool | None,
    desde: datetime,
    page: int,
    per_page: int,
):
    """HU_71. Página de notificaciones propias dentro de la retención de 90 días.

    Orden: más recientes primero. `leida=None` devuelve leídas y no leídas.
    """
    stmt = select(Notificacion).where(
        Notificacion.usuario_id == usuario_id,
        Notificacion.created_at >= desde,
    )
    if leida is not None:
        stmt = stmt.where(Notificacion.leida.is_(leida))

    stmt = stmt.order_by(Notificacion.created_at.desc(), Notificacion.id.desc())
    return db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=per_page,
        error_out=False,
    )


def count_unread(usuario_id: int, *, desde: datetime) -> int:
    """HU_71: contador del encabezado. No lo afecta el filtro leída/no leída."""
    stmt = select(func.count(Notificacion.id)).where(
        Notificacion.usuario_id == usuario_id,
        Notificacion.leida.is_(False),
        Notificacion.created_at >= desde,
    )
    return int(db.session.execute(stmt).scalar_one())


def get_for_user(notificacion_id: int, usuario_id: int) -> Notificacion | None:
    """HU_72: solo la notificación propia; la de otro usuario no existe para el actor."""
    stmt = select(Notificacion).where(
        Notificacion.id == notificacion_id,
        Notificacion.usuario_id == usuario_id,
    )
    return db.session.execute(stmt).scalar_one_or_none()


def mark_read(notificacion: Notificacion) -> None:
    notificacion.leida = True
    db.session.flush()


def mark_all_read(usuario_id: int, *, desde: datetime) -> int:
    """HU_73: marca todas las no leídas del usuario. Devuelve cuántas cambiaron."""
    stmt = (
        update(Notificacion)
        .where(
            Notificacion.usuario_id == usuario_id,
            Notificacion.leida.is_(False),
            Notificacion.created_at >= desde,
        )
        .values(leida=True)
    )
    return int(db.session.execute(stmt).rowcount or 0)


def exists_by_clave(clave_unica: str) -> bool:
    """HU_66: evita duplicar el recordatorio de la misma tarea y fecha límite."""
    stmt = select(Notificacion.id).where(Notificacion.clave_unica == clave_unica)
    return db.session.execute(stmt).first() is not None


def purge_older_than(corte: datetime) -> int:
    """HU_71: retención de 90 días. Devuelve las notificaciones eliminadas."""
    stmt = delete(Notificacion).where(Notificacion.created_at < corte)
    return int(db.session.execute(stmt).rowcount or 0)
