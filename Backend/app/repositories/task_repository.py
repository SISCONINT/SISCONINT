"""HU_29-30. Acceso a datos de tareas."""
from datetime import date

from sqlalchemy import func, or_, select
from sqlalchemy.orm import aliased

from app.core.datetime_utils import today_mx
from app.core.semaforo import (
    SEMAFORO_AMARILLO,
    SEMAFORO_GRIS,
    SEMAFORO_VERDE,
    primer_dia_verde,
    rango_amarillo,
)
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
# HU_30: listado de tareas
# ---------------------------------------------------------------------------
def search(
    *,
    cliente_id: int | None,
    responsable_id: int | None,
    estado: str | None,
    prioridad: str | None,
    categoria_id: int | None,
    fecha_limite_desde: date | None,
    fecha_limite_hasta: date | None,
    semaforo: str | None,
    scope_usuario_id: int | None,
    page: int,
    per_page: int,
):
    """HU_30. Página de tareas no eliminadas con filtros y alcance del Contador (RG-12).

    Orden por defecto: fecha límite ascendente. Se desempata por hora y por id para
    que la paginación sea estable entre páginas.
    """
    stmt = select(Tarea).where(Tarea.deleted_at.is_(None))

    if cliente_id is not None:
        stmt = stmt.where(Tarea.cliente_id == cliente_id)

    if responsable_id is not None:
        stmt = stmt.where(Tarea.asignado_id == responsable_id)

    if estado is not None:
        stmt = stmt.where(Tarea.estado == estado)

    if prioridad is not None:
        stmt = stmt.where(Tarea.prioridad == prioridad)

    if categoria_id is not None:
        # El catálogo es un árbol de 2 niveles: al filtrar una categoría también
        # se incluyen las tareas clasificadas en sus subcategorías.
        subcategorias = select(CategoriaProyecto.id).where(
            CategoriaProyecto.padre_id == categoria_id,
            CategoriaProyecto.deleted_at.is_(None),
        )
        stmt = stmt.where(
            or_(
                Tarea.categoria_id == categoria_id,
                Tarea.categoria_id.in_(subcategorias),
            )
        )

    if fecha_limite_desde is not None:
        stmt = stmt.where(Tarea.fecha_limite >= fecha_limite_desde)

    if fecha_limite_hasta is not None:
        stmt = stmt.where(Tarea.fecha_limite <= fecha_limite_hasta)

    if semaforo is not None:
        stmt = _filtrar_semaforo(stmt, semaforo)

    # --- alcance del Contador (RG-12) ---
    if scope_usuario_id is not None:
        stmt = stmt.where(
            or_(
                Tarea.asignado_id == scope_usuario_id,
                Tarea.creador_id == scope_usuario_id,
            )
        )

    stmt = stmt.order_by(Tarea.fecha_limite, Tarea.hora_limite, Tarea.id)

    return db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=per_page,
        error_out=False,
    )


def _filtrar_semaforo(stmt, semaforo: str):
    """Traduce el color del semáforo (RG-11) a condiciones SQL portables.

    Se comparan fechas contra `today_mx()` en lugar de usar funciones de fecha del
    motor, para que funcione igual en PostgreSQL y SQLite.
    """
    if semaforo == SEMAFORO_GRIS:
        return stmt.where(Tarea.estado == ESTADO_COMPLETADO)

    # Cualquier otro color exige una tarea no completada.
    stmt = stmt.where(Tarea.estado != ESTADO_COMPLETADO)

    hoy = today_mx()
    if semaforo == SEMAFORO_VERDE:
        return stmt.where(Tarea.fecha_limite >= primer_dia_verde(hoy))

    if semaforo == SEMAFORO_AMARILLO:
        desde, hasta = rango_amarillo(hoy)
        return stmt.where(
            Tarea.fecha_limite >= desde,
            Tarea.fecha_limite <= hasta,
        )

    # ROJO: vence hoy o ya venció.
    return stmt.where(Tarea.fecha_limite <= hoy)


def details_for(tarea_ids: list[int]) -> dict[int, dict]:
    """HU_30. Nombres para las columnas del listado, sin N+1.

    Recibe los ids de una sola página (≤ 20) y devuelve
    {tarea_id: {"cliente_nombre", "categoria_nombre", "categoria_padre_nombre", "asignado_nombre"}}.
    """
    if not tarea_ids:
        return {}

    padre = aliased(CategoriaProyecto)
    stmt = (
        select(
            Tarea.id,
            Cliente.nombre_completo,
            CategoriaProyecto.nombre,
            padre.nombre,
            Colaborador.nombre_completo,
        )
        .select_from(Tarea)
        .outerjoin(Cliente, Cliente.id == Tarea.cliente_id)
        .outerjoin(CategoriaProyecto, CategoriaProyecto.id == Tarea.categoria_id)
        .outerjoin(padre, padre.id == CategoriaProyecto.padre_id)
        .outerjoin(Colaborador, Colaborador.id == Tarea.asignado_id)
        .where(Tarea.id.in_(tarea_ids))
    )

    return {
        tarea_id: {
            "cliente_nombre": cliente_nombre,
            "categoria_nombre": categoria_nombre,
            "categoria_padre_nombre": categoria_padre_nombre,
            "asignado_nombre": asignado_nombre,
        }
        for tarea_id, cliente_nombre, categoria_nombre, categoria_padre_nombre, asignado_nombre
        in db.session.execute(stmt).all()
    }

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
