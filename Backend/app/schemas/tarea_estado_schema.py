"""HU_43. Schema para mover una tarea entre columnas del tablero."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models.task import ESTADOS


class TareaEstadoSchema(Schema):
    """Cuerpo de PATCH /api/v1/tasks/<id>/estado.

    `confirmar_subtareas_pendientes` es la confirmación explícita (RG-14) que se
    exige cuando la tarea pasa a Completado y todavía tiene subtareas sin terminar.
    """

    class Meta:
        unknown = EXCLUDE

    estado = fields.String(
        required=True,
        validate=validate.OneOf(
            ESTADOS, error=f"Estado no válido. Valores: {', '.join(ESTADOS)}"
        ),
    )
    confirmar_subtareas_pendientes = fields.Boolean(load_default=False)

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios y deja el estado en mayúsculas (enums del sistema)."""
        limpio = dict(data or {})
        if isinstance(limpio.get("estado"), str):
            limpio["estado"] = limpio["estado"].strip().upper()
        return limpio
