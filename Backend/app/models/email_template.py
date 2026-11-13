"""Plantillas de correo administrables (asunto + cuerpo con placeholders)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

CLAVE_ASIGNACION = "ASIGNACION"
CLAVE_VENCIMIENTO = "VENCIMIENTO"
CLAVE_COMPLETADA = "COMPLETADA"
CLAVES = (CLAVE_ASIGNACION, CLAVE_VENCIMIENTO, CLAVE_COMPLETADA)


class PlantillaNotificacion(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "plantilla_notificacion"

    id = db.Column(BigId, primary_key=True)
    clave = db.Column(db.String(40), nullable=False, unique=True)
    asunto = db.Column(db.String(150), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    asunto_original = db.Column(db.String(150), nullable=False)
    cuerpo_original = db.Column(db.Text, nullable=False)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clave": self.clave,
            "asunto": self.asunto,
            "cuerpo": self.cuerpo,
            "asunto_original": self.asunto_original,
            "cuerpo_original": self.cuerpo_original,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
