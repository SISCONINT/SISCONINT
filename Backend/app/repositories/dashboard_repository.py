"""HU_79-85. Consultas agregadas del dashboard.

Todo el cálculo se hace en la base de datos: el servicio solo redondea y arma el
contrato. Los filtros de tiempo se comparten entre las tarjetas y las gráficas.
"""
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import ESTADO_COMPLETADO, ESTADOS, Tarea
from app.models.time_entry import RegistroTiempo
from app.models.user import Colaborador


# ---------------------------------------------------------------------------
# Filtros compartidos
# ---------------------------------------------------------------------------
def _time_conditions(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None,
    colaborador_id: int | None,
) -> list:
    """Condiciones de los registros de tiempo para el periodo y filtros activos."""
    conds = [
        RegistroTiempo.deleted_at.is_(None),
        RegistroTiempo.fecha >= fecha_desde,
        RegistroTiempo.fecha <= fecha_hasta,
    ]

    if colaborador_id is not None:
        conds.append(RegistroTiempo.colaborador_id == colaborador_id)

    if cliente_id is not None:
        tareas = select(Tarea.id).where(Tarea.cliente_id == cliente_id)
        conds.append(RegistroTiempo.tarea_id.in_(tareas))

    return conds


# ---------------------------------------------------------------------------
# Tiempo por periodo
# ---------------------------------------------------------------------------
def total_minutos(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
) -> int:
    """Minutos registrados en el periodo con los filtros aplicados (HU_79)."""
    conds = _time_conditions(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    stmt = select(func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0)).where(*conds)
    return int(db.session.execute(stmt).scalar_one())


def tiempo_por_empleado(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
) -> list[dict]:
    """Horas por empleado, de mayor a menor (HU_80)."""
    conds = _time_conditions(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    minutos = func.sum(RegistroTiempo.duracion_minutos)
    stmt = (
        select(
            Colaborador.id,
            Colaborador.nombre_completo,
            minutos.label("minutos"),
        )
        .select_from(RegistroTiempo)
        .join(Colaborador, Colaborador.id == RegistroTiempo.colaborador_id)
        .where(*conds)
        .group_by(Colaborador.id, Colaborador.nombre_completo)
        .order_by(minutos.desc(), Colaborador.nombre_completo)
    )
    return [
        {
            "colaborador_id": empleado_id,
            "nombre": nombre,
            "minutos": int(total),
        }
        for empleado_id, nombre, total in db.session.execute(stmt).all()
    ]


def tiempo_por_cliente(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
) -> list[dict]:
    """Horas por cliente, de mayor a menor (HU_81)."""
    conds = _time_conditions(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    minutos = func.sum(RegistroTiempo.duracion_minutos)
    stmt = (
        select(
            Cliente.id,
            Cliente.nombre_completo,
            minutos.label("minutos"),
        )
        .select_from(RegistroTiempo)
        .join(Tarea, Tarea.id == RegistroTiempo.tarea_id)
        .join(Cliente, Cliente.id == Tarea.cliente_id)
        .where(*conds)
        .group_by(Cliente.id, Cliente.nombre_completo)
        .order_by(minutos.desc(), Cliente.nombre_completo)
    )
    return [
        {
            "cliente_id": cliente_row_id,
            "nombre": nombre,
            "minutos": int(total),
        }
        for cliente_row_id, nombre, total in db.session.execute(stmt).all()
    ]


def tiempo_por_categoria(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
) -> list[dict]:
    """Horas por categoría raíz del catálogo, de mayor a menor (HU_82).

    Las tareas pueden clasificarse en una subcategoría; para que el reparto use las
    13 categorías del catálogo, la subcategoría se suma a su categoría padre.
    """
    conds = _time_conditions(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    hija = aliased(CategoriaProyecto)
    padre = aliased(CategoriaProyecto)
    categoria_id = func.coalesce(padre.id, hija.id)
    categoria_nombre = func.coalesce(padre.nombre, hija.nombre)
    minutos = func.sum(RegistroTiempo.duracion_minutos)

    stmt = (
        select(
            categoria_id.label("categoria_id"),
            categoria_nombre.label("nombre"),
            minutos.label("minutos"),
        )
        .select_from(RegistroTiempo)
        .join(Tarea, Tarea.id == RegistroTiempo.tarea_id)
        .join(hija, hija.id == Tarea.categoria_id)
        .outerjoin(padre, padre.id == hija.padre_id)
        .where(*conds)
        .group_by(categoria_id, categoria_nombre)
        .order_by(minutos.desc(), categoria_nombre)
    )
    return [
        {
            "categoria_id": categoria_id,
            "nombre": nombre,
            "minutos": int(total),
        }
        for categoria_id, nombre, total in db.session.execute(stmt).all()
    ]


# ---------------------------------------------------------------------------
# Tareas (foto actual, sin periodo)
# ---------------------------------------------------------------------------
def conteo_tareas(
    *,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
    hoy: date,
) -> dict[str, int]:
    """Conteo de tareas por estado y vencidas (HU_79, HU_83).

    Es una foto del estado actual: el periodo no aplica a las tareas, solo los
    filtros de cliente y colaborador. Se excluyen las tareas eliminadas.
    """
    conds = [Tarea.deleted_at.is_(None)]

    if cliente_id is not None:
        conds.append(Tarea.cliente_id == cliente_id)

    if colaborador_id is not None:
        conds.append(Tarea.asignado_id == colaborador_id)

    stmt = select(Tarea.estado, func.count(Tarea.id)).where(*conds).group_by(Tarea.estado)
    conteo = {estado: 0 for estado in ESTADOS}
    for estado, cantidad in db.session.execute(stmt).all():
        conteo[estado] = int(cantidad)

    vencidas_stmt = select(func.count(Tarea.id)).where(
        *conds,
        Tarea.estado != ESTADO_COMPLETADO,
        Tarea.fecha_limite < hoy,
    )
    conteo["vencidas"] = int(db.session.execute(vencidas_stmt).scalar_one())
    conteo["total"] = sum(conteo[estado] for estado in ESTADOS)
    return conteo


# ---------------------------------------------------------------------------
# Nombres de los filtros
# ---------------------------------------------------------------------------
def get_cliente_nombre(cliente_id: int | None) -> str | None:
    if cliente_id is None:
        return None
    stmt = select(Cliente.nombre_completo).where(Cliente.id == cliente_id)
    return db.session.execute(stmt).scalar_one_or_none()


def get_colaborador_nombre(colaborador_id: int | None) -> str | None:
    if colaborador_id is None:
        return None
    stmt = select(Colaborador.nombre_completo).where(Colaborador.id == colaborador_id)
    return db.session.execute(stmt).scalar_one_or_none()
