"""HU_41-42. Schemas del tablero Kanban."""
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

from app.models.task import PRIORIDADES


class TareaBoardQuerySchema(Schema):
    """Query params de GET /api/v1/tasks/board (HU_42).

    Todos los filtros son opcionales y se pueden combinar. `responsable` no está
    disponible para el Contador: el servicio lo ignora para respetar su alcance
    (RG-12), igual que en el listado de HU_30.
    """

    class Meta:
        unknown = EXCLUDE

    cliente = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El cliente debe ser un id válido"),
        error_messages={"invalid": "El cliente debe ser un id válido"},
    )
    responsable = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El responsable debe ser un id válido"),
        error_messages={"invalid": "El responsable debe ser un id válido"},
    )
    prioridad = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(
            PRIORIDADES, error=f"Prioridad no válida. Valores: {', '.join(PRIORIDADES)}"
        ),
    )
    fecha_limite_desde = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    fecha_limite_hasta = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios, quita parámetros vacíos y pasa la prioridad a mayúsculas."""
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue  # el frontend puede mandar ?cliente=&prioridad=
            limpio[clave] = valor

        if isinstance(limpio.get("prioridad"), str):
            limpio["prioridad"] = limpio["prioridad"].upper()
        return limpio

    @validates_schema
    def _validar_rango(self, data, **_):
        desde = data.get("fecha_limite_desde")
        hasta = data.get("fecha_limite_hasta")
        if desde is not None and hasta is not None and desde > hasta:
            raise ValidationError(
                "La fecha límite inicial no puede ser posterior a la final",
                field_name="fecha_limite_desde",
            )


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
    """Las cuatro columnas del tablero y el total de tarjetas.

    `mensaje` solo viaja cuando hay filtros aplicados y ninguna tarea cumple
    (HU_42): «No hay tareas con los filtros seleccionados».
    """

    class Meta:
        unknown = EXCLUDE

    columnas = fields.List(fields.Nested(TareaBoardColumnSchema))
    total_tareas = fields.Integer()
    mensaje = fields.String(allow_none=True)
