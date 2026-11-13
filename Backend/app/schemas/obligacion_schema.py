"""Schemas de obligaciones periódicas."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate, validates_schema
from marshmallow import ValidationError as MarshmallowValidationError

from app.models.obligation import PERIODICIDADES, PERIODICIDAD_SEMANAL
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


class ObligacionQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=1))
    solo_activas = fields.Boolean(load_default=False)
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))

    @pre_load
    def _norm(self, data, **_):
        data = dict(data or {})
        if data.get("cliente") == "":
            data.pop("cliente")
        return data


class ObligacionCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente_id = fields.Integer(required=True, validate=validate.Range(min=1))
    categoria_id = fields.Integer(required=True, validate=validate.Range(min=1))
    responsable_id = fields.Integer(required=True, validate=validate.Range(min=1))
    periodicidad = fields.String(required=True, validate=validate.OneOf(PERIODICIDADES))
    dia_vencimiento = fields.Integer(required=True, validate=validate.Range(min=1, max=31))
    fecha_inicio = fields.Date(required=True)
    prioridad = fields.String(required=True, validate=validate.OneOf(PRIORIDADES))

    @pre_load
    def _norm(self, data, **_):
        data = _strip(data)
        for field in ("periodicidad", "prioridad"):
            if isinstance(data.get(field), str):
                data[field] = data[field].upper()
        return data

    @validates_schema
    def _dias_por_periodicidad(self, data, **_):
        if data.get("periodicidad") == PERIODICIDAD_SEMANAL:
            dia = data.get("dia_vencimiento")
            if dia is not None and not 1 <= dia <= 7:
                raise MarshmallowValidationError(
                    "Para periodicidad semanal el día debe estar entre 1 y 7",
                    field_name="dia_vencimiento",
                )


class ObligacionUpdateSchema(ObligacionCreateSchema):
    activa = fields.Boolean(load_default=None, allow_none=True)
