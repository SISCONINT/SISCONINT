"""Plantillas de correo administrables (asunto + cuerpo con placeholders {nombre}, etc.)."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class PlantillaCorreo(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "plantilla_correo"

    id = db.Column(BigId, primary_key=True)
    clave = db.Column(db.String(50), nullable=False, unique=True)
    nombre = db.Column(db.String(150), nullable=False)
    asunto = db.Column(db.String(200), nullable=False)
    cuerpo = db.Column(db.Text, nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "clave": self.clave,
            "nombre": self.nombre,
            "asunto": self.asunto,
            "cuerpo": self.cuerpo,
            "activa": self.activa,
        }
