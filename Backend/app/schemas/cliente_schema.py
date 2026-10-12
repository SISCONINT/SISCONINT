"""HU_11. Schemas de alta de cliente."""
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

from app.core.validators import validate_email, validate_phone, validate_postal_code
from app.models.client import (
    NOMINA_MENSUAL,
    NOMINA_QUINCENAL,
    NOMINA_SEMANAL,
    TIPO_FISICA,
    TIPO_MORAL,
)

_TIPOS_PERSONA = (TIPO_FISICA, TIPO_MORAL)
_FORMAS_PAGO = ("EFECTIVO", "TRANSFERENCIA")
_TIPOS_NOMINA = (NOMINA_SEMANAL, NOMINA_QUINCENAL, NOMINA_MENSUAL)
_RFC_FISICA = r"^[A-ZÑ&]{4}[0-9]{6}[A-Z0-9]{3}$"
_RFC_MORAL = r"^[A-ZÑ&]{3}[0-9]{6}[A-Z0-9]{3}$"


def _strip(data: dict) -> dict:
    out = {}
    for k, v in (data or {}).items():
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                v = None
        out[k] = v
    return out


class _Contacto(Schema):
    class Meta:
        unknown = EXCLUDE

    nombre_completo = fields.String(required=True, validate=validate.Length(min=1, max=150))
    telefono = fields.String(required=True, validate=validate_phone)
    correo = fields.String(required=True, validate=validate_email)
    cargo = fields.String(required=True, validate=validate.Length(min=1, max=100))

    @pre_load
    def _norm(self, data, **_):
        return _strip(data)


class ClienteCreateSchema(Schema):
    """Cuerpo de POST /api/v1/clients."""

    class Meta:
        unknown = EXCLUDE

    # Generales
    nombre_completo = fields.String(required=True, validate=validate.Length(min=1, max=200))
    rfc = fields.String(required=True, validate=validate.Length(min=12, max=13))
    tipo_persona = fields.String(required=True, validate=validate.OneOf(_TIPOS_PERSONA))
    razon_social = fields.String(allow_none=True, validate=validate.Length(max=250))
    forma_pago = fields.String(required=True, validate=validate.OneOf(_FORMAS_PAGO))
    contador_asignado_id = fields.Integer(required=True, validate=validate.Range(min=1))
    giro = fields.String(required=True, validate=validate.Length(min=1, max=150))
    telefono = fields.String(required=True, validate=validate_phone)
    correo = fields.String(required=True, validate=validate_email)

    # Domicilio fiscal
    codigo_postal = fields.String(required=True, validate=validate_postal_code)
    calle = fields.String(required=True, validate=validate.Length(min=1, max=150))
    no_exterior = fields.String(required=True, validate=validate.Length(min=1, max=20))
    no_interior = fields.String(allow_none=True, validate=validate.Length(max=20))
    colonia = fields.String(required=True, validate=validate.Length(min=1, max=100))
    ciudad = fields.String(required=True, validate=validate.Length(min=1, max=100))
    estado = fields.String(required=True, validate=validate.Length(min=1, max=100))

    # Régimen y nómina
    regimenes = fields.List(fields.String(validate=validate.Length(equal=3)), required=True, validate=validate.Length(min=1))
    tiene_trabajadores = fields.Boolean(required=True)
    tipo_nomina = fields.String(allow_none=True, validate=validate.OneOf(_TIPOS_NOMINA))

    # Contactos
    contacto_principal = fields.Nested(_Contacto, required=True)
    contacto_pagos = fields.Nested(_Contacto, allow_none=True)

    @pre_load
    def _norm(self, data, **_):
        data = _strip(data)
        if isinstance(data.get("rfc"), str):
            data["rfc"] = data["rfc"].upper()
        if isinstance(data.get("tipo_persona"), str):
            data["tipo_persona"] = data["tipo_persona"].upper()
        if isinstance(data.get("forma_pago"), str):
            data["forma_pago"] = data["forma_pago"].upper()
        if isinstance(data.get("tipo_nomina"), str):
            data["tipo_nomina"] = data["tipo_nomina"].upper()
        regimenes = data.get("regimenes")
        if isinstance(regimenes, list):
            data["regimenes"] = [r.upper() if isinstance(r, str) else r for r in regimenes]
        return data

    @validates_schema
    def _reglas_cruzadas(self, data, **_):
        errors = {}

        tipo = data.get("tipo_persona")
        rfc = data.get("rfc") or ""
        if tipo == TIPO_MORAL:
            if not data.get("razon_social"):
                errors["razon_social"] = ["Campo obligatorio"]
            if len(rfc) != 12:
                errors["rfc"] = ["El RFC de persona Moral debe tener 12 caracteres"]
        elif tipo == TIPO_FISICA:
            if len(rfc) != 13:
                errors["rfc"] = ["El RFC de persona Física debe tener 13 caracteres"]

        # Formato RFC por tipo
        import re
        if tipo == TIPO_MORAL and rfc and not re.match(_RFC_MORAL, rfc):
            errors["rfc"] = ["El RFC no tiene un formato válido"]
        elif tipo == TIPO_FISICA and rfc and not re.match(_RFC_FISICA, rfc):
            errors["rfc"] = ["El RFC no tiene un formato válido"]

        # Nómina condicional
        tiene = data.get("tiene_trabajadores")
        nomina = data.get("tipo_nomina")
        if tiene is True and not nomina:
            errors["tipo_nomina"] = ["Campo obligatorio"]
        if tiene is False and nomina:
            errors["tipo_nomina"] = ["No aplica cuando no tiene trabajadores"]

        # Regla "todo o nada" para el contacto de pagos
        pagos = data.get("contacto_pagos")
        if pagos is not None:
            faltantes = [k for k in ("nombre_completo", "telefono", "correo", "cargo") if not pagos.get(k)]
            if faltantes:
                errors["contacto_pagos"] = [
                    "Si capturas el contacto de pagos, sus 4 campos son obligatorios"
                ]

        if errors:
            raise ValidationError(errors)