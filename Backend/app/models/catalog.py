from app.extensions import db
from app.models.base import BigId, SoftDeleteMixin, TimestampMixin


class CategoriaProyecto(TimestampMixin, SoftDeleteMixin, db.Model):
    """HU_25-28. Árbol de 2 niveles: categoría (padre_id NULL) y subcategoría.

    Espejo de la tabla categoria_proyecto del esquema oficial.
    "Proyecto" = categoría del catálogo (Anexo A de las HU).
    """

    __tablename__ = "categoria_proyecto"

    id = db.Column(BigId, primary_key=True)
    padre_id = db.Column(BigId, db.ForeignKey("categoria_proyecto.id"), nullable=True, index=True)
    nombre = db.Column(db.String(80), nullable=False)
    activa = db.Column(db.Boolean, nullable=False, default=True)
    orden = db.Column(db.Integer, nullable=False, default=0)

    subcategorias = db.relationship(
        "CategoriaProyecto",
        backref=db.backref("padre", remote_side=[id]),
        order_by="CategoriaProyecto.orden, CategoriaProyecto.nombre",
    )

    @property
    def es_categoria(self) -> bool:
        return self.padre_id is None

    def to_dict(self, incluir_subcategorias: bool = False) -> dict:
        data = {
            "id": self.id,
            "nombre": self.nombre,
            "activa": self.activa,
            "orden": self.orden,
        }
        if incluir_subcategorias:
            data["subcategorias"] = [
                sub.to_dict() for sub in self.subcategorias if sub.deleted_at is None
            ]
        return data