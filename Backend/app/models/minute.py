"""Minutas y acuerdos: bitácora de reuniones ligada opcionalmente a un cliente o tarea."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class Minuta(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "minuta"

    id = db.Column(BigId, primary_key=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=True, index=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=True, index=True)
    titulo = db.Column(db.String(150), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    participantes = db.Column(db.String(300))
    acuerdos = db.Column(db.Text, nullable=False)
    creador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False)
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    cliente = db.relationship("Cliente")
    tarea = db.relationship("Tarea")
    creador = db.relationship("Colaborador", foreign_keys=[creador_id])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre_completo if self.cliente else None,
            "tarea_id": self.tarea_id,
            "tarea_titulo": self.tarea.titulo if self.tarea else None,
            "titulo": self.titulo,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "participantes": self.participantes,
            "acuerdos": self.acuerdos,
            "creador_id": self.creador_id,
            "creador_nombre": self.creador.nombre_completo if self.creador else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
