"""Schemas de minutas y acuerdos (documentos cargados)."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models.minute import TIPOS


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

    tipo = fields.String(required=True, validate=validate.OneOf(TIPOS))
    titulo = fields.String(required=True, validate=validate.Length(min=3, max=100))
    fecha_reunion = fields.Date(required=True)
    cliente_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    tarea_id = fields.Integer(allow_none=True, validate=validate.Range(min=1))
    observaciones = fields.String(allow_none=True, validate=validate.Length(max=2000))

    @pre_load
    def _norm(self, data, **_):
        data = _strip(data)
        if isinstance(data.get("tipo"), str):
            data["tipo"] = data["tipo"].upper()
        return data


class MinutaUpdateSchema(MinutaCreateSchema):
    pass
