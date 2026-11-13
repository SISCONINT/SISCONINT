"""Schemas de plantillas de notificación."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models.email_template import CLAVES


class PlantillaCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    clave = fields.String(required=True, validate=validate.OneOf(CLAVES))
    asunto = fields.String(required=True, validate=validate.Length(min=1, max=150))
    cuerpo = fields.String(required=True, validate=validate.Length(min=1, max=2000))

    @pre_load
    def _norm(self, data, **_):
        data = dict(data or {})
        for field in ("clave", "asunto", "cuerpo"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()
        if isinstance(data.get("clave"), str):
            data["clave"] = data["clave"].upper()
        return data


class PlantillaUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    asunto = fields.String(required=True, validate=validate.Length(min=1, max=150))
    cuerpo = fields.String(required=True, validate=validate.Length(min=1, max=2000))

    @pre_load
    def _norm(self, data, **_):
        data = dict(data or {})
        for field in ("asunto", "cuerpo"):
            value = data.get(field)
            if isinstance(value, str):
                data[field] = value.strip()
        return data
