"""HU_34-40. Schemas de subtareas y comentarios de una tarea."""
from marshmallow import EXCLUDE, Schema, fields, pre_load, validate


def _limpiar(data: dict) -> dict:
    limpio = {}
    for clave, valor in (data or {}).items():
        if isinstance(valor, str):
            valor = valor.strip()
            if valor == "":
                valor = None
        limpio[clave] = valor
    return limpio


class SubtareaCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    titulo = fields.String(
        required=True,
        validate=validate.Length(min=1, max=150, error="El título debe tener entre 1 y 150 caracteres"),
        error_messages={"required": "Campo obligatorio"},
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class SubtareaUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    titulo = fields.String(
        validate=validate.Length(min=1, max=150, error="El título debe tener entre 1 y 150 caracteres")
    )
    completada = fields.Boolean()

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class ComentarioCreateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    texto = fields.String(
        required=True,
        validate=validate.Length(min=1, max=1000, error="El comentario debe tener entre 1 y 1,000 caracteres"),
        error_messages={"required": "Campo obligatorio"},
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class ComentarioUpdateSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    texto = fields.String(
        required=True,
        validate=validate.Length(min=1, max=1000, error="El comentario debe tener entre 1 y 1,000 caracteres"),
        error_messages={"required": "Campo obligatorio"},
    )

    @pre_load
    def _norm(self, data, **_):
        return _limpiar(data)


class TareaOptionsQuerySchema(Schema):
    """Query params de GET /api/v1/tasks/options.

    `mias` limita el selector a las tareas asignadas al usuario autenticado (lo
    usan el temporizador y el registro manual). `incluir_completadas` permite
    consultar tareas cerradas para minutas o filtros históricos.
    """

    class Meta:
        unknown = EXCLUDE

    mias = fields.Boolean(load_default=False)
    incluir_completadas = fields.Boolean(load_default=False)

    @pre_load
    def _norm(self, data, **_):
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip().lower()
                if valor == "":
                    continue
                if clave in ("mias", "incluir_completadas"):
                    valor = valor in ("1", "true", "si", "sí", "yes")
            limpio[clave] = valor
        return limpio


class TareaOpcionSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    titulo = fields.String()
    cliente_id = fields.Integer()
    cliente_nombre = fields.String(allow_none=True)
    asignado_id = fields.Integer()
    asignado_nombre = fields.String(allow_none=True)
    estado = fields.String()
    fecha_limite = fields.Date()
