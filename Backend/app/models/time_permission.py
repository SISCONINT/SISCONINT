"""Permisos para registrar tiempo fuera de plazo (HU_55, módulo 8)."""
from datetime import timedelta

from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

ESTATUS_VIGENTE = "VIGENTE"
ESTATUS_VENCIDO = "VENCIDO"
ESTATUS_REVOCADO = "REVOCADO"
ESTATUS_USADO = "USADO"
ESTATUS = (ESTATUS_VIGENTE, ESTATUS_VENCIDO, ESTATUS_REVOCADO, ESTATUS_USADO)


class PermisoFueraPlazo(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "permiso_fuera_plazo"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    otorgado_por = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False)
    revocado_por = db.Column(BigId, db.ForeignKey("colaborador.id"))
    fecha_inicial = db.Column(db.Date, nullable=False)
    fecha_final = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(300), nullable=False)
    vence_en = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: utcnow() + timedelta(hours=48),
    )
    estatus = db.Column(db.String(10), nullable=False, default=ESTATUS_VIGENTE, index=True)
    revocado_en = db.Column(db.DateTime(timezone=True))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
