"""Schemas de minutas y acuerdos."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


def _strip(data: dict) -> dict:
    out = {}
    for k, v in (data or {}).items():
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                v = None
        out[k] = v
    return out


class MinutaQuerySchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=1))
    tarea = fields.Integer(load_default=None, allow_none=True, validate=validate.Range(min=1))
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))

    @pre_load
    def _norm(self, data, **_):
        data = dict(data or {})
        for key in ("cliente", "tarea"):
            if data.get(key) == "":
                data.pop(key)
        return data


class MinutaCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    tarea_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    titulo = fields.String(required=True, validate=validate.Length(min=1, max=150))
    fecha = fields.Date(required=True)
    participantes = fields.String(allow_none=True, validate=validate.Length(max=300))
    acuerdos = fields.String(required=True, validate=validate.Length(min=1, max=4000))

    @pre_load
    def _norm(self, data, **_):
        return _strip(data)


class MinutaUpdateSchema(MinutaCreateSchema):
    pass
