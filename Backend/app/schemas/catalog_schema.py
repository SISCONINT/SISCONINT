"""HU_25. Schemas del catálogo de proyectos y actividades (solo lectura)."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


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


def _limpiar(data: dict) -> dict:
    limpio = {}
    for clave, valor in (data or {}).items():
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                valor = None
        limpio[clave] = valor
    return limpio


class CategoriaCreateSchema(Schema):
    """Cuerpo de POST /api/v1/catalog (HU_26).

    `padre_id` vacío o ausente crea una categoría raíz; con valor crea una
    subcategoría (el árbol solo admite dos niveles).
    """

    class Meta:
        unknown = EXCLUDE

    nombre = fields.String(
        required=True,
        validate=validate.Length(min=1, max=80, error="El nombre debe tener entre 1 y 80 caracteres"),
        error_messages={"required": "Campo obligatorio"},
    )
    padre_id = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="La categoría padre no es válida"),
    )
    orden = fields.Integer(load_default=0, validate=validate.Range(min=0, max=9999))
    activa = fields.Boolean(load_default=True)

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class CategoriaUpdateSchema(Schema):
    """Cuerpo de PUT /api/v1/catalog/<id> (HU_27). Actualización parcial."""

    class Meta:
        unknown = EXCLUDE

    nombre = fields.String(
        validate=validate.Length(min=1, max=80, error="El nombre debe tener entre 1 y 80 caracteres")
    )
    orden = fields.Integer(validate=validate.Range(min=0, max=9999))
    activa = fields.Boolean()

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)