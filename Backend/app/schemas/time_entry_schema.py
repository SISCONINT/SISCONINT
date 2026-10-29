"""HU_49-53. Schemas del módulo 8: registro de tiempos."""
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

MSG_DESCRIPCION = "La descripción debe tener entre 5 y 500 caracteres"
MSG_TOTAL_CERO = "El total de horas y minutos debe ser mayor a 0"


def _limpiar(data: dict) -> dict:
    """Recorta espacios y descarta cadenas vacías (el frontend puede mandar campos vacíos)."""
    limpio = {}
    for clave, valor in (data or {}).items():
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                continue
        limpio[clave] = valor
    return limpio


class TimeEntryTimerStartSchema(Schema):
    """Cuerpo de POST /api/v1/time-entries/timer (HU_49)."""

    class Meta:
        unknown = EXCLUDE

    tarea_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="La tarea debe ser un id válido"),
        error_messages={"invalid": "La tarea debe ser un id válido", "required": "Campo obligatorio"},
    )


class TimeEntryTimerStopSchema(Schema):
    """Cuerpo de POST /api/v1/time-entries/timer/stop (HU_50)."""

    class Meta:
        unknown = EXCLUDE

    descripcion = fields.String(
        required=True,
        validate=validate.Length(min=5, max=500, error=MSG_DESCRIPCION),
        error_messages={"required": "Campo obligatorio"},
    )
    # Opcional: si el cliente lo envía, debe corresponder al temporizador activo.
    temporizador_id = fields.Integer(
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=1, error="El temporizador debe ser un id válido"),
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class TimeEntryManualSchema(Schema):
    """Cuerpo de POST /api/v1/time-entries (HU_51).

    `fecha` se captura como AAAA-MM-DD; si no llega, el servicio usa hoy (RG-04).
    """

    class Meta:
        unknown = EXCLUDE

    tarea_id = fields.Integer(
        required=True,
        validate=validate.Range(min=1, error="La tarea debe ser un id válido"),
        error_messages={"invalid": "La tarea debe ser un id válido", "required": "Campo obligatorio"},
    )
    fecha = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    horas = fields.Integer(
        required=True,
        validate=validate.Range(min=0, max=23, error="Las horas deben estar entre 0 y 23"),
        error_messages={"invalid": "Las horas deben ser un número entero", "required": "Campo obligatorio"},
    )
    minutos = fields.Integer(
        required=True,
        validate=validate.Range(min=0, max=59, error="Los minutos deben estar entre 0 y 59"),
        error_messages={
            "invalid": "Los minutos deben ser un número entero",
            "required": "Campo obligatorio",
        },
    )
    descripcion = fields.String(
        required=True,
        validate=validate.Length(min=5, max=500, error=MSG_DESCRIPCION),
        error_messages={"required": "Campo obligatorio"},
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)

    @validates_schema
    def _total_mayor_cero(self, data, **_):
        if data.get("horas") == 0 and data.get("minutos") == 0:
            raise ValidationError(MSG_TOTAL_CERO, field_name="minutos")


class TimeEntryUpdateSchema(Schema):
    """Cuerpo de PUT /api/v1/time-entries/<id> (HU_53)."""

    class Meta:
        unknown = EXCLUDE

    tarea_id = fields.Integer(
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=1, error="La tarea debe ser un id válido"),
    )
    horas = fields.Integer(
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=0, max=23, error="Las horas deben estar entre 0 y 23"),
        error_messages={"invalid": "Las horas deben ser un número entero"},
    )
    minutos = fields.Integer(
        allow_none=True,
        load_default=None,
        validate=validate.Range(min=0, max=59, error="Los minutos deben estar entre 0 y 59"),
        error_messages={"invalid": "Los minutos deben ser un número entero"},
    )
    duracion_minutos = fields.Integer(
        allow_none=True,
        load_default=None,
        validate=validate.Range(
            min=1, max=24 * 60, error="La duración debe estar entre 1 y 1440 minutos"
        ),
        error_messages={"invalid": "La duración debe ser un número entero"},
    )
    descripcion = fields.String(
        allow_none=True,
        load_default=None,
        validate=validate.Length(min=5, max=500, error=MSG_DESCRIPCION),
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class TimeEntryListQuerySchema(Schema):
    """Query params de GET /api/v1/time-entries (HU_52).

    El rango por defecto (semana actual) lo aplica el servicio. `page` es la única
    paginación aceptada porque RG-07 fija 20 registros por página.
    """

    class Meta:
        unknown = EXCLUDE

    fecha_desde = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    fecha_hasta = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    empleado = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El empleado debe ser un id válido"),
        error_messages={"invalid": "El empleado debe ser un id válido"},
    )
    cliente = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El cliente debe ser un id válido"),
        error_messages={"invalid": "El cliente debe ser un id válido"},
    )
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="La página debe ser 1 o mayor"),
        error_messages={"invalid": "La página debe ser un número entero"},
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)

    @validates_schema
    def _validar_rango(self, data, **_):
        desde = data.get("fecha_desde")
        hasta = data.get("fecha_hasta")
        if desde is not None and hasta is not None and desde > hasta:
            raise ValidationError(
                "La fecha inicial no puede ser posterior a la final",
                field_name="fecha_desde",
            )


class TimeEntrySchema(Schema):
    """Registro de tiempo listo para el cliente (HU_50-53)."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    fecha = fields.Date()
    empleado_id = fields.Integer()
    empleado_nombre = fields.String(allow_none=True)
    cliente_id = fields.Integer(allow_none=True)
    cliente_nombre = fields.String(allow_none=True)
    tarea_id = fields.Integer()
    tarea_titulo = fields.String(allow_none=True)
    tipo = fields.String()
    duracion_minutos = fields.Integer()
    horas = fields.Float()
    descripcion = fields.String()
    nivel_escalafon = fields.String()
    cierre_automatico = fields.Boolean()
    permiso_fuera_plazo_id = fields.Integer(allow_none=True)
    created_at = fields.DateTime(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)


class TimeEntryTimerSchema(Schema):
    """Temporizador activo (HU_49).

    `iniciado_en` viaja en UTC (RG-04); `transcurrido` está en HH:MM:SS y se calcula
    con la hora del servidor.
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    tarea_id = fields.Integer()
    tarea_titulo = fields.String(allow_none=True)
    cliente_id = fields.Integer(allow_none=True)
    cliente_nombre = fields.String(allow_none=True)
    iniciado_en = fields.DateTime()
    transcurrido_segundos = fields.Integer()
    transcurrido = fields.String()


class TimeEntryTimerResultSchema(Schema):
    """Resultado de detener el temporizador (HU_50) o de un cierre automático."""

    class Meta:
        unknown = EXCLUDE

    guardado = fields.Boolean()
    descartado = fields.Boolean()
    cierre_automatico = fields.Boolean()
    mensaje = fields.String()
    segundos = fields.Integer(allow_none=True)
    registro = fields.Nested(TimeEntrySchema, allow_none=True)


class TimeEntryTimerStateSchema(Schema):
    """Estado del temporizador al abrir o recargar la pantalla (HU_49-50)."""

    class Meta:
        unknown = EXCLUDE

    activo = fields.Nested(TimeEntryTimerSchema, allow_none=True)
    aviso_cierre_automatico = fields.Nested(TimeEntryTimerResultSchema, allow_none=True)
