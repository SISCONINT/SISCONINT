import hashlib
from datetime import datetime
from sqlalchemy import func, select

from app.extensions import db
from app.models.auth_token import IntentoLogin, EnlaceActivacion
from app.models.user import Colaborador
from app.core.datetime_utils import utcnow


def add_attempt(correo: str, exitoso: bool, colaborador_id: int | None, ip: str | None) -> IntentoLogin:
    attempt = IntentoLogin(correo=correo, exitoso=exitoso, colaborador_id=colaborador_id, ip=ip)
    db.session.add(attempt)
    return attempt


def failure_streak(correo: str) -> tuple[int, datetime | None]:
    """Fallos consecutivos de un correo (desde su último inicio exitoso) y la fecha del último."""
    same_email = func.lower(IntentoLogin.correo) == correo.lower()

    last_ok = db.session.scalar(
        select(func.max(IntentoLogin.created_at)).where(same_email, IntentoLogin.exitoso.is_(True))
    )
    stmt = select(func.count(IntentoLogin.id), func.max(IntentoLogin.created_at)).where(
        same_email, IntentoLogin.exitoso.is_(False)
    )
    if last_ok is not None:
        stmt = stmt.where(IntentoLogin.created_at > last_ok)

    count, last_fail = db.session.execute(stmt).one()
    return count, last_fail

def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()

def get_valid_activation_link(token_hash: str) -> EnlaceActivacion | None:
    """Busca un enlace no usado y no vencido."""
    stmt = select(EnlaceActivacion).where(
        EnlaceActivacion.token_hash == token_hash,
        EnlaceActivacion.usado_en.is_(None),
        EnlaceActivacion.vence_en > utcnow(),
    )
    return db.session.execute(stmt).scalar_one_or_none()

def get_user_by_id(user_id: int) -> Colaborador | None:
    return db.session.get(Colaborador, user_id)