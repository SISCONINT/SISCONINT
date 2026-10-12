from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

# Estados (coinciden con el CHECK de la tabla tarea)
ESTADO_POR_HACER = "POR_HACER"
ESTADO_EN_PROGRESO = "EN_PROGRESO"
ESTADO_EN_REVISION = "EN_REVISION"
ESTADO_COMPLETADO = "COMPLETADO"
ESTADOS = (ESTADO_POR_HACER, ESTADO_EN_PROGRESO, ESTADO_EN_REVISION, ESTADO_COMPLETADO)

# Prioridades (CHECK de la tabla tarea)
PRIORIDAD_BAJA = "BAJA"
PRIORIDAD_MEDIA = "MEDIA"
PRIORIDAD_ALTA = "ALTA"
PRIORIDADES = (PRIORIDAD_BAJA, PRIORIDAD_MEDIA, PRIORIDAD_ALTA)


class Tarea(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_29-33, HU_41-43. Espejo de la tabla tarea del esquema oficial.

    Solo columnas + las constantes de estado que ya usan otras HU (HU_12).
    Las relaciones (subtareas, comentarios, historial) llegan en sus HU.
    """

    __tablename__ = "tarea"

    id = db.Column(BigId, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    categoria_id = db.Column(BigId, db.ForeignKey("categoria_proyecto.id"), nullable=False, index=True)
    asignado_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    creador_id = db.Column(BigId, db.ForeignKey("colaborador.id"))
    obligacion_id = db.Column(BigId, db.ForeignKey("obligacion_periodica.id"))
    periodo = db.Column(db.String(20))
    fecha_limite = db.Column(db.Date, nullable=False, index=True)
    hora_limite = db.Column(db.Time, nullable=False, default="23:59")
    prioridad = db.Column(db.String(5), nullable=False)
    estado = db.Column(db.String(12), nullable=False, default=ESTADO_POR_HACER, index=True)
    horas_estimadas = db.Column(db.Numeric(4, 1))
    notificar_cliente = db.Column(db.Boolean, nullable=False, default=True)
    cliente_notificado = db.Column(db.Boolean, nullable=False, default=False)
    completada_en = db.Column(db.DateTime(timezone=True))
    completada_por = db.Column(BigId, db.ForeignKey("colaborador.id"))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    @property
    def activa(self) -> bool:
        return self.estado != ESTADO_COMPLETADO and self.deleted_at is None