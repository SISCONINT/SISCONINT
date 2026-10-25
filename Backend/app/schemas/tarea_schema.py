"""HU_29, HU_32. Schemas de alta y edición de tarea."""
from datetime import time as _time

from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates,
    validates_schema,
)

from app.core.datetime_utils import today_mx
from app.models.task import PRIORIDADES

MSG_FECHA_PASADA = "La fecha límite debe ser hoy o posterior"
MSG_HORAS_MEDIA = "Las horas estimadas deben ser múltiplos de 0.5"


def _strip(data: dict) -> dict:
    out = {}
    for k, v in (data or {}).items():
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                v = None
        out[k] = v
    return out


def _normalizar(data: dict) -> dict:
    """Recorta espacios, convierte cadenas vacías a None y deja la prioridad en mayúsculas."""
    data = _strip(data)
    if isinstance(data.get("prioridad"), str):
        data["prioridad"] = data["prioridad"].upper()
    return data


def validar_fecha_no_pasada(value) -> None:
    """Valida la fecha límite del alta: hoy o posterior."""
    if value is not None and value < today_mx():
        raise ValidationError(MSG_FECHA_PASADA)


def _validar_multiplos_media(value) -> None:
    """Las horas estimadas se capturan en múltiplos de 0.5 (value es Decimal)."""
    if value is None:
        return
    doble = value * 2
    if doble != doble.to_integral_value():
        raise ValidationError(MSG_HORAS_MEDIA)


class TareaCreateSchema(Schema):
    """Cuerpo de POST /api/v1/tasks."""

    class Meta:
        unknown = EXCLUDE

    titulo = fields.String(required=True, validate=validate.Length(min=5, max=100))
    descripcion = fields.String(allow_none=True, validate=validate.Length(max=2000))
    cliente_id = fields.Integer(required=True, validate=validate.Range(min=1))
    categoria_id = fields.Integer(required=True, validate=validate.Range(min=1))
    asignado_id = fields.Integer(required=True, validate=validate.Range(min=1))
    fecha_limite = fields.Date(required=True)
    hora_limite = fields.Time(load_default=_time(23, 59))
    prioridad = fields.String(required=True, validate=validate.OneOf(PRIORIDADES))
    horas_estimadas = fields.Decimal(
        allow_none=True, places=1, validate=validate.Range(min=0.5, max=200)
    )
    notificar_cliente = fields.Boolean(load_default=True)

    @pre_load
    def _norm(self, data, **_):
        return _normalizar(data)

    @validates("fecha_limite")
    def _fecha_no_pasada(self, value, **_):
        validar_fecha_no_pasada(value)

    @validates("horas_estimadas")
    def _multiplos_media(self, value, **_):
        _validar_multiplos_media(value)

    @validates_schema
    def _reglas_cruzadas(self, data, **_):
        # No hay reglas cruzadas obligatorias aquí; las de "cliente Activo",
        # "categoría Activa" y "contador Activo" dependen de la BD y se validan en el servicio.
        return


class TareaUpdateSchema(Schema):
    """Cuerpo de PUT /api/v1/tasks/<id> (HU_32).

    Actualización parcial: solo se aplican los campos enviados y cada uno conserva
    las validaciones del alta. `estado` no se edita aquí —lo cambia la HU de mover
    tarea—, por eso se descarta si llega en el cuerpo.

    La regla «fecha límite hoy o posterior» se aplica en el servicio y solo cuando
    la fecha cambia: así se puede editar (por ejemplo, reasignar) una tarea ya
    vencida sin tener que moverla de día.
    """

    class Meta:
        unknown = EXCLUDE

    titulo = fields.String(validate=validate.Length(min=5, max=100))
    descripcion = fields.String(allow_none=True, validate=validate.Length(max=2000))
    cliente_id = fields.Integer(validate=validate.Range(min=1))
    categoria_id = fields.Integer(validate=validate.Range(min=1))
    asignado_id = fields.Integer(validate=validate.Range(min=1))
    fecha_limite = fields.Date()
    hora_limite = fields.Time()
    prioridad = fields.String(validate=validate.OneOf(PRIORIDADES))
    horas_estimadas = fields.Decimal(
        allow_none=True, places=1, validate=validate.Range(min=0.5, max=200)
    )
    notificar_cliente = fields.Boolean()

    @pre_load
    def _norm(self, data, **_):
        return _normalizar(data)

    @validates("horas_estimadas")
    def _multiplos_media(self, value, **_):
        _validar_multiplos_media(value)
