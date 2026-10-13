"""Lógica de negocio de colaboradores. No conoce HTTP."""
from datetime import timedelta

from flask_sqlalchemy.pagination import Pagination   # junto a los imports de flask

from flask import current_app
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.pagination import PER_PAGE              # junto a los de app.core
from app.core.datetime_utils import utcnow
from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ReassignmentRequiredError,
    ValidationAppError,
)
from app.core.permissions import ROL_DUENO, admin_may_edit, can_assign_role
from app.core.security import bump_user_generation, generate_token
from app.extensions import db
from app.models.auth_token import EnlaceActivacion
from app.models.notification import TIPO_REASIGNACION, Notificacion
from app.models.user import ESTATUS_ACTIVO, ESTATUS_INACTIVO, ROL_ADMINISTRADOR, Colaborador
from app.repositories import client_repository, task_repository, user_repository

MSG_EMAIL_DUPLICATED = "El correo ya está registrado"
MSG_LAST_OWNER_ROLE = "No se puede cambiar el rol del último Dueño activo"
MSG_OWN_ROLE = "No puedes cambiar tu propio rol"
MSG_ASSIGN_ROLE = "No puedes asignar el rol seleccionado"
MSG_OWN_DEACTIVATE = "No puedes desactivar tu propia cuenta"
MSG_LAST_OWNER_DEACTIVATE = "No se puede desactivar al último Dueño activo"
MSG_ALREADY_INACTIVE = "El colaborador ya está inactivo"
MSG_REASSIGN_REQUIRED = "Elige un Contador o Coordinador activo para reasignar sus clientes y tareas abiertas"
MSG_REASSIGN_INVALID = "Debe ser un Contador o Coordinador activo distinto del colaborador a desactivar"
MOTIVO_DESACTIVACION = "Desactivación de colaborador"

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


def get_deactivation_impact(actor: Colaborador, user_id: int) -> dict:
    """HU_09. Qué tiene pendiente el colaborador y quién puede recibirlo (para armar la confirmación)."""
    user = get_user(user_id)
    _assert_can_deactivate(actor, user)

    clientes = client_repository.count_reassignable(user.id)
    tareas = task_repository.count_open_by_assignee(user.id)
    return {
        "colaborador_id": user.id,
        "clientes_asignados": clientes,
        "tareas_abiertas": tareas,
        "requiere_reasignacion": bool(clientes or tareas),
        "destinos": user_repository.list_reassign_targets(user.id),
    }


def deactivate_user(actor: Colaborador, user_id: int, reasignar_a: int | None = None) -> dict:
    """HU_09. Pasa al colaborador a Inactivo (RG-03: no se elimina) y cierra sus sesiones.

    Si tiene clientes Activos/Pausados o tareas sin completar, `reasignar_a` es obligatorio: un
    Contador o Coordinador Activo que los recibe en la misma transacción y es notificado.
    Sus tareas completadas, registros de tiempo y minutas no se tocan: siguen atribuidos a él.
    """
    user = get_user(user_id)
    _assert_can_deactivate(actor, user)

    clientes = client_repository.list_reassignable(user.id)
    tareas = task_repository.list_open_by_assignee(user.id)
    has_pending = bool(clientes or tareas)

    if reasignar_a is None and has_pending:
        raise ReassignmentRequiredError(
            MSG_REASSIGN_REQUIRED,
            fields={"reasignar_a": [MSG_REASSIGN_REQUIRED]},
            extra={"clientes_asignados": len(clientes), "tareas_abiertas": len(tareas)},
        )

    destino = None
    if reasignar_a is not None:
        destino = user_repository.get_reassign_target(reasignar_a, exclude_id=user.id)
        if destino is None:
            raise ValidationAppError(MSG_REASSIGN_INVALID, fields={"reasignar_a": [MSG_REASSIGN_INVALID]})

    moved_clientes = moved_tareas = 0
    if destino is not None and has_pending:
        for cliente in clientes:
            _reassign(actor, "cliente", cliente, "contador_asignado_id", destino.id)
        for tarea in tareas:
            _reassign(actor, "tarea", tarea, "asignado_id", destino.id)
        moved_clientes, moved_tareas = len(clientes), len(tareas)
        db.session.add(_reassignment_notification(user, destino, moved_clientes, moved_tareas))

    user.estatus = ESTATUS_INACTIVO
    user.updated_by = actor.id
    audit.log(
        actor.id, "colaborador", user.id, audit.ESTATUS,
        {
            "estatus": {"antes": ESTATUS_ACTIVO, "despues": ESTATUS_INACTIVO},
            "reasignado_a": destino.id if has_pending and destino else None,
            "clientes_reasignados": moved_clientes,
            "tareas_reasignadas": moved_tareas,
        },
    )
    db.session.commit()

    # Tras confirmar: si el commit falla no se cierran sesiones de una cuenta que sigue Activa.
    # La cuenta ya es inválida por su estatus; esto además tira de inmediato los tokens vigentes.
    bump_user_generation(user.id, _session_revoke_ttl())

    return {
        "colaborador": user,
        "reasignado_a": destino if has_pending else None,
        "clientes_reasignados": moved_clientes,
        "tareas_reasignadas": moved_tareas,
    }


def _assert_can_deactivate(actor: Colaborador, target: Colaborador) -> None:
    if actor.id == target.id:
        raise ForbiddenError(MSG_OWN_DEACTIVATE)
    _assert_can_edit(actor, target)
    if target.estatus != ESTATUS_ACTIVO:
        raise ConflictError(MSG_ALREADY_INACTIVE)
    if target.rol == ROL_DUENO and user_repository.count_active_with_role(ROL_DUENO) <= 1:
        raise ConflictError(MSG_LAST_OWNER_DEACTIVATE)


def _reassign(actor: Colaborador, entidad: str, record, field: str, new_id: int) -> None:
    before = getattr(record, field)
    setattr(record, field, new_id)
    record.updated_by = actor.id
    audit.log(
        actor.id, entidad, record.id, audit.MODIFICAR,
        {field: {"antes": before, "despues": new_id}, "motivo": MOTIVO_DESACTIVACION},
    )


def _reassignment_notification(origen: Colaborador, destino: Colaborador, clientes: int, tareas: int) -> Notificacion:
    parts = []
    if clientes:
        parts.append(f"{clientes} {'cliente' if clientes == 1 else 'clientes'}")
    if tareas:
        parts.append(f"{tareas} {'tarea' if tareas == 1 else 'tareas'}")
    return Notificacion(
        usuario_id=destino.id,
        tipo=TIPO_REASIGNACION,
        titulo="Se te reasignaron clientes y tareas",
        mensaje=f"Recibiste {' y '.join(parts)} de {origen.nombre_completo}, quien fue desactivado.",
    )


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
