"""HU_29-30. Lógica de negocio de tareas."""
from datetime import date

from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.datetime_utils import today_mx
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.core.pagination import PER_PAGE
from app.core.semaforo import calcular_semaforo, dias_restantes
from app.extensions import db
from app.models.task import ESTADO_POR_HACER, Tarea
from app.models.user import ROL_CONTADOR
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


def list_tasks(actor, filtros: dict):
    """HU_30. Listado paginado de tareas con filtros y alcance por rol (RG-12).

    Dueño, Administrador y Coordinador ven todas las tareas. El Contador solo las
    asignadas a él o creadas por él; por eso el filtro `responsable` se ignora para
    el Contador (no puede consultar tareas de otros responsables).

    Devuelve (items_listos_para_serializar, página) para conservar las reglas de
    negocio (semáforo y alcance) fuera de la ruta.
    """
    es_contador = actor.rol == ROL_CONTADOR
    responsable_id = None if es_contador else filtros.get("responsable")
    scope_usuario_id = actor.id if es_contador else None

    page = task_repository.search(
        cliente_id=filtros.get("cliente"),
        responsable_id=responsable_id,
        estado=filtros.get("estado"),
        prioridad=filtros.get("prioridad"),
        categoria_id=filtros.get("categoria"),
        fecha_limite_desde=filtros.get("fecha_limite_desde"),
        fecha_limite_hasta=filtros.get("fecha_limite_hasta"),
        semaforo=filtros.get("semaforo"),
        scope_usuario_id=scope_usuario_id,
        page=filtros["page"],
        per_page=PER_PAGE,
    )

    detalles = task_repository.details_for([tarea.id for tarea in page.items])
    hoy = today_mx()
    items = [
        _list_item(tarea, detalles.get(tarea.id, {}), hoy)
        for tarea in page.items
    ]
    return items, page


def _list_item(tarea: Tarea, detalle: dict, hoy: date) -> dict:
    """Columnas de HU_30: título, cliente, categoría, responsable, prioridad,
    estado, fecha límite y semáforo (calculado en el servidor)."""
    return {
        "id": tarea.id,
        "titulo": tarea.titulo,
        "cliente_id": tarea.cliente_id,
        "cliente_nombre": detalle.get("cliente_nombre"),
        "categoria_id": tarea.categoria_id,
        "categoria_nombre": detalle.get("categoria_nombre"),
        "categoria_padre_nombre": detalle.get("categoria_padre_nombre"),
        "asignado_id": tarea.asignado_id,
        "asignado_nombre": detalle.get("asignado_nombre"),
        "prioridad": tarea.prioridad,
        "estado": tarea.estado,
        "fecha_limite": tarea.fecha_limite,
        "hora_limite": tarea.hora_limite.strftime("%H:%M") if tarea.hora_limite else None,
        "semaforo": calcular_semaforo(tarea.estado, tarea.fecha_limite, hoy),
        "dias_restantes": dias_restantes(tarea.fecha_limite, hoy),
    }


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