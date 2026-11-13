"""Consultas de vencimientos para el calendario."""
from datetime import date

from sqlalchemy import or_, select
from sqlalchemy.orm import aliased

from app.extensions import db
from app.models.client import Cliente
from app.models.task import Tarea
from app.models.user import Colaborador


def list_tasks(
    *,
    fecha_desde: date,
    fecha_hasta: date,
    cliente_id: int | None = None,
    colaborador_id: int | None = None,
    scope_usuario_id: int | None = None,
) -> list[dict]:
    """Tareas con fecha límite dentro del rango y sus nombres resueltos."""
    asignado = aliased(Colaborador)
    stmt = (
        select(
            Tarea.id,
            Tarea.titulo,
            Tarea.fecha_limite,
            Tarea.hora_limite,
            Tarea.cliente_id,
            Cliente.nombre_completo,
            Tarea.asignado_id,
            asignado.nombre_completo,
            Tarea.estado,
            Tarea.prioridad,
        )
        .select_from(Tarea)
        .join(Cliente, Cliente.id == Tarea.cliente_id)
        .join(asignado, asignado.id == Tarea.asignado_id)
        .where(
            Tarea.deleted_at.is_(None),
            Tarea.fecha_limite >= fecha_desde,
            Tarea.fecha_limite <= fecha_hasta,
        )
    )

    if cliente_id is not None:
        stmt = stmt.where(Tarea.cliente_id == cliente_id)
    if colaborador_id is not None:
        stmt = stmt.where(Tarea.asignado_id == colaborador_id)
    if scope_usuario_id is not None:
        stmt = stmt.where(
            or_(Tarea.asignado_id == scope_usuario_id, Tarea.creador_id == scope_usuario_id)
        )

    stmt = stmt.order_by(Tarea.fecha_limite, Tarea.hora_limite, Tarea.id)
    return [
        {
            "id": tarea_id,
            "titulo": titulo,
            "fecha": fecha_limite,
            "hora": hora_limite.strftime("%H:%M") if hora_limite else None,
            "cliente_id": cliente_row_id,
            "cliente_nombre": cliente_nombre,
            "asignado_id": asignado_id,
            "asignado_nombre": asignado_nombre,
            "estado": estado,
            "prioridad": prioridad,
        }
        for (
            tarea_id,
            titulo,
            fecha_limite,
            hora_limite,
            cliente_row_id,
            cliente_nombre,
            asignado_id,
            asignado_nombre,
            estado,
            prioridad,
        ) in db.session.execute(stmt).all()
    ]
