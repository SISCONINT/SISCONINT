"""HU_57-62. Tarifa por hora de cada colaborador (para el costo estimado del dashboard)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class Tarifa(TimestampMixin, SoftDeleteMixin, db.Model):
    """Una tarifa vigente por colaborador. Al cambiarla se sobrescribe (RG-13 deja el rastro)."""

    __tablename__ = "tarifa"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(
        BigId, db.ForeignKey("colaborador.id"), nullable=False, unique=True, index=True
    )
    monto_hora = db.Column(db.Numeric(10, 2), nullable=False)
    moneda = db.Column(db.String(3), nullable=False, default="MXN")
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    colaborador = db.relationship("Colaborador", foreign_keys=[colaborador_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "colaborador_id": self.colaborador_id,
            "monto_hora": float(self.monto_hora),
            "moneda": self.moneda,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
