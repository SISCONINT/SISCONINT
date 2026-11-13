"""Consultas adicionales de los reportes ejecutivos."""
from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models.task import ESTADO_COMPLETADO, Tarea


def count_completed_tasks(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
) -> int:
    """Tareas completadas dentro del periodo, con los filtros del reporte."""
    conds = [
        Tarea.deleted_at.is_(None),
        Tarea.estado == ESTADO_COMPLETADO,
        Tarea.completada_en.is_not(None),
        func.date(Tarea.completada_en) >= fecha_desde,
        func.date(Tarea.completada_en) <= fecha_hasta,
    ]
    if cliente_id is not None:
        conds.append(Tarea.cliente_id == cliente_id)
    if colaborador_id is not None:
        conds.append(Tarea.asignado_id == colaborador_id)

    stmt = select(func.count(Tarea.id)).where(*conds)
    return int(db.session.execute(stmt).scalar_one() or 0)
