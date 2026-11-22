"""Códigos de recuperación de contraseña (HU_10)."""
from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId


class CodigoRecuperacion(db.Model):
    __tablename__ = "codigo_recuperacion"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    codigo_hash = db.Column(db.String(255), nullable=False)
    vence_en = db.Column(db.DateTime(timezone=True), nullable=False)
    intentos_fallidos = db.Column(db.SmallInteger, nullable=False, default=0)
    usado_en = db.Column(db.DateTime(timezone=True))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
