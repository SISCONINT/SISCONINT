"""Minutas y acuerdos: documentos cargados por reunión, ligados a un cliente o tarea."""
from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin

TIPO_CLIENTE = "CLIENTE"
TIPO_PERSONAL = "PERSONAL"
TIPOS = (TIPO_CLIENTE, TIPO_PERSONAL)

# ck_minuta_mime: tipos permitidos por la base de datos.
MIMES_PERMITIDOS = (
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "image/jpeg",
    "image/png",
)

MAX_BYTES = 10 * 1024 * 1024  # ck_minuta_bytes: 1 byte - 10 MB


class Minuta(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = "minuta"

    id = db.Column(BigId, primary_key=True)
    tipo = db.Column(db.String(8), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    fecha_reunion = db.Column(db.Date, nullable=False, index=True)
    cliente_id = db.Column(BigId, db.ForeignKey("cliente.id"), nullable=True, index=True)
    tarea_id = db.Column(BigId, db.ForeignKey("tarea.id"), nullable=True)
    observaciones = db.Column(db.Text)
    cargada_por = db.Column(BigId, db.ForeignKey("colaborador.id"), nullable=False, index=True)
    archivo_nombre = db.Column(db.String(255), nullable=False)
    archivo_ruta = db.Column(db.String(500), nullable=False)
    archivo_mime = db.Column(db.String(100), nullable=False)
    archivo_bytes = db.Column(db.Integer, nullable=False)
    created_by = db.Column(BigId, db.ForeignKey("colaborador.id"))
    updated_by = db.Column(BigId, db.ForeignKey("colaborador.id"))

    cliente = db.relationship("Cliente")
    tarea = db.relationship("Tarea")
    cargador = db.relationship("Colaborador", foreign_keys=[cargada_por])

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo": self.tipo,
            "titulo": self.titulo,
            "fecha_reunion": self.fecha_reunion.isoformat() if self.fecha_reunion else None,
            "cliente_id": self.cliente_id,
            "cliente_nombre": self.cliente.nombre_completo if self.cliente else None,
            "tarea_id": self.tarea_id,
            "tarea_titulo": self.tarea.titulo if self.tarea else None,
            "observaciones": self.observaciones,
            "cargada_por": self.cargada_por,
            "cargador_nombre": self.cargador.nombre_completo if self.cargador else None,
            "archivo_nombre": self.archivo_nombre,
            "archivo_mime": self.archivo_mime,
            "archivo_bytes": self.archivo_bytes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
