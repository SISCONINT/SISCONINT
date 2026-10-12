"""HU_25. Schemas del catálogo de proyectos y actividades (solo lectura)."""
from marshmallow import EXCLUDE, Schema, fields, pre_load


class CategoriaQuerySchema(Schema):
    """Query params de GET /catalog/categories.

    - q: búsqueda parcial por nombre (categoría o subcategoría), opcional.
    - solo_activas: 'true' / '1' -> solo entradas activas; por defecto false.
    """

    class Meta:
        unknown = EXCLUDE

    q = fields.String(load_default=None, allow_none=True)
    solo_activas = fields.Boolean(load_default=False)

    @pre_load
    def _normalize(self, data, **_kwargs):
        data = dict(data or {})
        q = data.get("q")
        if isinstance(q, str):
            q = q.strip()
            data["q"] = q or None
        # Marshmallow ya entiende 'true'/'false'/'1'/'0' como boolean, pero normalizamos por si viene ''.
        val = data.get("solo_activas")
        if val in ("", None):
            data["solo_activas"] = False
        return data


class CategoriaItemSchema(Schema):
    """Salida de una entrada del catálogo. `subcategorias` solo se llena en las categorías raíz."""

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    nombre = fields.String()
    activa = fields.Boolean()
    orden = fields.Integer()
    subcategorias = fields.List(fields.Dict(), required=False)


class CategoriaArbolSchema(Schema):
    """Lista completa de categorías raíz, cada una con sus subcategorías."""

    class Meta:
        unknown = EXCLUDE

    data = fields.List(fields.Nested(CategoriaItemSchema))