from app.core import audit
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.obligation import Obligacion
from app.models.user import Colaborador
from app.repositories import obligation_repository

MSG_DUPLICADA = "Ya existe una obligación con esa categoría y periodicidad para el cliente"


def list_obligations(filtros: dict):
    return obligation_repository.search(
        cliente_id=filtros.get("cliente"),
        solo_activas=filtros.get("solo_activas", False),
        page=filtros["page"],
    )


def _validar_cliente(cliente_id: int) -> Cliente:
    cliente = db.session.get(Cliente, cliente_id)
    if cliente is None or cliente.deleted_at is not None:
        raise ValidationAppError(
            "El cliente no es válido", fields={"cliente_id": ["Cliente no encontrado"]}
        )
    return cliente


def _validar_categoria(categoria_id: int) -> CategoriaProyecto:
    categoria = db.session.get(CategoriaProyecto, categoria_id)
    if categoria is None or categoria.deleted_at is not None:
        raise ValidationAppError(
            "La categoría no es válida", fields={"categoria_id": ["Categoría no encontrada"]}
        )
    return categoria


def _validar_responsable(responsable_id: int) -> Colaborador:
    responsable = db.session.get(Colaborador, responsable_id)
    if responsable is None or not responsable.activo:
        raise ValidationAppError(
            "El responsable no es válido",
            fields={"responsable_id": ["Colaborador no encontrado o inactivo"]},
        )
    return responsable


def _validar_duplicada(data: dict, exclude_id: int | None = None) -> None:
    existente = obligation_repository.find_duplicada(
        cliente_id=data["cliente_id"],
        categoria_id=data["categoria_id"],
        periodicidad=data["periodicidad"],
        exclude_id=exclude_id,
    )
    if existente is not None:
        raise ConflictError(
            MSG_DUPLICADA,
            fields={"periodicidad": [MSG_DUPLICADA]},
        )


def _validar(data: dict, exclude_id: int | None = None) -> None:
    _validar_cliente(data["cliente_id"])
    _validar_categoria(data["categoria_id"])
    _validar_responsable(data["responsable_id"])
    _validar_duplicada(data, exclude_id)


def create_obligation(actor, data: dict) -> Obligacion:
    _validar(data)

    obligacion = Obligacion(
        cliente_id=data["cliente_id"],
        categoria_id=data["categoria_id"],
        responsable_id=data["responsable_id"],
        periodicidad=data["periodicidad"],
        dia_vencimiento=data["dia_vencimiento"],
        fecha_inicio=data["fecha_inicio"],
        prioridad=data["prioridad"],
        activa=True,
        created_by=actor.id,
        updated_by=actor.id,
    )
    db.session.add(obligacion)
    db.session.flush()
    audit.log(
        actor.id,
        "obligacion",
        obligacion.id,
        audit.CREAR,
        {"periodicidad": obligacion.periodicidad, "categoria_id": obligacion.categoria_id},
    )
    db.session.commit()
    return obligacion


def get_obligation(obligacion_id: int) -> Obligacion:
    obligacion = obligation_repository.get_by_id(obligacion_id)
    if obligacion is None:
        raise NotFoundError("Obligación no encontrada")
    return obligacion


def update_obligation(actor, obligacion_id: int, data: dict) -> Obligacion:
    obligacion = get_obligation(obligacion_id)
    _validar(data, exclude_id=obligacion.id)

    for field in (
        "cliente_id",
        "categoria_id",
        "responsable_id",
        "periodicidad",
        "dia_vencimiento",
        "fecha_inicio",
        "prioridad",
    ):
        setattr(obligacion, field, data.get(field, getattr(obligacion, field)))
    if data.get("activa") is not None:
        obligacion.activa = data["activa"]
    obligacion.updated_by = actor.id
    audit.log(
        actor.id,
        "obligacion",
        obligacion.id,
        audit.MODIFICAR,
        {"periodicidad": obligacion.periodicidad, "categoria_id": obligacion.categoria_id},
    )
    db.session.commit()
    return obligacion


def deactivate_obligation(actor, obligacion_id: int) -> Obligacion:
    obligacion = get_obligation(obligacion_id)
    obligacion.activa = False
    obligacion.updated_by = actor.id
    audit.log(actor.id, "obligacion", obligacion.id, audit.ESTATUS, {"activa": False})
    db.session.commit()
    return obligacion
