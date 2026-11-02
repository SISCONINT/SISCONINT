"""HU_65-66, HU_71-73. Bandeja de notificaciones in-app.

Las notificaciones son un log por usuario: no tienen soft delete ni edición. La
retención es de 90 días (HU_71); lo anterior deja de mostrarse y se purga con el
comando `flask purgar-notificaciones`.
"""
from datetime import date, datetime, timedelta

from app.core.datetime_utils import today_mx, utcnow
from app.core.errors import NotFoundError
from app.core.pagination import PER_PAGE
from app.extensions import db
from app.models.notification import TIPO_VENCIMIENTO, Notificacion
from app.repositories import notification_repository, task_repository

DIAS_RETENCION = 90

# Ruta del frontend para abrir la entidad relacionada (HU_71).
ENLACES = {
    "TAREA": "/tareas/{id}",
    "CLIENTE": "/clientes/{id}",
}


def list_inbox(actor, filtros: dict):
    """HU_71. Bandeja propia, más recientes primero, con contador de no leídas.

    El contador no lo afecta el filtro leída/no leída: siempre refleja el total de
    no leídas vigentes, que es lo que muestra el encabezado.
    """
    desde = _corte_retencion()
    page = notification_repository.list_for_user(
        actor.id,
        leida=filtros.get("leida"),
        desde=desde,
        page=filtros["page"],
        per_page=PER_PAGE,
    )
    no_leidas = notification_repository.count_unread(actor.id, desde=desde)
    return [_item(notificacion) for notificacion in page.items], page, no_leidas


def mark_read(actor, notificacion_id: int) -> dict:
    """HU_72. Marca como leída una notificación propia (idempotente).

    La de otro usuario responde 404: para el actor no existe. Marcar una ya leída
    vuelve a responder 200 sin cambiar nada.
    """
    notificacion = notification_repository.get_for_user(notificacion_id, actor.id)
    if notificacion is None:
        raise NotFoundError("Notificación no encontrada")

    if not notificacion.leida:
        notification_repository.mark_read(notificacion)
        db.session.commit()

    return {
        "notificacion": _item(notificacion),
        "no_leidas": notification_repository.count_unread(
            actor.id, desde=_corte_retencion()
        ),
    }


def mark_all_read(actor) -> dict:
    """HU_73. Marca todas las notificaciones propias como leídas."""
    actualizadas = notification_repository.mark_all_read(
        actor.id, desde=_corte_retencion()
    )
    db.session.commit()
    return {"actualizadas": actualizadas, "no_leidas": 0}


def notify_upcoming_deadlines(hoy=None) -> dict:
    """HU_66. Crea el recordatorio in-app de las tareas que vencen mañana.

    Se ejecuta todos los días a las 08:00 con `flask recordatorios-vencimiento`
    (el programador de tareas externo dispara el comando). Es idempotente por
    tarea y fecha límite gracias a `clave_unica`: correrlo dos veces el mismo día
    no duplica avisos.
    """
    hoy = hoy or today_mx()
    manana = hoy + timedelta(days=1)
    tareas = task_repository.tasks_due_on(manana)
    detalles = task_repository.details_for([tarea.id for tarea in tareas])

    creadas = 0
    for tarea in tareas:
        clave = _clave_vencimiento(tarea.id, manana)
        if notification_repository.exists_by_clave(clave):
            continue

        cliente = detalles.get(tarea.id, {}).get("cliente_nombre") or "Cliente"
        notification_repository.add(
            Notificacion(
                usuario_id=tarea.asignado_id,
                tipo=TIPO_VENCIMIENTO,
                titulo="Tarea próxima a vencer",
                mensaje=(
                    f"{tarea.titulo} — {cliente} — prioridad {tarea.prioridad} "
                    f"— vence mañana {manana.isoformat()}"
                ),
                entidad_tipo="TAREA",
                entidad_id=tarea.id,
                clave_unica=clave,
            )
        )
        creadas += 1

    db.session.commit()
    return {
        "fecha_limite": manana.isoformat(),
        "creadas": creadas,
        "omitidas": len(tareas) - creadas,
    }


def purge_expired() -> int:
    """HU_71. Elimina las notificaciones con más de 90 días de antigüedad."""
    eliminadas = notification_repository.purge_older_than(_corte_retencion())
    db.session.commit()
    return eliminadas


def _corte_retencion() -> datetime:
    return utcnow() - timedelta(days=DIAS_RETENCION)


def _clave_vencimiento(tarea_id: int, fecha_limite: date) -> str:
    return f"VENCIMIENTO:{tarea_id}:{fecha_limite.isoformat()}"


def _item(notificacion: Notificacion) -> dict:
    """Fila de la bandeja con el enlace que abre la tarea o el cliente (HU_71)."""
    return {
        "id": notificacion.id,
        "tipo": notificacion.tipo,
        "titulo": notificacion.titulo,
        "mensaje": notificacion.mensaje,
        "entidad_tipo": notificacion.entidad_tipo,
        "entidad_id": notificacion.entidad_id,
        "enlace": _enlace(notificacion.entidad_tipo, notificacion.entidad_id),
        "leida": notificacion.leida,
        "created_at": notificacion.created_at,
    }


def _enlace(entidad_tipo: str | None, entidad_id: int | None) -> str | None:
    plantilla = ENLACES.get(entidad_tipo or "")
    if plantilla is None or entidad_id is None:
        return None
    return plantilla.format(id=entidad_id)
