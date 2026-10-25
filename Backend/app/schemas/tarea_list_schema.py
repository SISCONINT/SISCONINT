"""HU_30. Schemas del listado de tareas."""
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

from app.core.semaforo import SEMAFOROS
from app.models.task import ESTADOS, PRIORIDADES

_ENUMS_MAYUSCULAS = ("estado", "prioridad", "semaforo")


class TareaListQuerySchema(Schema):
    """Query params de GET /api/v1/tasks.

    Todos los filtros son opcionales; `page` es la única paginación aceptada porque
    RG-07 fija 20 registros por página.
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
    estado = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(ESTADOS, error=f"Estado no válido. Valores: {', '.join(ESTADOS)}"),
    )
    prioridad = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(
            PRIORIDADES, error=f"Prioridad no válida. Valores: {', '.join(PRIORIDADES)}"
        ),
    )
    categoria = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="La categoría debe ser un id válido"),
        error_messages={"invalid": "La categoría debe ser un id válido"},
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
    semaforo = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(
            SEMAFOROS, error=f"Semáforo no válido. Valores: {', '.join(SEMAFOROS)}"
        ),
    )
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="La página debe ser 1 o mayor"),
        error_messages={"invalid": "La página debe ser un número entero"},
    )

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios, quita parámetros vacíos y pasa los enums a mayúsculas."""
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue  # el frontend puede mandar ?estado=&page=
            limpio[clave] = valor

        for clave in _ENUMS_MAYUSCULAS:
            if isinstance(limpio.get(clave), str):
                limpio[clave] = limpio[clave].upper()
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


class TareaListItemSchema(Schema):
    """Columnas del listado de HU_30.

    El servicio entrega los nombres ya resueltos y el semáforo calculado; este schema
    solo serializa. Las fechas viajan en ISO 8601 (RG-04: DD/MM/AAAA se aplica en el front).
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    titulo = fields.String()
    cliente_id = fields.Integer()
    cliente_nombre = fields.String(allow_none=True)
    categoria_id = fields.Integer()
    categoria_nombre = fields.String(allow_none=True)
    categoria_padre_nombre = fields.String(allow_none=True)
    asignado_id = fields.Integer()
    asignado_nombre = fields.String(allow_none=True)
    prioridad = fields.String()
    estado = fields.String()
    fecha_limite = fields.Date()
    hora_limite = fields.String(allow_none=True)
    semaforo = fields.String()
    dias_restantes = fields.Integer()
