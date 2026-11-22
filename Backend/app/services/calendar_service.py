"""Calendario de vencimientos de tareas."""
from datetime import date, timedelta

from app.core.datetime_utils import today_mx
from app.core.semaforo import calcular_semaforo
from app.models.user import ROL_CONTADOR
from app.repositories import calendar_repository

MSG_SIN_EVENTOS = "Sin vencimientos para el rango seleccionado"


def _mes_actual() -> tuple[date, date]:
    hoy = today_mx()
    desde = hoy.replace(day=1)
    siguiente = (desde.replace(day=28) + timedelta(days=4)).replace(day=1)
    return desde, siguiente - timedelta(days=1)


def get_calendar(actor, filtros: dict) -> dict:
    """Vencimientos del rango, con el alcance RG-12 del Contador."""
    default_desde, default_hasta = _mes_actual()
    desde = filtros.get("fecha_desde") or default_desde
    hasta = filtros.get("fecha_hasta") or default_hasta

    scope_usuario_id = actor.id if actor.rol == ROL_CONTADOR else None
    rows = calendar_repository.list_tasks(
        fecha_desde=desde,
        fecha_hasta=hasta,
        cliente_id=filtros.get("cliente"),
        colaborador_id=filtros.get("colaborador"),
        scope_usuario_id=scope_usuario_id,
    )

    hoy = today_mx()
    eventos = [
        {
            "id": row["id"],
            "tipo": "TAREA",
            "titulo": row["titulo"],
            "fecha": row["fecha"],
            "hora": row["hora"],
            "cliente_id": row["cliente_id"],
            "cliente_nombre": row["cliente_nombre"],
            "asignado_id": row["asignado_id"],
            "asignado_nombre": row["asignado_nombre"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "semaforo": calcular_semaforo(row["estado"], row["fecha"], hoy),
        }
        for row in rows
    ]

    por_dia: dict[str, int] = {}
    for evento in eventos:
        clave = evento["fecha"].isoformat()
        por_dia[clave] = por_dia.get(clave, 0) + 1

    return {
        "desde": desde,
        "hasta": hasta,
        "eventos": eventos,
        "total": len(eventos),
        "por_dia": por_dia,
        "mensaje": None if eventos else MSG_SIN_EVENTOS,
    }
