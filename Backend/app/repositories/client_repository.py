"""HU_11-12. Acceso a datos de clientes."""
from sqlalchemy import String, func, or_, select

from app.core.datetime_utils import today_mx
from app.models.access_grant import PermisoAtencionCliente
from app.models.task import Tarea
from app.models.time_entry import RegistroTiempo

from app.core.sql import escape_like
from app.extensions import db
from app.models.client import Cliente, ContactoCliente, RegimenFiscal
from app.models.user import ESTATUS_ACTIVO, ROL_CONTADOR, Colaborador


# ---------------------------------------------------------------------------
# HU_11
# ---------------------------------------------------------------------------
def find_by_rfc(rfc: str) -> Cliente | None:
    """Busca un cliente NO eliminado por RFC (comparación exacta, ya viene en mayúsculas)."""
    stmt = select(Cliente).where(Cliente.rfc == rfc, Cliente.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def get_contador_activo(contador_id: int) -> Colaborador | None:
    """Colaborador Activo con rol CONTADOR, no eliminado."""
    stmt = select(Colaborador).where(
        Colaborador.id == contador_id,
        Colaborador.rol == ROL_CONTADOR,
        Colaborador.estatus == ESTATUS_ACTIVO,
        Colaborador.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def regimenes_existen(claves: list[str]) -> set[str]:
    """Subconjunto de claves que SÍ existen y están activas en regimen_fiscal."""
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
    """HU_12. Listado paginado de clientes.

    `scope_contador_id`: si no es None, limita a los clientes asignados a ese Contador
    o con permiso de atención vigente (RG-12). El alcance lo decide el servicio,
    nunca el cliente de la API.
    """
    # --- subconsultas correlacionadas para las columnas calculadas ---
    contacto_principal = (
        select(ContactoCliente.correo)
        .where(
            ContactoCliente.cliente_id == Cliente.id,
            ContactoCliente.tipo == "PRINCIPAL",
            ContactoCliente.deleted_at.is_(None),
        )
        .limit(1)
        .scalar_subquery()
    )


    tareas_activas = (
        select(func.count(Tarea.id))
        .where(
            Tarea.cliente_id == Cliente.id,
            Tarea.estado != "COMPLETADO",
            Tarea.deleted_at.is_(None),
        )
        .scalar_subquery()
    )

    horas_registradas = (
        select(func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0) / 60.0)
        .where(
            RegistroTiempo.tarea_id.in_(
                select(Tarea.id).where(
                    Tarea.cliente_id == Cliente.id, Tarea.deleted_at.is_(None)
                )
            ),
            RegistroTiempo.deleted_at.is_(None),
        )
        .scalar_subquery()
    )

    stmt = select(
        Cliente,
        contacto_principal.label("contacto_principal_correo"),
        tareas_activas.label("tareas_activas"),
        horas_registradas.label("horas_registradas"),
    ).where(Cliente.deleted_at.is_(None))

    # --- filtros ---
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

    # --- orden estable ---
    stmt = stmt.order_by(func.lower(Cliente.nombre_completo), Cliente.id)

    # --- paginación: sobre la entidad Cliente ---
    return db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=per_page,
        error_out=False,
    )