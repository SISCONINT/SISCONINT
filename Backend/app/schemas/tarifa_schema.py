"""HU_57-62. Schemas del catálogo de tarifas por colaborador."""
from marshmallow import EXCLUDE, Schema, fields, validate


class TarifaUpsertSchema(Schema):
    """Cuerpo de PUT /api/v1/rates/<colaborador_id>."""

    class Meta:
        unknown = EXCLUDE

    monto_hora = fields.Decimal(
        required=True, places=2, validate=validate.Range(min=0.01, max=99999.99),
        error_messages={"invalid": "El monto por hora debe ser un número válido"},
    )
    moneda = fields.String(load_default="MXN", validate=validate.OneOf(["MXN", "USD"]))


class TarifaSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    colaborador_id = fields.Integer()
    colaborador_nombre = fields.String()
    rol = fields.String()
    monto_hora = fields.Float(allow_none=True)
    moneda = fields.String(allow_none=True)
    updated_at = fields.DateTime(allow_none=True)
