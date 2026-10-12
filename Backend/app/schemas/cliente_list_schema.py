"""HU_12. Schemas del listado de clientes."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


class ClienteListQuerySchema(Schema):
    """Query params de GET /api/v1/clients."""

    class Meta:
        unknown = EXCLUDE

    q = fields.String(load_default=None, allow_none=True)
    estatus = fields.String(
        load_default="ACTIVO",
        validate=validate.OneOf(["ACTIVO", "PAUSADO", "BAJA"]),
    )
    contador = fields.Integer(load_default=None, allow_none=True)
    tipo_persona = fields.String(
        load_default=None,
        allow_none=True,
        validate=validate.OneOf(["FISICA", "MORAL"]),
    )
    page = fields.Integer(load_default=1, validate=validate.Range(min=1))

    @pre_load
    def _normalize(self, data, **_):
        data = dict(data or {})
        # recorta y vacío -> None
        for key in ("q", "contador", "tipo_persona"):
            v = data.get(key)
            if isinstance(v, str):
                v = v.strip()
                if v == "":
                    data[key] = None
        # enums a mayúsculas
        for key in ("estatus", "tipo_persona"):
            v = data.get(key)
            if isinstance(v, str) and v:
                data[key] = v.upper()
        return data


class ClienteListItemSchema(Schema):
    """Columnas del listado de HU_12.

    El repositorio devuelve tuplas (Cliente, contacto_principal_correo,
    tareas_activas, horas_registradas); el servicio las convierte a dicts y este
    schema las serializa.
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    nombre_completo = fields.String()
    razon_social = fields.String(allow_none=True)
    rfc = fields.String()
    tipo_persona = fields.String()
    contacto_principal_correo = fields.String(allow_none=True)
    tareas_activas = fields.Integer()
    horas_registradas = fields.Float()
    estatus = fields.String()