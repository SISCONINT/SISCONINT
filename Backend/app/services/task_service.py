"""HU_29. Lógica de negocio de tareas."""
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.extensions import db
from app.models.task import ESTADO_POR_HACER, Tarea
from app.repositories import task_repository


def create_task(actor, data: dict) -> Tarea:
    """HU_29. Crea una tarea en estado POR_HACER y notifica al asignado.

    Reglas:
      - El cliente debe existir y estar ACTIVO (no Pausado / Baja).
      - La categoría (o subcategoría) debe existir y estar activa.
      - El contador asignado debe ser un Contador Activo.
    """
    cliente = task_repository.get_cliente(data["cliente_id"])
    if cliente is None:
        raise NotFoundError("El cliente no existe", fields={"cliente_id": ["No existe"]})
    if cliente.estatus != "ACTIVO":
        raise ValidationAppError(
            "No se pueden crear tareas para clientes Pausados o en Baja",
            fields={"cliente_id": ["El cliente no está Activo"]},
        )

    categoria = task_repository.get_categoria(data["categoria_id"])
    if categoria is None:
        raise NotFoundError("La categoría no existe", fields={"categoria_id": ["No existe"]})
    if not categoria.activa:
        raise ValidationAppError(
            "La categoría está inactiva",
            fields={"categoria_id": ["Selecciona una categoría activa"]},
        )

    contador = task_repository.get_contador_activo(data["asignado_id"])
    if contador is None:
        raise ValidationAppError(
            "El contador asignado no es válido",
            fields={"asignado_id": ["Debe ser un Contador Activo"]},
        )

    tarea = Tarea(
        titulo=data["titulo"],
        descripcion=data.get("descripcion"),
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=contador.id,
        creador_id=actor.id,
        fecha_limite=data["fecha_limite"],
        hora_limite=data["hora_limite"],
        prioridad=data["prioridad"],
        estado=ESTADO_POR_HACER,
        horas_estimadas=data.get("horas_estimadas"),
        notificar_cliente=data.get("notificar_cliente", True),
        created_by=actor.id,
        updated_by=actor.id,
    )

    try:
        task_repository.add(tarea)
        task_repository.add_historial(
            tarea_id=tarea.id,
            estado_anterior=None,
            estado_nuevo=ESTADO_POR_HACER,
            usuario_id=actor.id,
        )

        audit.log(
            actor.id,
            entidad="tarea",
            entidad_id=tarea.id,
            accion=audit.CREAR,
            detalle={
                "titulo": tarea.titulo,
                "cliente_id": tarea.cliente_id,
                "asignado_id": tarea.asignado_id,
            },
        )

        _notificar_asignacion(tarea, actor)

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("No se pudo crear la tarea") from exc

    return tarea


def _notificar_asignacion(tarea: Tarea, actor) -> None:
    """HU_65: notificación in-app al contador asignado.

    No se envía si el asignado es el mismo que crea (criterio de HU_65).
    Por ahora sin correo (decisión D4 del MVP).
    """
    if tarea.asignado_id == actor.id:
        return

    from app.models.notification import Notificacion

    db.session.add(
        Notificacion(
            usuario_id=tarea.asignado_id,
            tipo="ASIGNACION",
            titulo="Nueva tarea asignada",
            mensaje=f"{tarea.titulo} — vence {tarea.fecha_limite.isoformat()}",
            entidad_tipo="TAREA",
            entidad_id=tarea.id,
        )
    )