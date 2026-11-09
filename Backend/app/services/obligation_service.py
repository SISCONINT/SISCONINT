from app.core import audit
from app.core.errors import NotFoundError, ValidationAppError
from app.extensions import db
from app.models.client import Cliente
from app.models.obligation import Obligacion
from app.repositories import obligation_repository


def list_obligations(filtros: dict):
    return obligation_repository.search(
        cliente_id=filtros.get("cliente"),
        solo_activas=filtros.get("solo_activas", False),
        page=filtros["page"],
    )


def create_obligation(actor, data: dict) -> Obligacion:
    cliente = db.session.get(Cliente, data["cliente_id"])
    if cliente is None or cliente.deleted_at is not None:
        raise ValidationAppError(
            "El cliente no es válido", fields={"cliente_id": ["Cliente no encontrado"]}
        )

    obligacion = Obligacion(
        cliente_id=data["cliente_id"],
        categoria_id=data.get("categoria_id"),
        nombre=data["nombre"],
        periodicidad=data["periodicidad"],
        dia_limite=data["dia_limite"],
        notas=data.get("notas"),
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.session.add(obligacion)
    db.session.flush()
    audit.log(actor.id, "obligacion", obligacion.id, audit.CREAR, {"nombre": obligacion.nombre})
    db.session.commit()
    return obligacion


def get_obligation(obligacion_id: int) -> Obligacion:
    obligacion = obligation_repository.get_by_id(obligacion_id)
    if obligacion is None:
        raise NotFoundError("Obligación no encontrada")
    return obligacion


def update_obligation(actor, obligacion_id: int, data: dict) -> Obligacion:
    obligacion = get_obligation(obligacion_id)
    for field in ("categoria_id", "nombre", "periodicidad", "dia_limite", "notas", "activa"):
        setattr(obligacion, field, data.get(field, getattr(obligacion, field)))
    obligacion.updated_by = actor.id
    audit.log(actor.id, "obligacion", obligacion.id, audit.MODIFICAR, {"nombre": obligacion.nombre})
    db.session.commit()
    return obligacion


def deactivate_obligation(actor, obligacion_id: int) -> Obligacion:
    obligacion = get_obligation(obligacion_id)
    obligacion.activa = False
    obligacion.updated_by = actor.id
    audit.log(actor.id, "obligacion", obligacion.id, audit.ESTATUS, {"activa": False})
    db.session.commit()
    return obligacion
