from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

# Estatus (coinciden con el CHECK de permiso_atencion_cliente)
ESTATUS_VIGENTE = "VIGENTE"
ESTATUS_VENCIDO = "VENCIDO"
ESTATUS_REVOCADO = "REVOCADO"


class PermisoAtencionCliente(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_17-19, RG-12. Permiso temporal para que un Contador atienda un cliente no asignado.

    Máximo 30 días naturales (CHECK en la base). El estatus VIGENTE se evalúa
    también contra fecha_inicio/fecha_fin en el repositorio: no dependemos del job
    que lo marca VENCIDO.
    """

    __tablename__ = "permiso_atencion_cliente"

    id = db.Column(BigId, primary_key=True)
    contador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    otorgado_por = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False)
    revocado_por = db.Column(BigId, db.ForeignKey("colaborador.id"))
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    motivo = db.Column(db.String(300))
    estatus = db.Column(db.String(10), nullable=False, default=ESTATUS_VIGENTE, index=True)
    revocado_en = db.Column(db.DateTime(timezone=True))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    @property
    def vigente(self) -> bool:
        from app.core.datetime_utils import today_mx

        if self.estatus != ESTATUS_VIGENTE or self.deleted_at is not None:
            return False
        hoy = today_mx()
        return self.fecha_inicio <= hoy <= self.fecha_fin