from sqlalchemy import select

from app.core import audit
from app.core.errors import ConflictError, NotFoundError
from app.extensions import db
from app.models.email_template import PlantillaCorreo


def list_templates() -> list[PlantillaCorreo]:
    stmt = select(PlantillaCorreo).where(PlantillaCorreo.deleted_at.is_(None)).order_by(PlantillaCorreo.nombre)
    return list(db.session.execute(stmt).scalars())


def get_template(plantilla_id: int) -> PlantillaCorreo:
    plantilla = db.session.get(PlantillaCorreo, plantilla_id)
    if plantilla is None or plantilla.deleted_at is not None:
        raise NotFoundError("Plantilla no encontrada")
    return plantilla


def create_template(actor, data: dict) -> PlantillaCorreo:
    existente = db.session.execute(
        select(PlantillaCorreo).where(PlantillaCorreo.clave == data["clave"], PlantillaCorreo.deleted_at.is_(None))
    ).scalar_one_or_none()
    if existente is not None:
        raise ConflictError(
            "Ya existe una plantilla con esa clave", fields={"clave": ["Clave ya utilizada"]}
        )

    plantilla = PlantillaCorreo(
        clave=data["clave"], nombre=data["nombre"], asunto=data["asunto"],
        cuerpo=data["cuerpo"], activa=data.get("activa", True), updated_by=actor.id,
    )
    db.session.add(plantilla)
    db.session.flush()
    audit.log(actor.id, "plantilla_correo", plantilla.id, audit.CREAR, {"clave": plantilla.clave})
    db.session.commit()
    return plantilla


def update_template(actor, plantilla_id: int, data: dict) -> PlantillaCorreo:
    plantilla = get_template(plantilla_id)
    plantilla.nombre = data["nombre"]
    plantilla.asunto = data["asunto"]
    plantilla.cuerpo = data["cuerpo"]
    plantilla.activa = data.get("activa", True)
    plantilla.updated_by = actor.id
    audit.log(actor.id, "plantilla_correo", plantilla.id, audit.MODIFICAR, {"clave": plantilla.clave})
    db.session.commit()
    return plantilla
