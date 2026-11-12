"""Schemas de plantillas de correo."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


class PlantillaCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    clave = fields.String(required=True, validate=validate.Length(min=1, max=50))
    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    asunto = fields.String(required=True, validate=validate.Length(min=1, max=200))
    cuerpo = fields.String(required=True, validate=validate.Length(min=1, max=8000))
    activa = fields.Boolean(load_default=True)

    @pre_load
    def _norm(self, data, **_):
        data = dict(data or {})
        if isinstance(data.get("clave"), str):
            data["clave"] = data["clave"].strip().upper().replace(" ", "_")
        return data


class PlantillaUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    nombre = fields.String(required=True, validate=validate.Length(min=1, max=150))
    asunto = fields.String(required=True, validate=validate.Length(min=1, max=200))
    cuerpo = fields.String(required=True, validate=validate.Length(min=1, max=8000))
    activa = fields.Boolean(load_default=True)
