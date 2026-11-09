"""Schemas de obligaciones periódicas."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models.obligation import PERIODICIDADES


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
    categoria_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    periodicidad = fields.String(required=True, validate=validate.OneOf(PERIODICIDADES))
    dia_limite = fields.Integer(required=True, validate=validate.Range(min=1, max=31))
    notas = fields.String(allow_none=True, validate=validate.Length(max=300))

    @pre_load
    def _norm(self, data, **_):
        data = _strip(data)
        if isinstance(data.get("periodicidad"), str):
            data["periodicidad"] = data["periodicidad"].upper()
        return data


class ObligacionUpdateSchema(ObligacionCreateSchema):
    activa = fields.Boolean(load_default=True)
