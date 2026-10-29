"""HU_49-53. Lógica de negocio del registro de tiempos (módulo 8)."""
from datetime import date, datetime, time, timedelta

from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.datetime_utils import TZ_MX, as_utc, today_mx, utcnow
from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationAppError,
)
from app.core.pagination import PER_PAGE, pagination_meta
from app.extensions import db
from app.models.notification import TIPO_CIERRE_AUTOMATICO, Notificacion
from app.models.task import ESTADO_COMPLETADO
from app.models.time_entry import TIPO_MANUAL, TIPO_TIMER, RegistroTiempo, TemporizadorActivo
from app.models.user import ROL_ADMINISTRADOR, ROL_CONTADOR, ROL_DUENO, Colaborador
from app.repositories import task_repository, time_repository

MINUTOS_POR_DIA = 24 * 60

MSG_TAREA_NO_ASIGNADA = "Solo puedes registrar tiempo en tareas asignadas a ti"
MSG_TAREA_COMPLETADA = "No se puede iniciar el temporizador en una tarea Completada"
MSG_TIMER_ACTIVO = "Tienes un temporizador activo. Deténlo y guárdalo antes de iniciar otro"
MSG_SIN_TIMER = "No tienes un temporizador activo"
MSG_TIMER_NO_COINCIDE = "El temporizador indicado no está activo"
MSG_MENOS_DE_UN_MINUTO = "El tiempo registrado fue menor a 1 minuto y no se guardó"
MSG_CIERRE_AUTOMATICO = "El temporizador se cerró automáticamente a las 23:59 y el tiempo quedó guardado"
MSG_CIERRE_DESCARTADO = (
    "El temporizador se cerró automáticamente a las 23:59, pero duró menos de 1 minuto y no se guardó"
)
MSG_FUERA_PLAZO = (
    "Solo puedes registrar tiempo de hoy; para una fecha anterior se requiere un permiso vigente"
)
MSG_FUERA_PLAZO_EDICION = (
    "Solo puedes editar tus registros del mismo día; "
    "para otro día se requiere un permiso vigente"
)
MSG_LIMITE_DIARIO = "El total del día no puede superar 24 horas"
MSG_TOTAL_CERO = "El total de horas y minutos debe ser mayor a 0"
MSG_FECHA_FUTURA = "No se aceptan fechas futuras"
MSG_REGISTRO_NO_ENCONTRADO = "Registro de tiempo no encontrado"
MSG_NO_GUARDAR = "No se pudo guardar el registro de tiempo"


# ---------------------------------------------------------------------------
# Utilidades de tiempo (RG-04)
# ---------------------------------------------------------------------------
def _a_mx(valor: datetime) -> datetime:
    return as_utc(valor).astimezone(TZ_MX)


def _segundos_transcurridos(iniciado_en: datetime) -> int:
    return max(0, int((utcnow() - as_utc(iniciado_en)).total_seconds()))


def _minutos_redondeados(segundos: int) -> int | None:
    """HU_50: redondeo al minuto más cercano; menos de 1 minuto se descarta."""
    if segundos < 60:
        return None
    return (segundos + 30) // 60


def _hhmmss(segundos: int) -> str:
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"


def _valor_auditable(valor):
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    return valor


# ---------------------------------------------------------------------------
# Validaciones compartidas
# ---------------------------------------------------------------------------
def _tarea_para(colaborador_id: int, tarea_id: int, *, exigir_no_completada: bool = False):
    """La tarea debe existir y estar asignada al colaborador dueño del tiempo."""
    tarea = task_repository.get_by_id(tarea_id)
    if tarea is None:
        raise NotFoundError("La tarea no existe", fields={"tarea_id": ["No existe"]})

    if tarea.asignado_id != colaborador_id:
        raise ForbiddenError(
            MSG_TAREA_NO_ASIGNADA, fields={"tarea_id": [MSG_TAREA_NO_ASIGNADA]}
        )

    if exigir_no_completada and tarea.estado == ESTADO_COMPLETADO:
        raise ValidationAppError(
            MSG_TAREA_COMPLETADA, fields={"tarea_id": [MSG_TAREA_COMPLETADA]}
        )

    return tarea


def _assert_limite_diario(
    colaborador_id: int,
    fecha: date,
    minutos: int,
    exclude_id: int | None = None,
) -> None:
    """HU_51: máximo 24 horas por usuario en un mismo día."""
    registrados = time_repository.sum_minutes_for_day(colaborador_id, fecha, exclude_id)
    if registrados + minutos > MINUTOS_POR_DIA:
        raise ValidationAppError(
            MSG_LIMITE_DIARIO,
            fields={"minutos": [MSG_LIMITE_DIARIO]},
            extra={
                "minutos_registrados": registrados,
                "minutos_disponibles": max(0, MINUTOS_POR_DIA - registrados),
            },
        )


# ---------------------------------------------------------------------------
# HU_49: iniciar temporizador
# ---------------------------------------------------------------------------
def start_timer(actor: Colaborador, tarea_id: int) -> dict:
    """HU_49. Inicia el cronómetro de una tarea asignada y no Completada.

    Cada colaborador tiene un solo temporizador. Si ya hay uno activo se responde 409
    con sus datos para que la interfaz pida detenerlo y guardarlo. La hora de inicio
    se guarda en el servidor (UTC), así el conteo sigue aunque se recargue la página.
    """
    tarea = _tarea_para(actor.id, tarea_id, exigir_no_completada=True)

    # Si quedó un temporizador de un día anterior, primero se cierra (HU_50).
    _cerrar_temporizador_vencido(actor)

    activo = time_repository.get_active_for_user(actor.id)
    if activo is not None:
        detalle = time_repository.get_timer_detail(activo.id)
        raise ConflictError(
            MSG_TIMER_ACTIVO,
            extra={"temporizador": _timer_payload(detalle) if detalle else None},
        )

    temporizador = TemporizadorActivo(
        colaborador_id=actor.id,
        tarea_id=tarea.id,
        iniciado_en=utcnow(),
    )

    try:
        time_repository.add_timer(temporizador)
        audit.log(
            actor.id,
            entidad="temporizador_activo",
            entidad_id=temporizador.id,
            accion=audit.CREAR,
            detalle={"tarea_id": tarea.id},
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_TIMER_ACTIVO) from exc

    detalle = time_repository.get_timer_detail(temporizador.id)
    return _timer_payload(detalle)


def get_timer_state(actor: Colaborador) -> dict:
    """HU_49-50. Estado del temporizador al abrir o recargar la pantalla.

    Si el temporizador quedó activo de un día anterior se cierra aquí y se devuelve
    el aviso de cierre automático (HU_50).
    """
    aviso = _cerrar_temporizador_vencido(actor)
    activo = time_repository.get_active_for_user(actor.id)
    detalle = time_repository.get_timer_detail(activo.id) if activo is not None else None

    return {
        "activo": _timer_payload(detalle) if detalle is not None else None,
        "aviso_cierre_automatico": aviso,
    }


def _timer_payload(detalle: dict) -> dict:
    segundos = _segundos_transcurridos(detalle["iniciado_en"])
    return {
        **detalle,
        "iniciado_en": as_utc(detalle["iniciado_en"]),
        "transcurrido_segundos": segundos,
        "transcurrido": _hhmmss(segundos),
    }


# ---------------------------------------------------------------------------
# HU_50: detener temporizador y guardar
# ---------------------------------------------------------------------------
def stop_timer(actor: Colaborador, data: dict) -> dict:
    """HU_50. Detiene el cronómetro, redondea al minuto y guarda el registro Timer.

    Si el cronómetro duró menos de un minuto se descarta y se avisa. Si había quedado
    activo de un día anterior, se cierra automáticamente a las 23:59.
    """
    cerrado = _cerrar_temporizador_vencido(actor)
    if cerrado is not None:
        return cerrado

    temporizador = time_repository.get_active_for_user(actor.id, for_update=True)
    if temporizador is None:
        raise NotFoundError(MSG_SIN_TIMER)

    if (
        data.get("temporizador_id") is not None
        and data["temporizador_id"] != temporizador.id
    ):
        raise ConflictError(MSG_TIMER_NO_COINCIDE)

    segundos = _segundos_transcurridos(temporizador.iniciado_en)
    minutos = _minutos_redondeados(segundos)
    fecha = _a_mx(temporizador.iniciado_en).date()

    time_repository.delete_timer(temporizador)

    if minutos is None:
        audit.log(
            actor.id,
            entidad="temporizador_activo",
            entidad_id=temporizador.id,
            accion=audit.ELIMINAR,
            detalle={"motivo": "menos de un minuto", "segundos": segundos},
        )
        db.session.commit()
        return {
            "guardado": False,
            "descartado": True,
            "cierre_automatico": False,
            "mensaje": MSG_MENOS_DE_UN_MINUTO,
            "segundos": segundos,
            "registro": None,
        }

    registro = RegistroTiempo(
        tarea_id=temporizador.tarea_id,
        colaborador_id=actor.id,
        fecha=fecha,
        duracion_minutos=minutos,
        tipo=TIPO_TIMER,
        descripcion=data["descripcion"],
        nivel_escalafon=actor.grado_escalafon,
        cierre_automatico=False,
        created_by=actor.id,
    )

    try:
        time_repository.add_registro(registro)
        audit.log(
            actor.id,
            entidad="registro_tiempo",
            entidad_id=registro.id,
            accion=audit.CREAR,
            detalle={
                "tarea_id": registro.tarea_id,
                "fecha": fecha.isoformat(),
                "duracion_minutos": minutos,
                "tipo": TIPO_TIMER,
            },
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_GUARDAR) from exc

    return _resultado_guardado(
        registro, "Registro de tiempo guardado", segundos=segundos
    )


def _cerrar_temporizador_vencido(actor: Colaborador) -> dict | None:
    """HU_50. Cierra a las 23:59 el temporizador que quedó activo de un día anterior.

    Devuelve el resultado del guardado (o del descarte) o None si no había nada que
    cerrar. También deja una notificación para avisar al usuario al volver a entrar.
    """
    temporizador = time_repository.get_active_for_user(actor.id, for_update=True)
    if temporizador is None:
        return None

    inicio_mx = _a_mx(temporizador.iniciado_en)
    fecha = inicio_mx.date()
    if fecha >= today_mx():
        return None

    fin_mx = datetime.combine(fecha, time(23, 59, 59), tzinfo=TZ_MX)
    segundos = max(0, int((fin_mx - inicio_mx).total_seconds()))
    minutos = _minutos_redondeados(segundos)

    registro = None
    if minutos is not None:
        registro = RegistroTiempo(
            tarea_id=temporizador.tarea_id,
            colaborador_id=actor.id,
            fecha=fecha,
            duracion_minutos=minutos,
            tipo=TIPO_TIMER,
            descripcion="Cierre automático",
            nivel_escalafon=actor.grado_escalafon,
            cierre_automatico=True,
            created_by=actor.id,
        )
        time_repository.add_registro(registro)
        audit.log(
            actor.id,
            entidad="registro_tiempo",
            entidad_id=registro.id,
            accion=audit.CREAR,
            detalle={
                "tarea_id": registro.tarea_id,
                "fecha": fecha.isoformat(),
                "duracion_minutos": minutos,
                "tipo": TIPO_TIMER,
                "cierre_automatico": True,
            },
        )

    time_repository.delete_timer(temporizador)
    db.session.add(
        Notificacion(
            usuario_id=actor.id,
            tipo=TIPO_CIERRE_AUTOMATICO,
            titulo="Temporizador cerrado automáticamente",
            mensaje=(
                f"Se cerró el temporizador de la tarea al final del día {fecha.isoformat()}"
                if registro is not None
                else f"El temporizador del día {fecha.isoformat()} duró menos de 1 minuto "
                "y no se guardó"
            ),
            entidad_tipo="TIEMPO",
            entidad_id=registro.id if registro is not None else None,
        )
    )

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_GUARDAR) from exc

    if registro is None:
        return {
            "guardado": False,
            "descartado": True,
            "cierre_automatico": True,
            "mensaje": MSG_CIERRE_DESCARTADO,
            "segundos": segundos,
            "registro": None,
        }

    return _resultado_guardado(
        registro, MSG_CIERRE_AUTOMATICO, cierre_automatico=True, segundos=segundos
    )


def _resultado_guardado(
    registro: RegistroTiempo,
    mensaje: str,
    *,
    cierre_automatico: bool = False,
    segundos: int | None = None,
) -> dict:
    return {
        "guardado": True,
        "descartado": False,
        "cierre_automatico": cierre_automatico,
        "mensaje": mensaje,
        "segundos": segundos,
        "registro": time_repository.get_detail(registro.id),
    }


def get_active_timer(colaborador_id: int) -> TemporizadorActivo | None:
    """Temporizador activo del colaborador; cierra el de días anteriores (HU_04, HU_50)."""
    colaborador = db.session.get(Colaborador, colaborador_id)
    if colaborador is None:
        return None
    _cerrar_temporizador_vencido(colaborador)
    return time_repository.get_active_for_user(colaborador_id)


# ---------------------------------------------------------------------------
# HU_51: registrar tiempo manualmente
# ---------------------------------------------------------------------------
def create_manual_entry(actor: Colaborador, data: dict) -> dict:
    """HU_51. Captura manual de horas y minutos en una tarea asignada.

    Solo se acepta la fecha de hoy: una fecha anterior exige el permiso de HU_55
    (fuera del MVP) y las fechas futuras siempre se rechazan. El total del día no
    puede exceder 24 horas por colaborador.
    """
    _tarea_para(actor.id, data["tarea_id"])

    hoy = today_mx()
    fecha = data.get("fecha") or hoy
    if fecha > hoy:
        raise ValidationAppError(MSG_FECHA_FUTURA, fields={"fecha": [MSG_FECHA_FUTURA]})
    if fecha < hoy:
        raise ForbiddenError(MSG_FUERA_PLAZO, fields={"fecha": [MSG_FUERA_PLAZO]})

    minutos = data["horas"] * 60 + data["minutos"]
    if minutos <= 0:
        raise ValidationAppError(MSG_TOTAL_CERO, fields={"minutos": [MSG_TOTAL_CERO]})

    _assert_limite_diario(actor.id, fecha, minutos)

    registro = RegistroTiempo(
        tarea_id=data["tarea_id"],
        colaborador_id=actor.id,
        fecha=fecha,
        duracion_minutos=minutos,
        tipo=TIPO_MANUAL,
        descripcion=data["descripcion"],
        nivel_escalafon=actor.grado_escalafon,
        cierre_automatico=False,
        created_by=actor.id,
    )

    try:
        time_repository.add_registro(registro)
        audit.log(
            actor.id,
            entidad="registro_tiempo",
            entidad_id=registro.id,
            accion=audit.CREAR,
            detalle={
                "tarea_id": registro.tarea_id,
                "fecha": fecha.isoformat(),
                "duracion_minutos": minutos,
                "tipo": TIPO_MANUAL,
            },
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_GUARDAR) from exc

    return time_repository.get_detail(registro.id)


# ---------------------------------------------------------------------------
# HU_52: consultar registros
# ---------------------------------------------------------------------------
def list_entries(actor: Colaborador, filtros: dict) -> tuple[list[dict], dict]:
    """HU_52. Listado de registros con total de horas del filtro.

    Dueño, Administrador y Coordinador ven los registros de todos. El Contador solo
    los suyos (RG-12) y el filtro por empleado se ignora para él. Sin rango explícito
    se consulta la semana actual (lunes a domingo, RG-04).
    """
    desde = filtros.get("fecha_desde")
    hasta = filtros.get("fecha_hasta")
    if desde is None and hasta is None:
        hoy = today_mx()
        desde = hoy - timedelta(days=hoy.weekday())
        hasta = desde + timedelta(days=6)

    es_contador = actor.rol == ROL_CONTADOR
    colaborador_id = actor.id if es_contador else filtros.get("empleado")

    items, page, total_minutos = time_repository.search(
        fecha_desde=desde,
        fecha_hasta=hasta,
        colaborador_id=colaborador_id,
        cliente_id=filtros.get("cliente"),
        scope_usuario_id=actor.id if es_contador else None,
        page=filtros["page"],
        per_page=PER_PAGE,
    )

    meta = pagination_meta(page)
    meta.update(
        {
            "total_minutos": total_minutos,
            "total_horas": round(total_minutos / 60, 2),
        }
    )
    return items, meta


# ---------------------------------------------------------------------------
# HU_53: editar registro
# ---------------------------------------------------------------------------
def update_entry(actor: Colaborador, registro_id: int, data: dict) -> dict:
    """HU_53. Corrige duración, descripción o tarea de un registro.

    El autor solo puede editar registros del mismo día natural (o de otro día con el
    permiso de HU_55, fuera del MVP); Dueño y Administrador editan cualquiera. Se
    aplican las validaciones del registro manual y se guarda quién editó y cuándo.
    """
    registro = time_repository.get_by_id(registro_id)
    if registro is None:
        raise NotFoundError(MSG_REGISTRO_NO_ENCONTRADO)

    _assert_can_edit(actor, registro)

    cambios: dict = {}

    if data.get("tarea_id") is not None and data["tarea_id"] != registro.tarea_id:
        _tarea_para(registro.colaborador_id, data["tarea_id"])
        cambios["tarea_id"] = data["tarea_id"]

    horas = data.get("horas")
    minutos = data.get("minutos")
    duracion = data.get("duracion_minutos")
    if horas is not None or minutos is not None:
        actual_horas, actual_minutos = divmod(registro.duracion_minutos, 60)
        nuevo_total = (actual_horas if horas is None else horas) * 60 + (
            actual_minutos if minutos is None else minutos
        )
    elif duracion is not None:
        nuevo_total = duracion
    else:
        nuevo_total = None

    if nuevo_total is not None:
        if nuevo_total <= 0:
            raise ValidationAppError(MSG_TOTAL_CERO, fields={"minutos": [MSG_TOTAL_CERO]})
        if nuevo_total != registro.duracion_minutos:
            _assert_limite_diario(
                registro.colaborador_id,
                registro.fecha,
                nuevo_total,
                exclude_id=registro.id,
            )
            cambios["duracion_minutos"] = nuevo_total

    if (
        data.get("descripcion") is not None
        and data["descripcion"] != registro.descripcion
    ):
        cambios["descripcion"] = data["descripcion"]

    if not cambios:
        return time_repository.get_detail(registro.id)

    anteriores = {campo: getattr(registro, campo) for campo in cambios}
    for campo, valor in cambios.items():
        setattr(registro, campo, valor)
    registro.updated_by = actor.id

    try:
        audit.log(
            actor.id,
            entidad="registro_tiempo",
            entidad_id=registro.id,
            accion=audit.MODIFICAR,
            detalle={
                campo: {
                    "antes": _valor_auditable(anteriores[campo]),
                    "despues": _valor_auditable(valor),
                }
                for campo, valor in cambios.items()
            },
        )
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError(MSG_NO_GUARDAR) from exc

    return time_repository.get_detail(registro.id)


def _assert_can_edit(actor: Colaborador, registro: RegistroTiempo) -> None:
    """HU_53: Dueño y Administrador editan cualquiera; el resto solo lo suyo y del día."""
    if actor.rol in (ROL_DUENO, ROL_ADMINISTRADOR):
        return

    if registro.colaborador_id != actor.id:
        raise ForbiddenError()

    if registro.fecha != today_mx():
        raise ForbiddenError(
            MSG_FUERA_PLAZO_EDICION, fields={"fecha": [MSG_FUERA_PLAZO_EDICION]}
        )
