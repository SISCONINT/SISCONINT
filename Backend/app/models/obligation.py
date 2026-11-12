"""Obligaciones fiscales periódicas de un cliente (declaraciones recurrentes)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

PERIODICIDAD_MENSUAL = "MENSUAL"
PERIODICIDAD_BIMESTRAL = "BIMESTRAL"
PERIODICIDAD_ANUAL = "ANUAL"
PERIODICIDADES = (PERIODICIDAD_MENSUAL, PERIODICIDAD_BIMESTRAL, PERIODICIDAD_ANUAL)


class Obligacion(TimestampMixin, SoftDeleteMixin, db.Model):
    """Una obligación recurrente (p. ej. "Declaración mensual de IVA") de un cliente."""

    __tablename__ = "obligacion"

    id = db.Column(BigId, primary_key=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    categoria_id = db.Column(BigId, db.ForeignKey("categoria_proyecto.id"), nullable=True)
    nombre = db.Column(db.String(150), nullable=False)
    periodicidad = db.Column(db.String(10), nullable=False, default=PERIODICIDAD_MENSUAL)
    dia_limite = db.Column(db.Integer, nullable=False)  # día del mes/periodo en que vence
    activa = db.Column(db.Boolean, nullable=False, default=True)
    notas = db.Column(db.String(300))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    cliente = db.relationship("Cliente")
    categoria = db.relationship("CategoriaProyecto")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre_completo if self.cliente else None,
            "categoria_id": self.categoria_id,
            "categoria_nombre": self.categoria.nombre if self.categoria else None,
            "nombre": self.nombre,
            "periodicidad": self.periodicidad,
            "dia_limite": self.dia_limite,
            "activa": self.activa,
            "notas": self.notas,
        }
