"""HU_29-33, HU_41. Lógica de negocio de tareas."""
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.datetime_utils import today_mx, utcnow
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.pagination import PER_PAGE
from app.core.semaforo import calcular_semaforo, dias_restantes
from app.extensions import db
from app.models.notification import TIPO_CAMBIO_FECHA, TIPO_REASIGNACION, Notificacion
from app.models.task import (
    ESTADO_COMPLETADO,
    ESTADO_EN_PROGRESO,
    ESTADO_EN_REVISION,
    ESTADO_POR_HACER,
    Tarea,
)
from app.models.user import ROL_ADMINISTRADOR, ROL_CONTADOR, ROL_COORDINADOR
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


def get_task_detail(actor, tarea_id: int) -> dict:
    """HU_31. Detalle completo de una tarea y su contexto.

    Incluye todos los campos, creador, semáforo, subtareas con su avance,
    comentarios, historial de estados y tiempo registrado total y por colaborador
    frente a las horas estimadas. El Contador solo abre sus tareas (RG-12).
    """
    tarea = task_repository.get_by_id(tarea_id)
    if tarea is None:
        raise NotFoundError("Tarea no encontrada")

    _assert_can_view(actor, tarea)

    detalle = task_repository.details_for([tarea.id]).get(tarea.id, {})
    subtareas = task_repository.list_subtareas(tarea.id)
    comentarios = task_repository.list_comentarios(tarea.id)
    historial_estados = task_repository.list_historial_estados(tarea.id)
    por_colaborador = task_repository.time_summary(tarea.id)

    total_subtareas = len(subtareas)
    subtareas_completadas = sum(1 for subtarea in subtareas if subtarea["completada"])
    total_minutos = sum(item["minutos"] for item in por_colaborador)
    total_horas = round(total_minutos / 60, 2)
    horas_estimadas = (
        float(tarea.horas_estimadas) if tarea.horas_estimadas is not None else None
    )
    porcentaje_registrado = None
    if horas_estimadas is not None and horas_estimadas > 0:
        porcentaje_registrado = round(total_horas / horas_estimadas * 100, 1)

    hoy = today_mx()
    return {
        "id": tarea.id,
        "titulo": tarea.titulo,
        "descripcion": tarea.descripcion,
        "cliente_id": tarea.cliente_id,
        "cliente_nombre": detalle.get("cliente_nombre"),
        "categoria_id": tarea.categoria_id,
        "categoria_nombre": detalle.get("categoria_nombre"),
        "categoria_padre_nombre": detalle.get("categoria_padre_nombre"),
        "asignado_id": tarea.asignado_id,
        "asignado_nombre": detalle.get("asignado_nombre"),
        "creador_id": tarea.creador_id,
        "creador_nombre": detalle.get("creador_nombre"),
        "obligacion_id": tarea.obligacion_id,
        "periodo": tarea.periodo,
        "fecha_limite": tarea.fecha_limite,
        "hora_limite": tarea.hora_limite.strftime("%H:%M") if tarea.hora_limite else None,
        "prioridad": tarea.prioridad,
        "estado": tarea.estado,
        "horas_estimadas": horas_estimadas,
        "notificar_cliente": tarea.notificar_cliente,
        "cliente_notificado": tarea.cliente_notificado,
        "completada_en": tarea.completada_en,
        "completada_por": tarea.completada_por,
        "completada_por_nombre": detalle.get("completada_por_nombre"),
        "created_by": tarea.created_by,
        "updated_by": tarea.updated_by,
        "created_at": tarea.created_at,
        "updated_at": tarea.updated_at,
        "semaforo": calcular_semaforo(tarea.estado, tarea.fecha_limite, hoy),
        "dias_restantes": dias_restantes(tarea.fecha_limite, hoy),
        "subtareas": {
            "items": subtareas,
            "total": total_subtareas,
            "completadas": subtareas_completadas,
            "avance": f"{subtareas_completadas}/{total_subtareas}",
            "porcentaje": (
                round(subtareas_completadas * 100 / total_subtareas, 1)
                if total_subtareas
                else 0.0
            ),
        },
        "comentarios": comentarios,
        "historial_estados": historial_estados,
        "tiempo": {
            "total_minutos": total_minutos,
            "total_horas": total_horas,
            "horas_estimadas": horas_estimadas,
            "porcentaje_registrado": porcentaje_registrado,
            "por_colaborador": [
                {
                    "colaborador_id": item["colaborador_id"],
                    "colaborador_nombre": item["colaborador_nombre"],
                    "minutos": item["minutos"],
                    "horas": round(item["minutos"] / 60, 2),
                }
                for item in por_colaborador
            ],
        },
    }


# ---------------------------------------------------------------------------
# HU_32: edición de tarea
# ---------------------------------------------------------------------------
_CAMPOS_EDITABLES = (
    "titulo",
    "descripcion",
    "cliente_id",
    "categoria_id",
    "asignado_id",
    "fecha_limite",
    "hora_limite",
    "prioridad",
    "horas_estimadas",
    "notificar_cliente",
)

MSG_FECHA_PASADA = "La fecha límite debe ser hoy o posterior"
MSG_TAREA_DE_ADMINISTRACION = (
    "No puedes editar tareas creadas por Administración o Coordinación"
)
MSG_NO_ACTUALIZAR = "No se pudo actualizar la tarea"


def update_task(actor, tarea_id: int, data: dict) -> Tarea:
    """HU_32. Actualiza los datos de una tarea; el estado no se edita aquí.

    Solo se aplican los campos enviados. Las validaciones del alta se aplican a los
    valores que cambian: si un campo no cambia se conserva tal cual, para poder
    editar una tarea cuya fecha ya venció o cuyo cliente se pausó después del alta.

    Si cambia el contador asignado se notifica al nuevo y al anterior (el aviso de
    reasignación ya incluye la nueva fecha); si solo cambia la fecha límite se
    notifica al asignado. Los registros de tiempo ya hechos no se tocan: siguen
    atribuidos a quien los registró.
    """
    tarea = task_repository.get_by_id(tarea_id)
    if tarea is None:
        raise NotFoundError("Tarea no encontrada")

    _assert_can_edit(actor, tarea)

    cambios = {
        campo: data[campo]
        for campo in _CAMPOS_EDITABLES
        if campo in data and data[campo] != getattr(tarea, campo)
    }
    if not cambios:
        return tarea

    _validar_cambios(cambios)

    anteriores = {campo: getattr(tarea, campo) for campo in cambios}
    anterior_asignado_id = tarea.asignado_id
    anterior_fecha_limite = tarea.fecha_limite

    for campo, valor in cambios.items():
        setattr(tarea, campo, valor)
    tarea.updated_by = actor.id

    try:
        audit.log(
            actor.id,
            entidad="tarea",
            entidad_id=tarea.id,
            accion=audit.MODIFICAR,
            detalle={
                campo: {
                    "antes": _valor_auditable(anteriores[campo]),
                    "despues": _valor_auditable(valor),
                }
                for campo, valor in cambios.items()
            },
        )

        if "asignado_id" in cambios:
            _notificar_reasignacion(tarea, anterior_asignado_id, actor)
        elif "fecha_limite" in cambios:
            _notificar_cambio_fecha(tarea, anterior_fecha_limite, actor)

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_ACTUALIZAR) from exc

    return tarea


def _validar_cambios(cambios: dict) -> None:
    """Validaciones de HU_29 que dependen de la BD, aplicadas a los campos que cambian."""
    if "fecha_limite" in cambios and cambios["fecha_limite"] < today_mx():
        raise ValidationAppError(
            MSG_FECHA_PASADA, fields={"fecha_limite": [MSG_FECHA_PASADA]}
        )

    if "cliente_id" in cambios:
        cliente = task_repository.get_cliente(cambios["cliente_id"])
        if cliente is None:
            raise NotFoundError(
                "El cliente no existe", fields={"cliente_id": ["No existe"]}
            )
        if cliente.estatus != "ACTIVO":
            raise ValidationAppError(
                "No se pueden asignar tareas a clientes Pausados o en Baja",
                fields={"cliente_id": ["El cliente no está Activo"]},
            )

    if "categoria_id" in cambios:
        categoria = task_repository.get_categoria(cambios["categoria_id"])
        if categoria is None:
            raise NotFoundError(
                "La categoría no existe", fields={"categoria_id": ["No existe"]}
            )
        if not categoria.activa:
            raise ValidationAppError(
                "La categoría está inactiva",
                fields={"categoria_id": ["Selecciona una categoría activa"]},
            )

    if "asignado_id" in cambios:
        contador = task_repository.get_contador_activo(cambios["asignado_id"])
        if contador is None:
            raise ValidationAppError(
                "El contador asignado no es válido",
                fields={"asignado_id": ["Debe ser un Contador Activo"]},
            )


def _valor_auditable(valor):
    """Convierte fechas, horas y decimales a tipos que la bitácora guarda como JSON."""
    if isinstance(valor, (date, time)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def _assert_can_edit(actor, tarea: Tarea) -> None:
    """HU_32 + RG-12: el Contador solo edita las tareas que él creó.

    Primero se exige que pueda verla (si no, 403 genérico de RG-02, sin revelar
    datos del registro). Si la ve pero la creó Administración o Coordinación, HU_32
    pide el mensaje específico; para cualquier otro creador (Dueño u otro Contador)
    se responde el mensaje genérico.
    """
    if actor.rol != ROL_CONTADOR or tarea.creador_id == actor.id:
        return

    if tarea.asignado_id != actor.id:
        raise ForbiddenError()

    rol_creador = task_repository.get_rol_colaborador(tarea.creador_id)
    if rol_creador in (ROL_ADMINISTRADOR, ROL_COORDINADOR):
        raise ForbiddenError(MSG_TAREA_DE_ADMINISTRACION)

    raise ForbiddenError()


def _notificar_reasignacion(tarea: Tarea, anterior_id: int, actor) -> None:
    """HU_32: avisa al contador nuevo y al anterior (nunca al propio actor)."""
    if tarea.asignado_id != actor.id:
        db.session.add(
            Notificacion(
                usuario_id=tarea.asignado_id,
                tipo=TIPO_REASIGNACION,
                titulo="Tarea reasignada a ti",
                mensaje=f"{tarea.titulo} — vence {tarea.fecha_limite.isoformat()}",
                entidad_tipo="TAREA",
                entidad_id=tarea.id,
            )
        )

    if anterior_id != actor.id:
        db.session.add(
            Notificacion(
                usuario_id=anterior_id,
                tipo=TIPO_REASIGNACION,
                titulo="Tarea reasignada",
                mensaje=f"{tarea.titulo} ya no está asignada a ti",
                entidad_tipo="TAREA",
                entidad_id=tarea.id,
            )
        )


def _notificar_cambio_fecha(tarea: Tarea, anterior: date, actor) -> None:
    """HU_32: avisa al contador asignado que cambió la fecha límite."""
    if tarea.asignado_id == actor.id:
        return

    db.session.add(
        Notificacion(
            usuario_id=tarea.asignado_id,
            tipo=TIPO_CAMBIO_FECHA,
            titulo="Cambió la fecha límite",
            mensaje=(
                f"{tarea.titulo} — nueva fecha {tarea.fecha_limite.isoformat()} "
                f"(antes {anterior.isoformat()})"
            ),
            entidad_tipo="TAREA",
            entidad_id=tarea.id,
        )
    )


# ---------------------------------------------------------------------------
# HU_33: eliminar tarea
# ---------------------------------------------------------------------------
MSG_TAREA_CON_TIEMPO = "No se puede eliminar la tarea porque tiene tiempo registrado"
MSG_NO_ELIMINAR = "No se pudo eliminar la tarea"


def delete_task(actor, tarea_id: int) -> dict:
    """HU_33. Elimina lógicamente una tarea (RG-03) junto con sus subtareas y comentarios.

    Solo se eliminan tareas sin tiempo registrado; si lo tienen se responde 409 con
    el conteo y los minutos, y no se toca nada. El Contador solo elimina las tareas
    que él creó (RG-12); en cualquier otro caso recibe el 403 genérico de RG-02.

    RG-14: la confirmación explícita con el nombre de la tarea se pide en la
    interfaz; la API únicamente recibe el id y devuelve el nombre para el aviso.
    """
    tarea = task_repository.get_by_id(tarea_id)
    if tarea is None:
        raise NotFoundError("Tarea no encontrada")

    _assert_can_delete(actor, tarea)

    tiempo = task_repository.time_entries_summary(tarea.id)
    if tiempo["registros"]:
        raise ConflictError(
            MSG_TAREA_CON_TIEMPO,
            extra={
                "registros_tiempo": tiempo["registros"],
                "minutos_registrados": tiempo["minutos"],
            },
        )

    eliminado_en = utcnow()
    try:
        ocultos = task_repository.soft_delete(tarea, actor.id, eliminado_en)

        audit.log(
            actor.id,
            entidad="tarea",
            entidad_id=tarea.id,
            accion=audit.ELIMINAR,
            detalle={
                "titulo": tarea.titulo,
                "cliente_id": tarea.cliente_id,
                "subtareas_ocultas": ocultos["subtareas"],
                "comentarios_ocultos": ocultos["comentarios"],
            },
        )

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_ELIMINAR) from exc

    return {
        "id": tarea.id,
        "titulo": tarea.titulo,
        "eliminada_en": eliminado_en.isoformat(),
        "mensaje": "Tarea eliminada",
    }


def _assert_can_delete(actor, tarea: Tarea) -> None:
    """RG-12: el Contador solo elimina las tareas que él creó."""
    if actor.rol == ROL_CONTADOR and tarea.creador_id != actor.id:
        raise ForbiddenError()


def _assert_can_view(actor, tarea: Tarea) -> None:
    """RG-12: el Contador solo abre tareas asignadas a él o creadas por él."""
    if actor.rol != ROL_CONTADOR:
        return
    if tarea.asignado_id == actor.id or tarea.creador_id == actor.id:
        return
    raise ForbiddenError()


def _notificar_asignacion(tarea: Tarea, actor) -> None:
    """HU_65: notificación in-app al contador asignado.

    No se envía si el asignado es el mismo que crea (criterio de HU_65).
    Por ahora sin correo (decisión D4 del MVP).
    """
    if tarea.asignado_id == actor.id:
        return

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


# ---------------------------------------------------------------------------
# HU_41: tablero Kanban
# ---------------------------------------------------------------------------
DIAS_COMPLETADO_KANBAN = 30
COLUMNAS_KANBAN = (
    (ESTADO_POR_HACER, "Por hacer"),
    (ESTADO_EN_PROGRESO, "En progreso"),
    (ESTADO_EN_REVISION, "En revisión"),
    (ESTADO_COMPLETADO, "Completado"),
)


def get_kanban_board(actor) -> dict:
    """HU_41. Tablero Kanban con las cuatro columnas fijas y su contador de tareas.

    Dueño, Administrador y Coordinador ven todas las tareas; el Contador solo las
    asignadas a él o creadas por él (RG-12). La columna Completado solo incluye las
    tareas cerradas en los últimos 30 días (HU_41). El semáforo y el tiempo se
    calculan en el servidor.

    Dentro de las columnas abiertas las tarjetas van por fecha límite ascendente
    (lo más urgente primero); en Completado, por fecha de cierre descendente.
    """
    es_contador = actor.rol == ROL_CONTADOR
    tareas = task_repository.board_tasks(
        scope_usuario_id=actor.id if es_contador else None,
        completadas_desde=utcnow() - timedelta(days=DIAS_COMPLETADO_KANBAN),
    )

    detalles = task_repository.details_for([tarea.id for tarea in tareas])
    minutos = task_repository.time_totals_for([tarea.id for tarea in tareas])
    hoy = today_mx()

    por_estado: dict[str, list[Tarea]] = {estado: [] for estado, _ in COLUMNAS_KANBAN}
    for tarea in tareas:
        por_estado[tarea.estado].append(tarea)

    columnas = []
    for estado, titulo in COLUMNAS_KANBAN:
        grupo = por_estado[estado]
        if estado == ESTADO_COMPLETADO:
            grupo.sort(key=lambda tarea: (tarea.completada_en, tarea.id), reverse=True)

        tarjetas = [
            _kanban_card(tarea, detalles.get(tarea.id, {}), minutos.get(tarea.id, 0), hoy)
            for tarea in grupo
        ]
        columnas.append(
            {
                "estado": estado,
                "titulo": titulo,
                "total": len(tarjetas),
                "tareas": tarjetas,
            }
        )

    return {"columnas": columnas, "total_tareas": len(tareas)}


def _kanban_card(tarea: Tarea, detalle: dict, minutos: int, hoy: date) -> dict:
    """Tarjeta de HU_41: cliente, título, responsable, prioridad, semáforo y tiempo."""
    horas_registradas = round(minutos / 60, 2)
    horas_estimadas = (
        float(tarea.horas_estimadas) if tarea.horas_estimadas is not None else None
    )
    porcentaje_registrado = None
    if horas_estimadas:
        porcentaje_registrado = round(horas_registradas / horas_estimadas * 100, 1)

    return {
        "id": tarea.id,
        "titulo": tarea.titulo,
        "cliente_id": tarea.cliente_id,
        "cliente_nombre": detalle.get("cliente_nombre"),
        "asignado_id": tarea.asignado_id,
        "asignado_nombre": detalle.get("asignado_nombre"),
        "prioridad": tarea.prioridad,
        "estado": tarea.estado,
        "fecha_limite": tarea.fecha_limite,
        "hora_limite": tarea.hora_limite.strftime("%H:%M") if tarea.hora_limite else None,
        "semaforo": calcular_semaforo(tarea.estado, tarea.fecha_limite, hoy),
        "minutos_registrados": minutos,
        "horas_registradas": horas_registradas,
        "horas_estimadas": horas_estimadas,
        "porcentaje_registrado": porcentaje_registrado,
        "completada_en": tarea.completada_en,
    }
