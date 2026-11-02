"""HU_64. Schemas del panel de alertas de vencimiento."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.core.semaforo import SEMAFORO_AMARILLO, SEMAFORO_ROJO

COLORES_ALERTA = (SEMAFORO_ROJO, SEMAFORO_AMARILLO)


class TareaAlertaQuerySchema(Schema):
    """Query params de GET /api/v1/tasks/alerts (HU_64).

    `color` solo admite ROJO y AMARILLO: el panel no muestra tareas verdes ni
    completadas. Los filtros son opcionales y se pueden combinar.
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
    color = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(
            COLORES_ALERTA,
            error=f"Color no válido. Valores: {', '.join(COLORES_ALERTA)}",
        ),
    )
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="La página debe ser 1 o mayor"),
        error_messages={"invalid": "La página debe ser un número entero"},
    )

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios, quita parámetros vacíos y pasa el color a mayúsculas."""
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue  # el frontend puede mandar ?cliente=&color=
            limpio[clave] = valor

        if isinstance(limpio.get("color"), str):
            limpio["color"] = limpio["color"].upper()
        return limpio


class TareaAlertaItemSchema(Schema):
    """Fila del panel: cliente, tarea, responsable, fecha límite y atraso."""

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
    dias_restantes = fields.Integer()
    dias_atraso = fields.Integer()


class TareaAlertasSchema(Schema):
    """Panel de alertas: conteos de Rojo/Amarillo y el listado paginado.

    Los conteos respetan los filtros de cliente y responsable, pero no el de color:
    así el panel siempre muestra cuántas tareas hay en cada color aunque el listado
    esté acotado a uno de ellos.
    """

    class Meta:
        unknown = EXCLUDE

    conteos = fields.Dict(keys=fields.String(), values=fields.Integer())
    tareas = fields.List(fields.Nested(TareaAlertaItemSchema))
