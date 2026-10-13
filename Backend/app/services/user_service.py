"""Lógica de negocio de colaboradores. No conoce HTTP."""
from datetime import timedelta

from flask_sqlalchemy.pagination import Pagination   # junto a los imports de flask

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.pagination import PER_PAGE              # junto a los de app.core
from app.core.datetime_utils import utcnow
from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.core.permissions import ROL_DUENO, admin_may_edit, can_assign_role
from app.core.security import bump_user_generation, generate_token
from app.extensions import db
from app.models.auth_token import EnlaceActivacion
from app.models.user import ESTATUS_ACTIVO, ROL_ADMINISTRADOR, Colaborador
from app.repositories import user_repository

MSG_EMAIL_DUPLICATED = "El correo ya está registrado"
MSG_LAST_OWNER_ROLE = "No se puede cambiar el rol del último Dueño activo"
MSG_OWN_ROLE = "No puedes cambiar tu propio rol"
MSG_ASSIGN_ROLE = "No puedes asignar el rol seleccionado"

_EDITABLE_FIELDS = (
    "nombre_completo",
    "telefono_despacho",
    "correo_institucional",
    "rol",
    "grado_escalafon",
    "telefono_personal",
    "emergencia_nombre",
    "emergencia_telefono",
    "licenciatura",
    "cedula",
    "calle",
    "no_ext_int",
    "colonia",
    "municipio",
    "estado",
)


def register_user(actor: Colaborador, data: dict) -> tuple[Colaborador, str]:
    """HU_05. Crea el colaborador Activo y su enlace de activación.

    Devuelve (colaborador, token_en_claro). El token en claro solo existe aquí para armar el
    correo; en la base se guarda su hash.
    """
    # El Dueño asigna cualquier rol; el Administrador solo Coordinador o Contador.
    if not can_assign_role(actor.rol, data["rol"]):
        raise ForbiddenError(MSG_ASSIGN_ROLE)

    if user_repository.email_exists(data["correo_institucional"]):
        raise _duplicated_email()

    user = Colaborador(**data, estatus=ESTATUS_ACTIVO, created_by=actor.id, updated_by=actor.id)
    raw_token, token_hash = generate_token()
    hours = current_app.config["ACTIVATION_LINK_HOURS"]

    try:
        user_repository.add(user)
        user_repository.add_activation_link(
            EnlaceActivacion(colaborador_id=user.id, token_hash=token_hash, vence_en=utcnow() + timedelta(hours=hours))
        )
        audit.log(
            actor.id, "colaborador", user.id, audit.CREAR,
            {"rol": user.rol, "grado_escalafon": user.grado_escalafon, "correo_institucional": user.correo_institucional},
        )
        db.session.commit()
    except IntegrityError:
        # Carrera: otro registro con el mismo correo se confirmó entre la verificación y el INSERT.
        db.session.rollback()
        raise _duplicated_email()

    return user, raw_token

def list_users(filters: dict) -> Pagination:
    """HU_06. Página de colaboradores según los filtros ya validados (RG-07: 20 por página)."""
    return user_repository.search(
        q=filters.get("q"),
        rol=filters.get("rol"),
        estatus=filters["estatus"],
        page=filters["page"],
        per_page=PER_PAGE,
    )

def get_user(user_id: int) -> Colaborador:
    """HU_08: ficha para precargar el formulario. 404 si no existe o está eliminado."""
    user = user_repository.get_by_id(user_id)
    if user is None:
        raise NotFoundError("Colaborador no encontrado")
    return user


def update_user(actor: Colaborador, user_id: int, data: dict) -> Colaborador:
    """HU_08. Actualiza datos, rol y grado. No reescribe registros de tiempo históricos."""
    user = get_user(user_id)
    _assert_can_edit(actor, user)

    new_rol = data["rol"]
    if new_rol != user.rol:
        _assert_can_change_role(actor, user, new_rol)

    if user_repository.email_exists(data["correo_institucional"], exclude_id=user.id):
        raise _duplicated_email()

    before = {field: getattr(user, field) for field in _EDITABLE_FIELDS}
    role_changed = new_rol != user.rol

    for field in _EDITABLE_FIELDS:
        setattr(user, field, data[field])
    user.updated_by = actor.id

    changed = {
        field: {"antes": before[field], "despues": getattr(user, field)}
        for field in _EDITABLE_FIELDS
        if before[field] != getattr(user, field)
    }

    try:
        if role_changed:
            bump_user_generation(user.id, _session_revoke_ttl())
        if changed:
            audit.log(actor.id, "colaborador", user.id, audit.MODIFICAR, changed)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise _duplicated_email()

    return user


def _assert_can_edit(actor: Colaborador, target: Colaborador) -> None:
    if actor.rol == ROL_ADMINISTRADOR and not admin_may_edit(target.rol):
        raise ForbiddenError()


def _assert_can_change_role(actor: Colaborador, target: Colaborador, new_rol: str) -> None:
    if actor.id == target.id:
        raise ForbiddenError(MSG_OWN_ROLE)
    if not can_assign_role(actor.rol, new_rol):
        raise ForbiddenError(MSG_ASSIGN_ROLE)
    if target.rol == ROL_DUENO and target.estatus == ESTATUS_ACTIVO:
        if user_repository.count_active_with_role(ROL_DUENO) <= 1:
            raise ConflictError(MSG_LAST_OWNER_ROLE, fields={"rol": [MSG_LAST_OWNER_ROLE]})


def _session_revoke_ttl() -> int:
    access = int(current_app.config["JWT_ACCESS_TOKEN_EXPIRES"].total_seconds())
    refresh = int(current_app.config["JWT_REFRESH_TOKEN_EXPIRES"].total_seconds())
    return max(access, refresh) + 60


def _duplicated_email() -> ConflictError:
    return ConflictError(MSG_EMAIL_DUPLICATED, fields={"correo_institucional": [MSG_EMAIL_DUPLICATED]})
