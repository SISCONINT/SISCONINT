"""HU_41. Schema del tablero Kanban."""
from marshmallow import EXCLUDE, Schema, fields


class TareaBoardCardSchema(Schema):
    """Tarjeta del tablero: lo que se pinta en cada columna (HU_41).

    Las fechas viajan en ISO 8601; el formato DD/MM/AAAA y el color del semáforo se
    aplican en el frontend (RG-04, RG-11).
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    titulo = fields.String()
    cliente_id = fields.Integer()
    cliente_nombre = fields.String(allow_none=True)
    asignado_id = fields.Integer()
    asignado_nombre = fields.String(allow_none=True)
    prioridad = fields.String()
    estado = fields.String()
    fecha_limite = fields.Date()
    hora_limite = fields.String(allow_none=True)
    semaforo = fields.String()
    minutos_registrados = fields.Integer()
    horas_registradas = fields.Float()
    horas_estimadas = fields.Float(allow_none=True)
    porcentaje_registrado = fields.Float(allow_none=True)
    completada_en = fields.DateTime(allow_none=True)


class TareaBoardColumnSchema(Schema):
    """Columna fija del tablero con su contador de tareas."""

    class Meta:
        unknown = EXCLUDE

    estado = fields.String()
    titulo = fields.String()
    total = fields.Integer()
    tareas = fields.List(fields.Nested(TareaBoardCardSchema))


class TareaBoardSchema(Schema):
    """Las cuatro columnas del tablero y el total de tarjetas."""

    class Meta:
        unknown = EXCLUDE

    columnas = fields.List(fields.Nested(TareaBoardColumnSchema))
    total_tareas = fields.Integer()
