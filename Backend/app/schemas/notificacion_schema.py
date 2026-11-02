"""HU_71-73. Schemas de la bandeja de notificaciones."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate

_VALORES_LEIDA = {"true": True, "1": True, "leida": True, "leidas": True, "si": True}
_VALORES_NO_LEIDA = {
    "false": False,
    "0": False,
    "no_leida": False,
    "no_leidas": False,
    "no": False,
}


def _a_booleano(valor: str):
    """Acepta true/false, 1/0 y las variantes en español que manda el frontend."""
    clave = valor.strip().lower()
    if clave in _VALORES_LEIDA:
        return True
    if clave in _VALORES_NO_LEIDA:
        return False
    return valor  # Marshmallow responde 422 con el mensaje del campo


class NotificacionQuerySchema(Schema):
    """Query params de GET /api/v1/notifications (HU_71).

    `leida` es opcional: sin filtro se devuelven leídas y no leídas. `page` es la
    única paginación aceptada porque RG-07 fija 20 registros por página.
    """

    class Meta:
        unknown = EXCLUDE

    leida = fields.Boolean(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "El filtro leída debe ser true o false"},
    )
    page = fields.Integer(
        load_default=1,
        validate=validate.Range(min=1, error="La página debe ser 1 o mayor"),
        error_messages={"invalid": "La página debe ser un número entero"},
    )

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios, descarta parámetros vacíos y normaliza el filtro leída."""
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue  # el frontend puede mandar ?leida=&page=
                if clave == "leida":
                    valor = _a_booleano(valor)
            limpio[clave] = valor
        return limpio


class NotificacionItemSchema(Schema):
    """Notificación de la bandeja (HU_71).

    `enlace` es la ruta del frontend para abrir la tarea o el cliente relacionado;
    se deriva de `entidad_tipo` y `entidad_id`.
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    tipo = fields.String()
    titulo = fields.String()
    mensaje = fields.String()
    entidad_tipo = fields.String(allow_none=True)
    entidad_id = fields.Integer(allow_none=True)
    enlace = fields.String(allow_none=True)
    leida = fields.Boolean()
    created_at = fields.DateTime()


class NotificacionLeidaSchema(Schema):
    """Respuesta de HU_72: la notificación actualizada y el contador de no leídas."""

    class Meta:
        unknown = EXCLUDE

    notificacion = fields.Nested(NotificacionItemSchema)
    no_leidas = fields.Integer()


class NotificacionLeidasTodasSchema(Schema):
    """Respuesta de HU_73: cuántas se marcaron y el contador (siempre 0)."""

    class Meta:
        unknown = EXCLUDE

    actualizadas = fields.Integer()
    no_leidas = fields.Integer()
