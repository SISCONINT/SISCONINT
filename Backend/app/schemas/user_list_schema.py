"""Esquemas del listado de colaboradores (HU_06)."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

from app.models.user import ESTATUS_ACTIVO, ESTATUS_INACTIVO, ROLES

_INVALID = {"invalid": "Valor no válido"}


class ColaboradorListQuerySchema(Schema):
    """Parámetros de la URL: ?q=&rol=&estatus=&page=  (todos opcionales).

    Por defecto solo muestra Activos. Los 20 registros por página son fijos (RG-07): cualquier
    otro parámetro, como per_page, se ignora.
    """

    class Meta:
        unknown = EXCLUDE

    q = fields.String(validate=validate.Length(max=150, error="Máximo 150 caracteres"), error_messages=_INVALID)
    rol = fields.String(
        validate=validate.OneOf(ROLES, error="Rol no válido. Valores: " + ", ".join(ROLES)),
        error_messages=_INVALID,
    )
    estatus = fields.String(
        load_default=ESTATUS_ACTIVO,
        validate=validate.OneOf(
            (ESTATUS_ACTIVO, ESTATUS_INACTIVO),
            error=f"Estatus no válido. Valores: {ESTATUS_ACTIVO}, {ESTATUS_INACTIVO}",
        ),
        error_messages=_INVALID,
    )
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="La página debe ser 1 o mayor"),
        error_messages={"invalid": "La página debe ser un número entero"},
    )

    @pre_load
    def normalize(self, data, **_kwargs):
        clean = {}
        for key, value in data.items():
            value = value.strip() if isinstance(value, str) else value
            if value in ("", None):  # parámetro vacío = no enviado (el frontend manda ?rol=&q=)
                continue
            clean[key] = value
        for key in ("rol", "estatus"):
            if isinstance(clean.get(key), str):
                clean[key] = clean[key].upper()
        return clean


class ColaboradorListItemSchema(Schema):
    """Columnas del listado. No incluye domicilio, teléfonos ni contacto de emergencia (HU_07)."""

    id = fields.Integer()
    nombre_completo = fields.String()
    correo_institucional = fields.String()
    rol = fields.String()
    grado_escalafon = fields.String()
    estatus = fields.String()