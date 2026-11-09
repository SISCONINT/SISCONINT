from app.core import audit
from app.core.errors import ForbiddenError, NotFoundError
from app.extensions import db
from app.models.minute import Minuta
from app.repositories import minute_repository
from app.core.permissions import ROL_ADMINISTRADOR, ROL_COORDINADOR, ROL_DUENO


def list_minutes(filtros: dict):
    return minute_repository.search(
        cliente_id=filtros.get("cliente"), tarea_id=filtros.get("tarea"), page=filtros["page"]
    )


def create_minute(actor, data: dict) -> Minuta:
    minuta = Minuta(
        cliente_id=data.get("cliente_id"),
        tarea_id=data.get("tarea_id"),
        titulo=data["titulo"],
        fecha=data["fecha"],
        participantes=data.get("participantes"),
        acuerdos=data["acuerdos"],
        creador_id=actor.id,
        updated_by=actor.id,
    )
    db.session.add(minuta)
    db.session.flush()
    audit.log(actor.id, "minuta", minuta.id, audit.CREAR, {"titulo": minuta.titulo})
    db.session.commit()
    return minuta


def get_minute(minuta_id: int) -> Minuta:
    minuta = minute_repository.get_by_id(minuta_id)
    if minuta is None:
        raise NotFoundError("Minuta no encontrada")
    return minuta


def _assert_can_edit(actor, minuta: Minuta) -> None:
    if actor.rol in (ROL_DUENO, ROL_ADMINISTRADOR, ROL_COORDINADOR):
        return
    if minuta.creador_id == actor.id:
        return
    raise ForbiddenError()


def update_minute(actor, minuta_id: int, data: dict) -> Minuta:
    minuta = get_minute(minuta_id)
    _assert_can_edit(actor, minuta)
    minuta.cliente_id = data.get("cliente_id")
    minuta.tarea_id = data.get("tarea_id")
    minuta.titulo = data["titulo"]
    minuta.fecha = data["fecha"]
    minuta.participantes = data.get("participantes")
    minuta.acuerdos = data["acuerdos"]
    minuta.updated_by = actor.id
    audit.log(actor.id, "minuta", minuta.id, audit.MODIFICAR, {"titulo": minuta.titulo})
    db.session.commit()
    return minuta


def delete_minute(actor, minuta_id: int) -> None:
    from app.core.datetime_utils import utcnow

    minuta = get_minute(minuta_id)
    minuta.deleted_at = utcnow()
    audit.log(actor.id, "minuta", minuta.id, audit.ELIMINAR, {"titulo": minuta.titulo})
    db.session.commit()
