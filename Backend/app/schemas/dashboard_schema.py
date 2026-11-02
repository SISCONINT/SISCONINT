"""HU_79-85. Schemas del dashboard: filtros y contrato de salida."""
from marshmallow import (
    EXCLUDE,
    Schema,
    ValidationError,
    fields,
    pre_load,
    validate,
    validates_schema,
)

PERIODOS = ("HOY", "SEMANA", "MES_ACTUAL", "MES_ANTERIOR", "PERSONALIZADO")

MSG_PERIODO = (
    "El periodo debe ser HOY, SEMANA, MES_ACTUAL, MES_ANTERIOR o PERSONALIZADO"
)
MSG_RANGO_REQUERIDO = "El rango personalizado requiere fecha_desde y fecha_hasta"
MSG_RANGO_INVALIDO = "La fecha inicial no puede ser posterior a la final"
MSG_RANGO_MAXIMO = "El rango personalizado no puede superar 12 meses"
MSG_FECHAS_SOLO_PERSONALIZADO = (
    "Solo el rango personalizado usa fecha_desde y fecha_hasta"
)

# 12 meses equivalen a 365 o 366 días según el año.
MAX_DIAS_RANGO = 366

_ALIAS_PERIODO = {
    "HOY": "HOY",
    "DIA": "HOY",
    "SEMANA": "SEMANA",
    "ESTA_SEMANA": "SEMANA",
    "SEMANA_ACTUAL": "SEMANA",
    "MES": "MES_ACTUAL",
    "ACTUAL": "MES_ACTUAL",
    "MES_ACTUAL": "MES_ACTUAL",
    "ANTERIOR": "MES_ANTERIOR",
    "MES_ANTERIOR": "MES_ANTERIOR",
    "PERSONALIZADO": "PERSONALIZADO",
    "RANGO": "PERSONALIZADO",
    "CUSTOM": "PERSONALIZADO",
}


class DashboardQuerySchema(Schema):
    """Query params de GET /api/v1/dashboard y /api/v1/dashboard/me.

    `periodo` acepta las opciones de HU_84 y algunos alias en español. Si llegan
    fechas sin periodo se asume rango personalizado. El rango máximo es de 12 meses.
    """

    class Meta:
        unknown = EXCLUDE

    periodo = fields.String(
        load_default="MES_ACTUAL",
        validate=validate.OneOf(PERIODOS, error=MSG_PERIODO),
        error_messages={"invalid": MSG_PERIODO},
    )
    fecha_desde = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    fecha_hasta = fields.Date(
        load_default=None,
        allow_none=True,
        error_messages={"invalid": "Fecha no válida (usa AAAA-MM-DD)"},
    )
    cliente = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El cliente debe ser un id válido"),
        error_messages={"invalid": "El cliente debe ser un id válido"},
    )
    colaborador = fields.Integer(
        load_default=None,
        allow_none=True,
        validate=validate.Range(min=1, error="El colaborador debe ser un id válido"),
        error_messages={"invalid": "El colaborador debe ser un id válido"},
    )

    @pre_load
    def _normalizar(self, data, **_):
        """Recorta espacios, descarta parámetros vacíos y normaliza el periodo."""
        limpio = {}
        for clave, valor in (data or {}).items():
            if isinstance(valor, str):
                valor = valor.strip()
                if valor == "":
                    continue
                if clave == "periodo":
                    valor = _ALIAS_PERIODO.get(valor.upper(), valor.upper())
            limpio[clave] = valor

        if "periodo" not in limpio and (
            "fecha_desde" in limpio or "fecha_hasta" in limpio
        ):
            limpio["periodo"] = "PERSONALIZADO"
        return limpio

    @validates_schema
    def _validar_rango(self, data, **_):
        periodo = data.get("periodo")
        desde = data.get("fecha_desde")
        hasta = data.get("fecha_hasta")

        if periodo != "PERSONALIZADO":
            if desde is not None or hasta is not None:
                raise ValidationError(
                    MSG_FECHAS_SOLO_PERSONALIZADO, field_name="fecha_desde"
                )
            return

        if desde is None or hasta is None:
            raise ValidationError(MSG_RANGO_REQUERIDO, field_name="fecha_desde")

        if desde > hasta:
            raise ValidationError(MSG_RANGO_INVALIDO, field_name="fecha_desde")

        if (hasta - desde).days + 1 > MAX_DIAS_RANGO:
            raise ValidationError(MSG_RANGO_MAXIMO, field_name="fecha_hasta")


# ---------------------------------------------------------------------------
# Salida
# ---------------------------------------------------------------------------
class PeriodoSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    tipo = fields.String()
    etiqueta = fields.String()
    desde = fields.Date()
    hasta = fields.Date()


class PeriodoAnteriorSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    desde = fields.Date()
    hasta = fields.Date()


class FiltrosAplicadosSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente_id = fields.Integer(allow_none=True)
    cliente_nombre = fields.String(allow_none=True)
    colaborador_id = fields.Integer(allow_none=True)
    colaborador_nombre = fields.String(allow_none=True)


class HorasCardSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    horas = fields.Float()
    minutos = fields.Integer()
    variacion_porcentaje = fields.Float(allow_none=True)
    horas_periodo_anterior = fields.Float()


class CostoEstimadoSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    disponible = fields.Boolean()
    monto = fields.Float(allow_none=True)
    horas_sin_tarifa = fields.Float()
    mensaje = fields.String()


class TarjetasSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    horas_totales = fields.Nested(HorasCardSchema)
    tareas_activas = fields.Integer()
    tareas_vencidas = fields.Integer()
    costo_estimado = fields.Nested(CostoEstimadoSchema, allow_none=True)


class TarjetasPersonalSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    horas_totales = fields.Nested(HorasCardSchema)
    tareas_activas = fields.Integer()
    tareas_vencidas = fields.Integer()


class EmpleadoHorasSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    colaborador_id = fields.Integer()
    nombre = fields.String()
    minutos = fields.Integer()
    horas = fields.Float()


class ClienteHorasSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    cliente_id = fields.Integer()
    nombre = fields.String()
    minutos = fields.Integer()
    horas = fields.Float()


class CategoriaHorasSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    categoria_id = fields.Integer()
    nombre = fields.String()
    minutos = fields.Integer()
    horas = fields.Float()
    porcentaje = fields.Float()


class EstadoTareasSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    POR_HACER = fields.Integer()
    EN_PROGRESO = fields.Integer()
    EN_REVISION = fields.Integer()
    COMPLETADO = fields.Integer()
    vencidas = fields.Integer()
    total = fields.Integer()


class DashboardSchema(Schema):
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
    sin_informacion = fields.Boolean()
    mensaje = fields.String(allow_none=True)


class DashboardPersonalSchema(Schema):
    class Meta:
        unknown = EXCLUDE

    periodo = fields.Nested(PeriodoSchema)
    periodo_anterior = fields.Nested(PeriodoAnteriorSchema)
    tarjetas = fields.Nested(TarjetasPersonalSchema)
    tiempo_por_cliente = fields.Nested(ClienteHorasSchema, many=True)
    distribucion_por_categoria = fields.Nested(CategoriaHorasSchema, many=True)
    estado_tareas = fields.Nested(EstadoTareasSchema)
    sin_informacion = fields.Boolean()
    mensaje = fields.String(allow_none=True)
