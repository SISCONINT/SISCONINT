from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin
from app.core.datetime_utils import utcnow

# Estados (coinciden con el CHECK de la tabla tarea)
ESTADO_POR_HACER = "POR_HACER"
ESTADO_EN_PROGRESO = "EN_PROGRESO"
ESTADO_EN_REVISION = "EN_REVISION"
ESTADO_COMPLETADO = "COMPLETADO"
ESTADOS = (ESTADO_POR_HACER, ESTADO_EN_PROGRESO, ESTADO_EN_REVISION, ESTADO_COMPLETADO)

# Prioridades (CHECK de la tabla tarea)
PRIORIDAD_BAJA = "BAJA"
PRIORIDAD_MEDIA = "MEDIA"
PRIORIDAD_ALTA = "ALTA"
PRIORIDADES = (PRIORIDAD_BAJA, PRIORIDAD_MEDIA, PRIORIDAD_ALTA)


class Tarea(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_29-33, HU_41-43. Espejo de la tabla tarea del esquema oficial."""

    __tablename__ = "tarea"

    id = db.Column(BigId, primary_key=True)
    titulo = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=False, index=True)
    categoria_id = db.Column(BigId, db.ForeignKey("categoria_proyecto.id"), nullable=False, index=True)
    asignado_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    creador_id = db.Column(BigId, db.ForeignKey("colaborador.id"))
    # FK diferida: obligacion_periodica llega con HU_20 (Módulo 4). El id igual se persiste.
    obligacion_id = db.Column(BigId)
    periodo = db.Column(db.String(20))
    fecha_limite = db.Column(db.Date, nullable=False, index=True)
    hora_limite = db.Column(db.Time, nullable=False, default="23:59")
    prioridad = db.Column(db.String(5), nullable=False)
    estado = db.Column(db.String(12), nullable=False, default=ESTADO_POR_HACER, index=True)
    horas_estimadas = db.Column(db.Numeric(4, 1))
    notificar_cliente = db.Column(db.Boolean, nullable=False, default=True)
    cliente_notificado = db.Column(db.Boolean, nullable=False, default=False)
    completada_en = db.Column(db.DateTime(timezone=True))
    completada_por = db.Column(BigId, db.ForeignKey("colaborador.id"))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    @property
    def activa(self) -> bool:
        return self.estado != ESTADO_COMPLETADO and self.deleted_at is None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "cliente_id": self.cliente_id,
            "categoria_id": self.categoria_id,
            "asignado_id": self.asignado_id,
            "creador_id": self.creador_id,
            "fecha_limite": self.fecha_limite.isoformat() if self.fecha_limite else None,
            "hora_limite": self.hora_limite.strftime("%H:%M") if self.hora_limite else None,
            "prioridad": self.prioridad,
            "estado": self.estado,
            "horas_estimadas": float(self.horas_estimadas) if self.horas_estimadas is not None else None,
            "notificar_cliente": self.notificar_cliente,
            "completada_en": self.completada_en.isoformat() if self.completada_en else None,
            "completada_por": self.completada_por,
        }


class HistorialEstadoTarea(db.Model):
    """HU_31, HU_43. Bitácora de cambios de estado (quién, cuándo, de qué a qué)."""

    __tablename__ = "historial_estado_tarea"

    id = db.Column(BigId, primary_key=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=False, index=True)
    estado_anterior = db.Column(db.String(12))
    estado_nuevo = db.Column(db.String(12), nullable=False)
    usuario_id = db.Column(BigId, db.ForeignKey("colaborador.id"))
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)  # se llena en __init__


class Subtarea(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_31, HU_34-37. Pasos verificables de una tarea (máximo 30 por tarea)."""

    __tablename__ = "subtarea"

    id = db.Column(BigId, primary_key=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=False, index=True)
    titulo = db.Column(db.String(150), nullable=False)
    completada = db.Column(db.Boolean, nullable=False, default=False)
    completada_por = db.Column(BigId, db.ForeignKey("colaborador.id"))
    completada_en = db.Column(db.DateTime(timezone=True))
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tarea_id": self.tarea_id,
            "titulo": self.titulo,
            "completada": self.completada,
            "completada_por": self.completada_por,
            "completada_en": self.completada_en.isoformat() if self.completada_en else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Comentario(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_31, HU_38-40. Comentarios de la tarea (texto máximo 1,000 caracteres)."""

    __tablename__ = "comentario"

    id = db.Column(BigId, primary_key=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=False, index=True)
    autor_id = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    texto = db.Column(db.String(1000), nullable=False)
    editado = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tarea_id": self.tarea_id,
            "autor_id": self.autor_id,
            "texto": self.texto,
            "editado": self.editado,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }