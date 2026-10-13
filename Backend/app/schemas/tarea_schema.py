"""HU_29. Schemas de alta de tarea."""
from datetime import time as _time

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates,
    validates_schema,
)

from app.core.datetime_utils import today_mx
from app.models.task import PRIORIDADES


def _strip(data: dict) -> dict:
    out = {}
    for k, v in (data or {}).items():
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                v = None
        out[k] = v
    return out


class TareaCreateSchema(Schema):
    """Cuerpo de POST /api/v1/tasks."""

    class Meta:
        unknown = EXCLUDE

    titulo = fields.String(required=True, validate=validate.Length(min=5, max=100))
    descripcion = fields.String(allow_none=True, validate=validate.Length(max=2000))
    cliente_id = fields.Integer(required=True, validate=validate.Range(min=1))
    categoria_id = fields.Integer(required=True, validate=validate.Range(min=1))
    asignado_id = fields.Integer(required=True, validate=validate.Range(min=1))
    fecha_limite = fields.Date(required=True)
    hora_limite = fields.Time(load_default=_time(23, 59))
    prioridad = fields.String(required=True, validate=validate.OneOf(PRIORIDADES))
    horas_estimadas = fields.Decimal(
        allow_none=True, places=1, validate=validate.Range(min=0.5, max=200)
    )
    notificar_cliente = fields.Boolean(load_default=True)

    @pre_load
    def _norm(self, data, **_):
        data = _strip(data)
        if isinstance(data.get("prioridad"), str):
            data["prioridad"] = data["prioridad"].upper()
        return data

    @validates("fecha_limite")
    def _fecha_no_pasada(self, value, **_):
        if value is not None and value < today_mx():
            raise ValidationError("La fecha límite debe ser hoy o posterior")

    @validates("horas_estimadas")
    def _multiplos_media(self, value, **_):
        if value is None:
            return
        # value es Decimal
        doble = value * 2
        if doble != doble.to_integral_value():
            raise ValidationError("Las horas estimadas deben ser múltiplos de 0.5")

    @validates_schema
    def _reglas_cruzadas(self, data, **_):
        # No hay reglas cruzadas obligatorias aquí; las de "cliente Activo",
        # "categoría Activa" y "contador Activo" dependen de la BD y se validan en el servicio.
        return