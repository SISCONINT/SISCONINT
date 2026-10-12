from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId

# tipo (valores libres; los jobs van agregando)
TIPO_CLIENTE_NUEVO = "CLIENTE_NUEVO"
TIPO_ASIGNACION = "ASIGNACION"
TIPO_VENCIMIENTO = "VENCIMIENTO"
TIPO_CAMBIO_ESTADO = "CAMBIO_ESTADO"
TIPO_COMENTARIO = "COMENTARIO"


class Notificacion(db.Model):
    """HU_65, 69, 71-73. Bandeja in-app. Sin soft delete ni updated_at: es un log."""

    __tablename__ = "notificacion"

    id = db.Column(BigId, primary_key=True)
    usuario_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    tipo = db.Column(db.String(40), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    mensaje = db.Column(db.String(500), nullable=False)
    entidad_tipo = db.Column(db.String(10))
    entidad_id = db.Column(BigId)
    leida = db.Column(db.Boolean, nullable=False, default=False)
    clave_unica = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "mensaje": self.mensaje,
            "entidad_tipo": self.entidad_tipo,
            "entidad_id": self.entidad_id,
            "leida": self.leida,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }