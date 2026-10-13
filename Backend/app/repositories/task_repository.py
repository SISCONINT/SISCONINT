"""HU_29. Acceso a datos de tareas."""
from sqlalchemy import func, select

from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import ESTADO_COMPLETADO, HistorialEstadoTarea, Tarea
from app.models.user import ESTATUS_ACTIVO, ROL_CONTADOR, Colaborador


def get_cliente(cliente_id: int) -> Cliente | None:
    """Cliente no eliminado (cualquier estatus: el servicio decide si puede recibir tareas)."""
    stmt = select(Cliente).where(Cliente.id == cliente_id, Cliente.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def get_categoria(categoria_id: int) -> CategoriaProyecto | None:
    """Categoría o subcategoría no eliminada. El servicio exige que esté activa."""
    stmt = select(CategoriaProyecto).where(
        CategoriaProyecto.id == categoria_id, CategoriaProyecto.deleted_at.is_(None)
    )
    return db.session.execute(stmt).scalar_one_or_none()


def get_contador_activo(colaborador_id: int) -> Colaborador | None:
    """Colaborador Activo con rol CONTADOR, no eliminado."""
    stmt = select(Colaborador).where(
        Colaborador.id == colaborador_id,
        Colaborador.rol == ROL_CONTADOR,
        Colaborador.estatus == ESTATUS_ACTIVO,
        Colaborador.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def add(tarea: Tarea) -> Tarea:
    db.session.add(tarea)
    db.session.flush()
    return tarea


def add_historial(
    tarea_id: int,
    estado_anterior: str | None,
    estado_nuevo: str,
    usuario_id: int | None,
) -> HistorialEstadoTarea:
    h = HistorialEstadoTarea(
        tarea_id=tarea_id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario_id=usuario_id,
    )
    db.session.add(h)
    return h

# ---------------------------------------------------------------------------
# HU_09 (desactivar colaborador)
# ---------------------------------------------------------------------------
def _open_by_assignee_stmt(asignado_id: int):
    return select(Tarea).where(
        Tarea.asignado_id == asignado_id,
        Tarea.estado != ESTADO_COMPLETADO,
        Tarea.deleted_at.is_(None),
    )


def count_open_by_assignee(asignado_id: int) -> int:
    stmt = select(func.count()).select_from(_open_by_assignee_stmt(asignado_id).subquery())
    return db.session.scalar(stmt) or 0


def list_open_by_assignee(asignado_id: int) -> list[Tarea]:
    return list(db.session.execute(_open_by_assignee_stmt(asignado_id).order_by(Tarea.id)).scalars())
