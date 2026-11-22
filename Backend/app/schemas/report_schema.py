"""Contrato de salida de los reportes ejecutivos."""
from marshmallow import EXCLUDE, Schema, fields

from app.schemas.dashboard_schema import (
    CategoriaHorasSchema,
    ClienteHorasSchema,
    EmpleadoHorasSchema,
    EstadoTareasSchema,
    FiltrosAplicadosSchema,
    PeriodoAnteriorSchema,
    PeriodoSchema,
    TarjetasSchema,
)


class ReporteEjecutivoSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    periodo = fields.Nested(PeriodoSchema)
    periodo_anterior = fields.Nested(PeriodoAnteriorSchema)
    filtros = fields.Nested(FiltrosAplicadosSchema)
    tarjetas = fields.Nested(TarjetasSchema)
    tiempo_por_empleado = fields.Nested(EmpleadoHorasSchema, many=True)
    tiempo_por_cliente = fields.Nested(ClienteHorasSchema, many=True)
    distribucion_por_categoria = fields.Nested(CategoriaHorasSchema, many=True)
    estado_tareas = fields.Nested(EstadoTareasSchema)
    tareas_completadas = fields.Integer()
    generado_en = fields.DateTime()
    sin_informacion = fields.Boolean()
    mensaje = fields.String(allow_none=True)
