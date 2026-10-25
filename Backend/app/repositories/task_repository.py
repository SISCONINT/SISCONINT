"""HU_29-33. Acceso a datos de tareas."""
from datetime import date, datetime

from sqlalchemy import func, or_, select, update
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
from app.models.task import (
    ESTADO_COMPLETADO,
    Comentario,
    HistorialEstadoTarea,
    Subtarea,
    Tarea,
)
from app.models.time_entry import RegistroTiempo
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


def get_rol_colaborador(colaborador_id: int | None) -> str | None:
    """Rol de un colaborador no eliminado (HU_32: permisos de edición del Contador)."""
    if colaborador_id is None:
        return None
    stmt = select(Colaborador.rol).where(
        Colaborador.id == colaborador_id, Colaborador.deleted_at.is_(None)
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
    """HU_30-31. Nombres relacionados para una o varias tareas, sin N+1.

    Devuelve {tarea_id: {"cliente_nombre", "categoria_nombre", "categoria_padre_nombre",
    "asignado_nombre", "creador_nombre", "completada_por_nombre"}}.
    """
    if not tarea_ids:
        return {}

    padre = aliased(CategoriaProyecto)
    creador = aliased(Colaborador)
    completada_por = aliased(Colaborador)
    stmt = (
        select(
            Tarea.id,
            Cliente.nombre_completo,
            CategoriaProyecto.nombre,
            padre.nombre,
            Colaborador.nombre_completo,
            creador.nombre_completo,
            completada_por.nombre_completo,
        )
        .select_from(Tarea)
        .outerjoin(Cliente, Cliente.id == Tarea.cliente_id)
        .outerjoin(CategoriaProyecto, CategoriaProyecto.id == Tarea.categoria_id)
        .outerjoin(padre, padre.id == CategoriaProyecto.padre_id)
        .outerjoin(Colaborador, Colaborador.id == Tarea.asignado_id)
        .outerjoin(creador, creador.id == Tarea.creador_id)
        .outerjoin(completada_por, completada_por.id == Tarea.completada_por)
        .where(Tarea.id.in_(tarea_ids))
    )

    return {
        tarea_id: {
            "cliente_nombre": cliente_nombre,
            "categoria_nombre": categoria_nombre,
            "categoria_padre_nombre": categoria_padre_nombre,
            "asignado_nombre": asignado_nombre,
            "creador_nombre": creador_nombre,
            "completada_por_nombre": completada_por_nombre,
        }
        for (
            tarea_id,
            cliente_nombre,
            categoria_nombre,
            categoria_padre_nombre,
            asignado_nombre,
            creador_nombre,
            completada_por_nombre,
        ) in db.session.execute(stmt).all()
    }


# ---------------------------------------------------------------------------
# HU_31: detalle de tarea
# ---------------------------------------------------------------------------
def get_by_id(tarea_id: int) -> Tarea | None:
    """Tarea no eliminada (el servicio aplica el alcance del Contador, RG-12)."""
    stmt = select(Tarea).where(Tarea.id == tarea_id, Tarea.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def list_subtareas(tarea_id: int) -> list[dict]:
    """Subtareas no eliminadas, en orden de creación (para el avance completadas/total)."""
    completada_por = aliased(Colaborador)
    stmt = (
        select(Subtarea, completada_por.nombre_completo)
        .outerjoin(completada_por, completada_por.id == Subtarea.completada_por)
        .where(Subtarea.tarea_id == tarea_id, Subtarea.deleted_at.is_(None))
        .order_by(Subtarea.created_at, Subtarea.id)
    )
    return [
        {
            "id": subtarea.id,
            "titulo": subtarea.titulo,
            "completada": subtarea.completada,
            "completada_por": subtarea.completada_por,
            "completada_por_nombre": completada_por_nombre,
            "completada_en": subtarea.completada_en,
            "created_at": subtarea.created_at,
        }
        for subtarea, completada_por_nombre in db.session.execute(stmt).all()
    ]


def list_comentarios(tarea_id: int) -> list[dict]:
    """Comentarios no eliminados, del más antiguo al más reciente."""
    stmt = (
        select(Comentario, Colaborador.nombre_completo)
        .outerjoin(Colaborador, Colaborador.id == Comentario.autor_id)
        .where(Comentario.tarea_id == tarea_id, Comentario.deleted_at.is_(None))
        .order_by(Comentario.created_at, Comentario.id)
    )
    return [
        {
            "id": comentario.id,
            "autor_id": comentario.autor_id,
            "autor_nombre": autor_nombre,
            "texto": comentario.texto,
            "editado": comentario.editado,
            "created_at": comentario.created_at,
            "updated_at": comentario.updated_at,
        }
        for comentario, autor_nombre in db.session.execute(stmt).all()
    ]


def list_historial_estados(tarea_id: int) -> list[dict]:
    """Historial de cambios de estado, del más antiguo al más reciente."""
    stmt = (
        select(HistorialEstadoTarea, Colaborador.nombre_completo)
        .outerjoin(Colaborador, Colaborador.id == HistorialEstadoTarea.usuario_id)
        .where(HistorialEstadoTarea.tarea_id == tarea_id)
        .order_by(HistorialEstadoTarea.created_at, HistorialEstadoTarea.id)
    )
    return [
        {
            "id": historial.id,
            "estado_anterior": historial.estado_anterior,
            "estado_nuevo": historial.estado_nuevo,
            "usuario_id": historial.usuario_id,
            "usuario_nombre": usuario_nombre,
            "created_at": historial.created_at,
        }
        for historial, usuario_nombre in db.session.execute(stmt).all()
    ]


def time_summary(tarea_id: int) -> list[dict]:
    """Tiempo registrado por colaborador (solo registros no eliminados)."""
    stmt = (
        select(
            RegistroTiempo.colaborador_id,
            Colaborador.nombre_completo,
            func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0),
        )
        .outerjoin(Colaborador, Colaborador.id == RegistroTiempo.colaborador_id)
        .where(
            RegistroTiempo.tarea_id == tarea_id,
            RegistroTiempo.deleted_at.is_(None),
        )
        .group_by(RegistroTiempo.colaborador_id, Colaborador.nombre_completo)
        .order_by(func.lower(Colaborador.nombre_completo), RegistroTiempo.colaborador_id)
    )
    return [
        {
            "colaborador_id": colaborador_id,
            "colaborador_nombre": colaborador_nombre,
            "minutos": int(minutos),
        }
        for colaborador_id, colaborador_nombre, minutos in db.session.execute(stmt).all()
    ]


# ---------------------------------------------------------------------------
# HU_33: eliminar tarea
# ---------------------------------------------------------------------------
def time_entries_summary(tarea_id: int) -> dict:
    """Registros de tiempo no eliminados de la tarea: cuántos son y cuánto suman.

    HU_33 solo permite eliminar tareas sin tiempo registrado, por eso el servicio
    necesita el conteo; los minutos se devuelven para que la interfaz explique el
    motivo sin consultar otra pantalla.
    """
    stmt = select(
        func.count(RegistroTiempo.id),
        func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0),
    ).where(
        RegistroTiempo.tarea_id == tarea_id,
        RegistroTiempo.deleted_at.is_(None),
    )
    registros, minutos = db.session.execute(stmt).one()
    return {"registros": int(registros), "minutos": int(minutos)}


def soft_delete(tarea: Tarea, actor_id: int, eliminado_en: datetime) -> dict:
    """RG-03: oculta la tarea y sus subtareas y comentarios sin borrar filas.

    Devuelve cuántas subtareas y comentarios se ocultaron, para la bitácora (RG-13).
    """
    valores = {"deleted_at": eliminado_en, "updated_by": actor_id}

    tarea.deleted_at = eliminado_en
    tarea.updated_by = actor_id

    subtareas = db.session.execute(
        update(Subtarea)
        .where(Subtarea.tarea_id == tarea.id, Subtarea.deleted_at.is_(None))
        .values(**valores)
    ).rowcount
    comentarios = db.session.execute(
        update(Comentario)
        .where(Comentario.tarea_id == tarea.id, Comentario.deleted_at.is_(None))
        .values(**valores)
    ).rowcount

    return {"subtareas": int(subtareas), "comentarios": int(comentarios)}


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
