"""Plantillas de notificación: asunto y cuerpo editables con respaldo original."""
from sqlalchemy import select

from app.core import audit
from app.core.errors import ConflictError, NotFoundError
from app.extensions import db
from app.models.email_template import PlantillaNotificacion


def list_templates() -> list[PlantillaNotificacion]:
    stmt = (
        select(PlantillaNotificacion)
        .where(PlantillaNotificacion.deleted_at.is_(None))
        .order_by(PlantillaNotificacion.clave)
    )
    return list(db.session.execute(stmt).scalars())


def get_template(plantilla_id: int) -> PlantillaNotificacion:
    plantilla = db.session.get(PlantillaNotificacion, plantilla_id)
    if plantilla is None or plantilla.deleted_at is not None:
        raise NotFoundError("Plantilla no encontrada")
    return plantilla


def _get_by_clave(clave: str) -> PlantillaNotificacion | None:
    stmt = select(PlantillaNotificacion).where(
        PlantillaNotificacion.clave == clave,
        PlantillaNotificacion.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def create_template(actor, data: dict) -> PlantillaNotificacion:
    if _get_by_clave(data["clave"]) is not None:
        raise ConflictError(
            "Ya existe una plantilla con esa clave", fields={"clave": ["Clave ya utilizada"]}
        )

    plantilla = PlantillaNotificacion(
        clave=data["clave"],
        asunto=data["asunto"],
        cuerpo=data["cuerpo"],
        asunto_original=data["asunto"],
        cuerpo_original=data["cuerpo"],
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.session.add(plantilla)
    db.session.flush()
    audit.log(
        actor.id, "plantilla_notificacion", plantilla.id, audit.CREAR, {"clave": plantilla.clave}
    )
    db.session.commit()
    return plantilla


def update_template(actor, plantilla_id: int, data: dict) -> PlantillaNotificacion:
    plantilla = get_template(plantilla_id)
    plantilla.asunto = data["asunto"]
    plantilla.cuerpo = data["cuerpo"]
    plantilla.updated_by = actor.id
    audit.log(
        actor.id, "plantilla_notificacion", plantilla.id, audit.MODIFICAR, {"clave": plantilla.clave}
    )
    db.session.commit()
    return plantilla
