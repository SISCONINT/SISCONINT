from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

# tipo (coinciden con el CHECK de registro_tiempo)
TIPO_TIMER = "TIMER"
TIPO_MANUAL = "MANUAL"


class TemporizadorActivo(TimestampMixin, SoftDeleteMixin, db.Model):
    """Un temporizador en curso por colaborador (módulo 8). HU_04 consulta si existe antes del logout."""

    __tablename__ = "temporizador_activo"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(
        BigId, db.ForeignKey("colaborador.id"), nullable=False, unique=True, index=True
    )
    # FK diferida: la agrega HU_29 (modelo Tarea) al registrar la relación completa.
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=False)
    iniciado_en = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class RegistroTiempo(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_50-54. Espejo de la tabla registro_tiempo.

    El costo se calcula con `nivel_escalafon` vigente al momento de registrar (HU_62),
    por eso se persiste el grado aquí y no se lee del colaborador.
    """

    __tablename__ = "registro_tiempo"

    id = db.Column(BigId, primary_key=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=False, index=True)
    colaborador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    # FK diferida: permiso_fuera_plazo llega con HU_55 (Módulo 8). El id igual se persiste.
    permiso_fuera_plazo_id = db.Column(BigId)
    fecha = db.Column(db.Date, nullable=False, index=True)
    duracion_minutos = db.Column(db.Integer, nullable=False)
    tipo = db.Column(db.String(6), nullable=False)
    descripcion = db.Column(db.String(500), nullable=False)
    nivel_escalafon = db.Column(db.String(10), nullable=False)
    cierre_automatico = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))