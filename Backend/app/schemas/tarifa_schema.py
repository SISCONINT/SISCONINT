"""HU_57-62. Schemas del catálogo de tarifas por nivel."""
from marshmallow import EXCLUDE, Schema, fields, validate

from app.models.user import GRADOS


class TarifaUpsertSchema(Schema):
    """Cuerpo de PUT /api/v1/rates/<nivel>."""

    class Meta:
        unknown = EXCLUDE

    monto_hora_mxn = fields.Decimal(
        required=True,
        places=2,
        validate=validate.Range(min=0.01, max=999999.99),
        error_messages={"invalid": "El monto por hora debe ser un número válido"},
    )
    vigencia_inicio = fields.Date(load_default=None, allow_none=True)
    vigencia_fin = fields.Date(load_default=None, allow_none=True)


class TarifaSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer(allow_none=True)
    nivel = fields.String(validate=validate.OneOf(GRADOS))
    monto_hora_mxn = fields.Float(allow_none=True)
    vigencia_inicio = fields.Date(allow_none=True)
    vigencia_fin = fields.Date(allow_none=True)
    vigente = fields.Boolean()
    updated_at = fields.DateTime(allow_none=True)
