"""HU_11-12. Acceso a datos de clientes."""
from sqlalchemy import func, or_, select

from app.core.datetime_utils import today_mx
from app.core.sql import escape_like
from app.extensions import db
from app.models.access_grant import PermisoAtencionCliente
from app.models.client import Cliente, ContactoCliente, RegimenFiscal
from app.models.task import Tarea
from app.models.time_entry import RegistroTiempo
from app.models.user import ESTATUS_ACTIVO, ROL_CONTADOR, Colaborador


# ---------------------------------------------------------------------------
# HU_11
# ---------------------------------------------------------------------------
def find_by_rfc(rfc: str) -> Cliente | None:
    stmt = select(Cliente).where(Cliente.rfc == rfc, Cliente.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def get_contador_activo(contador_id: int) -> Colaborador | None:
    stmt = select(Colaborador).where(
        Colaborador.id == contador_id,
        Colaborador.rol == ROL_CONTADOR,
        Colaborador.estatus == ESTATUS_ACTIVO,
        Colaborador.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def regimenes_existen(claves: list[str]) -> set[str]:
    if not claves:
        return set()
    stmt = select(RegimenFiscal.clave).where(
        RegimenFiscal.clave.in_(claves), RegimenFiscal.activo.is_(True)
    )
    return {row[0] for row in db.session.execute(stmt).all()}


def add(cliente: Cliente) -> Cliente:
    db.session.add(cliente)
    db.session.flush()
    return cliente


# ---------------------------------------------------------------------------
# HU_12
# ---------------------------------------------------------------------------
def search(
    *,
    q: str | None,
    estatus: str,
    contador_id: int | None,
    tipo_persona: str | None,
    scope_contador_id: int | None = None,
    page: int,
    per_page: int,
):
    """HU_12. Paginación de la entidad Cliente + filtros y alcance del Contador.

    Devuelve el objeto Pagination; las columnas calculadas (contacto, tareas_activas,
    horas_registradas) se resuelven aparte en `indicators_for(cliente_ids)`.
    """
    stmt = select(Cliente).where(Cliente.deleted_at.is_(None))

    if estatus:
        stmt = stmt.where(Cliente.estatus == estatus)

    if contador_id is not None:
        stmt = stmt.where(Cliente.contador_asignado_id == contador_id)

    if tipo_persona:
        stmt = stmt.where(Cliente.tipo_persona == tipo_persona)

    if q:
        pattern = f"%{escape_like(q)}%"
        stmt = stmt.where(
            or_(
                Cliente.nombre_completo.ilike(pattern, escape="\\"),
                Cliente.razon_social.ilike(pattern, escape="\\"),
                Cliente.rfc.ilike(pattern, escape="\\"),
            )
        )

    # --- alcance del Contador (RG-12) ---
    if scope_contador_id is not None:
        hoy = today_mx()
        permiso_vigente = (
            select(PermisoAtencionCliente.id)
            .where(
                PermisoAtencionCliente.contador_id == scope_contador_id,
                PermisoAtencionCliente.cliente_id == Cliente.id,
                PermisoAtencionCliente.estatus == "VIGENTE",
                PermisoAtencionCliente.deleted_at.is_(None),
                PermisoAtencionCliente.fecha_inicio <= hoy,
                PermisoAtencionCliente.fecha_fin >= hoy,
            )
            .exists()
        )
        stmt = stmt.where(
            or_(
                Cliente.contador_asignado_id == scope_contador_id,
                permiso_vigente,
            )
        )

    stmt = stmt.order_by(func.lower(Cliente.nombre_completo), Cliente.id)

    return db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=per_page,
        error_out=False,
    )


def indicators_for(cliente_ids: list[int]) -> dict[int, dict]:
    """HU_12. Columnas calculadas para los clientes de la página.

    Devuelve {cliente_id: {"contacto_principal_correo", "tareas_activas", "horas_registradas"}}.
    Hace 3 consultas agregadas sobre ≤ per_page IDs (sin N+1).
    """
    if not cliente_ids:
        return {}

    # 1) Correo del contacto principal (uno por cliente; índice único parcial lo garantiza).
    contacto_rows = db.session.execute(
        select(ContactoCliente.cliente_id, ContactoCliente.correo).where(
            ContactoCliente.cliente_id.in_(cliente_ids),
            ContactoCliente.tipo == "PRINCIPAL",
            ContactoCliente.deleted_at.is_(None),
        )
    ).all()
    contactos = {cliente_id: correo for cliente_id, correo in contacto_rows}

    # 2) Tareas activas por cliente (no Completadas).
    tareas_rows = db.session.execute(
        select(Tarea.cliente_id, func.count(Tarea.id))
        .where(
            Tarea.cliente_id.in_(cliente_ids),
            Tarea.estado != "COMPLETADO",
            Tarea.deleted_at.is_(None),
        )
        .group_by(Tarea.cliente_id)
    ).all()
    tareas_activas = {cliente_id: int(total) for cliente_id, total in tareas_rows}

    # 3) Horas registradas por cliente (SUM(minutos) / 60, redondeado a 1 decimal).
    horas_rows = db.session.execute(
        select(
            Tarea.cliente_id,
            func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0),
        )
        .join(RegistroTiempo, RegistroTiempo.tarea_id == Tarea.id)
        .where(
            Tarea.cliente_id.in_(cliente_ids),
            Tarea.deleted_at.is_(None),
            RegistroTiempo.deleted_at.is_(None),
        )
        .group_by(Tarea.cliente_id)
    ).all()
    horas = {cliente_id: round(int(minutos) / 60.0, 1) for cliente_id, minutos in horas_rows}

    return {
        cid: {
            "contacto_principal_correo": contactos.get(cid),
            "tareas_activas": tareas_activas.get(cid, 0),
            "horas_registradas": horas.get(cid, 0.0),
        }
        for cid in cliente_ids
    }

# ---------------------------------------------------------------------------
# HU_09 (desactivar colaborador)
# ---------------------------------------------------------------------------
# Los clientes en Baja ya no se atienden: conservan al contador con el que cerraron su historial.
_REASSIGNABLE_STATUSES = ("ACTIVO", "PAUSADO")


def _reassignable_stmt(contador_id: int):
    return select(Cliente).where(
        Cliente.contador_asignado_id == contador_id,
        Cliente.deleted_at.is_(None),
        Cliente.estatus.in_(_REASSIGNABLE_STATUSES),
    )


def count_reassignable(contador_id: int) -> int:
    stmt = select(func.count()).select_from(_reassignable_stmt(contador_id).subquery())
    return db.session.scalar(stmt) or 0


def list_reassignable(contador_id: int) -> list[Cliente]:
    return list(db.session.execute(_reassignable_stmt(contador_id).order_by(Cliente.id)).scalars())
