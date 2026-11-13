"""Calendario de vencimientos: filtros y contrato de salida."""
from marshmallow import EXCLUDE, Schema, ValidationError, fields, pre_load, validate, validates_schema

MAX_DIAS_RANGO = 366


class CalendarQuerySchema(Schema):
    """Query params de GET /api/v1/calendar.

    Si no llega el rango se usa el mes actual. `cliente` y `colaborador` son
    opcionales y se combinan con el alcance RG-12 del Contador.
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
    cliente = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El cliente debe ser un id válido"),
    )
    colaborador = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El colaborador debe ser un id válido"),
    )

    @pre_load
    def _norm(self, data, **_):
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue
            limpio[clave] = valor
        return limpio

    @validates_schema
    def _validar_rango(self, data, **_):
        desde = data.get("fecha_desde")
        hasta = data.get("fecha_hasta")
        if (desde is None) != (hasta is None):
            raise ValidationError(
                "Envía fecha_desde y fecha_hasta juntas", field_name="fecha_desde"
            )
        if desde is None:
            return
        if desde > hasta:
            raise ValidationError(
                "La fecha inicial no puede ser posterior a la final",
                field_name="fecha_desde",
            )
        if (hasta - desde).days + 1 > MAX_DIAS_RANGO:
            raise ValidationError(
                "El rango no puede superar 12 meses", field_name="fecha_hasta"
            )


class CalendarEventoSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    tipo = fields.String()
    titulo = fields.String()
    fecha = fields.Date()
    hora = fields.String(allow_none=True)
    cliente_id = fields.Integer()
    cliente_nombre = fields.String(allow_none=True)
    asignado_id = fields.Integer(allow_none=True)
    asignado_nombre = fields.String(allow_none=True)
    estado = fields.String(allow_none=True)
    prioridad = fields.String(allow_none=True)
    semaforo = fields.String(allow_none=True)


class CalendarSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    desde = fields.Date()
    hasta = fields.Date()
    eventos = fields.Nested(CalendarEventoSchema, many=True)
    total = fields.Integer()
    por_dia = fields.Dict(keys=fields.String(), values=fields.Integer())
    mensaje = fields.String(allow_none=True)
