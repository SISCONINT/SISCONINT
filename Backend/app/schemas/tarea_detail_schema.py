"""HU_31. Schema del detalle de tarea."""
from marshmallow import EXCLUDE, Schema, fields


class SubtareaDetalleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    titulo = fields.String()
    completada = fields.Boolean()
    completada_por = fields.Integer(allow_none=True)
    completada_por_nombre = fields.String(allow_none=True)
    completada_en = fields.DateTime(allow_none=True)
    created_at = fields.DateTime()


class ComentarioDetalleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    autor_id = fields.Integer()
    autor_nombre = fields.String(allow_none=True)
    texto = fields.String()
    editado = fields.Boolean()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class HistorialEstadoDetalleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    estado_anterior = fields.String(allow_none=True)
    estado_nuevo = fields.String()
    usuario_id = fields.Integer(allow_none=True)
    usuario_nombre = fields.String(allow_none=True)
    created_at = fields.DateTime()


class SubtareasDetalleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    items = fields.List(fields.Nested(SubtareaDetalleSchema))
    total = fields.Integer()
    completadas = fields.Integer()
    avance = fields.String()
    porcentaje = fields.Float()


class TiempoColaboradorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    colaborador_id = fields.Integer()
    colaborador_nombre = fields.String(allow_none=True)
    minutos = fields.Integer()
    horas = fields.Float()


class TiempoDetalleSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    total_minutos = fields.Integer()
    total_horas = fields.Float()
    horas_estimadas = fields.Float(allow_none=True)
    porcentaje_registrado = fields.Float(allow_none=True)
    por_colaborador = fields.List(fields.Nested(TiempoColaboradorSchema))


class TareaDetailSchema(Schema):
    """Todos los campos de la tarea, su contexto y sus colecciones (HU_31).

    Las fechas y horas viajan en ISO 8601; el formato DD/MM/AAAA se aplica en el
    frontend (RG-04). El semáforo y el tiempo se calculan en el servidor.
    """

    class Meta:
        unknown = EXCLUDE

    id = fields.Integer()
    titulo = fields.String()
    descripcion = fields.String(allow_none=True)
    cliente_id = fields.Integer()
    cliente_nombre = fields.String(allow_none=True)
    categoria_id = fields.Integer()
    categoria_nombre = fields.String(allow_none=True)
    categoria_padre_nombre = fields.String(allow_none=True)
    asignado_id = fields.Integer()
    asignado_nombre = fields.String(allow_none=True)
    creador_id = fields.Integer(allow_none=True)
    creador_nombre = fields.String(allow_none=True)
    obligacion_id = fields.Integer(allow_none=True)
    periodo = fields.String(allow_none=True)
    fecha_limite = fields.Date()
    hora_limite = fields.String(allow_none=True)
    prioridad = fields.String()
    estado = fields.String()
    horas_estimadas = fields.Float(allow_none=True)
    notificar_cliente = fields.Boolean()
    cliente_notificado = fields.Boolean()
    completada_en = fields.DateTime(allow_none=True)
    completada_por = fields.Integer(allow_none=True)
    completada_por_nombre = fields.String(allow_none=True)
    created_by = fields.Integer(allow_none=True)
    updated_by = fields.Integer(allow_none=True)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    semaforo = fields.String()
    dias_restantes = fields.Integer()
    subtareas = fields.Nested(SubtareasDetalleSchema)
    comentarios = fields.List(fields.Nested(ComentarioDetalleSchema))
    historial_estados = fields.List(fields.Nested(HistorialEstadoDetalleSchema))
    tiempo = fields.Nested(TiempoDetalleSchema)
