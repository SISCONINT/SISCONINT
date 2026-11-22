"""Obligaciones fiscales periódicas de un cliente (declaraciones recurrentes)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin
from app.models.task import PRIORIDADES

PERIODICIDAD_SEMANAL = "SEMANAL"
PERIODICIDAD_QUINCENAL = "QUINCENAL"
PERIODICIDAD_MENSUAL = "MENSUAL"
PERIODICIDAD_BIMESTRAL = "BIMESTRAL"
PERIODICIDAD_TRIMESTRAL = "TRIMESTRAL"
PERIODICIDAD_SEMESTRAL = "SEMESTRAL"
PERIODICIDAD_ANUAL = "ANUAL"
PERIODICIDADES = (
    PERIODICIDAD_SEMANAL,
    PERIODICIDAD_QUINCENAL,
    PERIODICIDAD_MENSUAL,
    PERIODICIDAD_BIMESTRAL,
    PERIODICIDAD_TRIMESTRAL,
    PERIODICIDAD_SEMESTRAL,
    PERIODICIDAD_ANUAL,
)


class Obligacion(TimestampMixin, SoftDeleteMixin, db.Model):
    """Una obligación recurrente (p. ej. "Declaración mensual de IVA") de un cliente."""

    __tablename__ = "obligacion_periodica"

    id = db.Column(BigId, primary_key=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    categoria_id = db.Column(
        BigId, db.ForeignKey("categoria_proyecto.id"), nullable=False, index=True
    )
    responsable_id = db.Column(
        BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True
    )
    periodicidad = db.Column(db.String(12), nullable=False, default=PERIODICIDAD_MENSUAL)
    dia_vencimiento = db.Column(db.SmallInteger, nullable=False)
    fecha_inicio = db.Column(db.Date, nullable=False)
    prioridad = db.Column(db.String(5), nullable=False, default="MEDIA")
    activa = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    cliente = db.relationship("Cliente")
    categoria = db.relationship("CategoriaProyecto")
    responsable = db.relationship("Colaborador", foreign_keys=[responsable_id])

    __table_args__ = (
        db.UniqueConstraint(
            "cliente_id", "categoria_id", "periodicidad",
            name="uq_obligacion_cliente_cat_period",
        ),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre_completo if self.cliente else None,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria.nombre if self.categoria else None,
            "responsable_id": self.responsable_id,
            "responsable_nombre": self.responsable.nombre_completo if self.responsable else None,
            "periodicidad": self.periodicidad,
            "dia_vencimiento": self.dia_vencimiento,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "prioridad": self.prioridad,
            "activa": self.activa,
        }
