"""Validadores reutilizables (RG-09, RG-10). Mismos formatos que los CHECK de la base."""
import re

from marshmallow import ValidationError

from app.core.errors import MSG_REQUIRED

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9]{10}$")
_CEDULA_RE = re.compile(r"^[0-9]{7,8}$")


def not_blank(value: str) -> None:
    if value is None or not str(value).strip():
        raise ValidationError(MSG_REQUIRED)


def validate_email(value: str) -> None:
    if not _EMAIL_RE.match(value):
        raise ValidationError("Correo electrónico con formato no válido")


def validate_phone(value: str) -> None:
    if not _PHONE_RE.match(value):
        raise ValidationError("El teléfono debe tener 10 dígitos")
    
    
def validate_postal_code(value: str) -> None:
    if not re.match(r"^[0-9]{5}$", value or ""):
        raise ValidationError("El código postal debe tener 5 dígitos")


def validate_cedula(value: str) -> None:
    if not _CEDULA_RE.match(value):
        raise ValidationError("La cédula debe tener 7 u 8 dígitos")
    
def validate_password(value: str) -> None:
    """RG-05: mínimo 10 caracteres, con mayúscula, minúscula, número y símbolo."""
    if not value or len(value) < 10:
        raise ValidationError("La contraseña debe tener al menos 10 caracteres")
    if not re.search(r"[A-Z]", value):
        raise ValidationError("La contraseña debe incluir al menos una mayúscula")
    if not re.search(r"[a-z]", value):
        raise ValidationError("La contraseña debe incluir al menos una minúscula")
    if not re.search(r"[0-9]", value):
        raise ValidationError("La contraseña debe incluir al menos un número")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValidationError("La contraseña debe incluir al menos un símbolo")