"""Cola y bitácora de envíos de correo (plantillas y tareas)."""
from app.extensions import db
from app.models.base import BigId, TimestampMixin

ESTATUS_PENDIENTE = "PENDIENTE"
ESTATUS_ENVIADO = "ENVIADO"
ESTATUS_FALLIDO = "FALLIDO"
ESTATUS = (ESTATUS_PENDIENTE, ESTATUS_ENVIADO, ESTATUS_FALLIDO)


class EnvioCorreo(TimestampMixin, db.Model):
    __tablename__ = "envio_correo"

    id = db.Column(BigId, primary_key=True)
    plantilla_id = db.Column(BigId, db.ForeignKey("plantilla_notificacion.id"))
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"))
    destinatario = db.Column(db.String(254), nullable=False)
    estatus = db.Column(db.String(10), nullable=False, default=ESTATUS_PENDIENTE)
    intentos = db.Column(db.SmallInteger, nullable=False, default=0)
    resultado = db.Column(db.Text)
    proximo_intento = db.Column(db.DateTime(timezone=True))
