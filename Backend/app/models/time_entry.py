from datetime import date

from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class TemporizadorActivo(TimestampMixin, SoftDeleteMixin, db.Model):
    """Un temporizador en curso por colaborador (módulo 8). HU_04 consulta si existe antes del logout."""

    __tablename__ = "temporizador_activo"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(
        BigId, db.ForeignKey("colaborador.id"), nullable=False, unique=True, index=True
    )
    # Sin FK a tarea: esa entidad llega con el módulo de tareas; el id igual se guarda.
    tarea_id = db.Column(BigId)
    iniciado_en = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class RegistroTiempo(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_08 / HU_62: el grado se copia al registrar; un cambio posterior no reescribe el histórico."""

    __tablename__ = "registro_tiempo"

    id = db.Column(BigId, primary_key=True)
    colaborador_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    grado_escalafon = db.Column(db.String(10), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
