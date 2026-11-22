"""HU_57-62. Tarifa por hora según el nivel de escalafón (para el costo estimado)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class TarifaNivel(TimestampMixin, SoftDeleteMixin, db.Model):
    """Una tarifa vigente por nivel. El histórico se conserva con vigencias."""

    __tablename__ = "tarifa_nivel"

    id = db.Column(BigId, primary_key=True)
    nivel = db.Column(db.String(10), nullable=False, index=True)
    monto_hora_mxn = db.Column(db.Numeric(10, 2), nullable=False)
    vigencia_inicio = db.Column(db.Date, nullable=False, index=True)
    vigencia_fin = db.Column(db.Date)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nivel": self.nivel,
            "monto_hora_mxn": float(self.monto_hora_mxn),
            "vigencia_inicio": self.vigencia_inicio.isoformat() if self.vigencia_inicio else None,
            "vigencia_fin": self.vigencia_fin.isoformat() if self.vigencia_fin else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
