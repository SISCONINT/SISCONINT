"""HU_11-16. Lógica de negocio de clientes."""
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.pagination import PER_PAGE
from app.core.permissions import ROL_CONTADOR
from app.extensions import db
from app.models.client import (
    CONTACTO_PAGOS,
    CONTACTO_PRINCIPAL,
    ESTATUS_BAJA,
    Cliente,
    ClienteRegimen,
    ContactoCliente,
)
from app.repositories import client_repository

_EDITABLE_FIELDS = (
    "nombre_completo",
    "rfc",
    "tipo_persona",
    "razon_social",
    "forma_pago",
    "contador_asignado_id",
    "giro",
    "telefono",
    "correo",
    "codigo_postal",
    "calle",
    "no_exterior",
    "no_interior",
    "colonia",
    "ciudad",
    "estado",
    "tiene_trabajadores",
    "tipo_nomina",
)


# ---------------------------------------------------------------------------
# HU_11
# ---------------------------------------------------------------------------
def create_client(actor, data: dict) -> Cliente:
    """HU_11. Registra un cliente nuevo con sus regímenes y contactos."""
    existente = client_repository.find_by_rfc(data["rfc"])
    if existente is not None:
        raise ConflictError(
            f"El RFC ya está registrado y pertenece al cliente: {existente.nombre_completo}",
            fields={"rfc": ["El RFC ya está registrado"]},
        )

    contador = client_repository.get_contador_activo(data["contador_asignado_id"])
    if contador is None:
        raise ValidationAppError(
            "El contador asignado no es válido",
            fields={"contador_asignado_id": ["Debe ser un Contador Activo"]},
        )

    solicitados = set(data["regimenes"])
    validos = client_repository.regimenes_existen(list(solicitados))
    invalidos = solicitados - validos
    if invalidos:
        raise ValidationAppError(
            "Hay regímenes fiscales inválidos",
            fields={"regimenes": [f"Claves no válidas: {sorted(invalidos)}"]},
        )

    cliente = Cliente(
        nombre_completo=data["nombre_completo"],
        rfc=data["rfc"],
        tipo_persona=data["tipo_persona"],
        razon_social=data.get("razon_social"),
        forma_pago=data["forma_pago"],
        contador_asignado_id=data["contador_asignado_id"],
        giro=data["giro"],
        telefono=data["telefono"],
        correo=data["correo"],
        codigo_postal=data["codigo_postal"],
        calle=data["calle"],
        no_exterior=data["no_exterior"],
        no_interior=data.get("no_interior"),
        colonia=data["colonia"],
        ciudad=data["ciudad"],
        estado=data["estado"],
        tiene_trabajadores=data["tiene_trabajadores"],
        tipo_nomina=data.get("tipo_nomina"),
        estatus="ACTIVO",
        created_by=actor.id,
        updated_by=actor.id,
    )
    try:
        client_repository.add(cliente)

        for clave in solicitados:
            db.session.add(ClienteRegimen(cliente_id=cliente.id, regimen_clave=clave))

        principal = data["contacto_principal"]
        db.session.add(
            ContactoCliente(
                cliente_id=cliente.id,
                tipo=CONTACTO_PRINCIPAL,
                nombre_completo=principal["nombre_completo"],
                telefono=principal["telefono"],
                correo=principal["correo"],
                cargo=principal["cargo"],
                created_by=actor.id,
                updated_by=actor.id,
            )
        )

        pagos = data.get("contacto_pagos")
        if pagos:
            db.session.add(
                ContactoCliente(
                    cliente_id=cliente.id,
                    tipo=CONTACTO_PAGOS,
                    nombre_completo=pagos["nombre_completo"],
                    telefono=pagos["telefono"],
                    correo=pagos["correo"],
                    cargo=pagos["cargo"],
                    created_by=actor.id,
                    updated_by=actor.id,
                )
            )

        audit.log(
            actor.id,
            entidad="cliente",
            entidad_id=cliente.id,
            accion=audit.CREAR,
            detalle={"rfc": cliente.rfc, "nombre": cliente.nombre_completo},
        )
        _notificar_alta_cliente(cliente, actor)

        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("No se pudo registrar el cliente") from exc

    return cliente


# ---------------------------------------------------------------------------
# HU_13: consultar expediente
# ---------------------------------------------------------------------------
def get_client(actor, cliente_id: int) -> Cliente:
    """HU_13. Expediente completo. El Contador solo accede a los suyos (RG-12)."""
    cliente = client_repository.get_by_id(cliente_id)
    if cliente is None:
        raise NotFoundError("Cliente no encontrado")

    if actor.rol == ROL_CONTADOR and not client_repository.tiene_acceso(actor.id, cliente_id):
        raise ForbiddenError()

    return cliente


# ---------------------------------------------------------------------------
# HU_14: editar cliente
# ---------------------------------------------------------------------------
def update_client(actor, cliente_id: int, data: dict) -> Cliente:
    """HU_14. Reemplaza los datos generales, domicilio, régimen y contactos del cliente."""
    cliente = client_repository.get_by_id(cliente_id)
    if cliente is None:
        raise NotFoundError("Cliente no encontrado")

    existente = client_repository.find_by_rfc(data["rfc"])
    if existente is not None and existente.id != cliente.id:
        raise ConflictError(
            f"El RFC ya está registrado y pertenece al cliente: {existente.nombre_completo}",
            fields={"rfc": ["El RFC ya está registrado"]},
        )

    contador = client_repository.get_contador_activo(data["contador_asignado_id"])
    if contador is None:
        raise ValidationAppError(
            "El contador asignado no es válido",
            fields={"contador_asignado_id": ["Debe ser un Contador Activo"]},
        )

    solicitados = set(data["regimenes"])
    validos = client_repository.regimenes_existen(list(solicitados))
    invalidos = solicitados - validos
    if invalidos:
        raise ValidationAppError(
            "Hay regímenes fiscales inválidos",
            fields={"regimenes": [f"Claves no válidas: {sorted(invalidos)}"]},
        )

    before = {field: getattr(cliente, field) for field in _EDITABLE_FIELDS}

    for field in _EDITABLE_FIELDS:
        setattr(cliente, field, data.get(field))
    cliente.updated_by = actor.id

    changed = {
        field: {"antes": before[field], "despues": getattr(cliente, field)}
        for field in _EDITABLE_FIELDS
        if before[field] != getattr(cliente, field)
    }

    # Regímenes: se reemplazan por completo.
    for regimen in list(cliente.regimenes):
        db.session.delete(regimen)
    db.session.flush()
    for clave in solicitados:
        db.session.add(ClienteRegimen(cliente_id=cliente.id, regimen_clave=clave))

    # Contactos: se actualiza el principal existente (o se crea) y lo mismo para pagos.
    _upsert_contacto(cliente, CONTACTO_PRINCIPAL, data["contacto_principal"], actor)
    pagos = data.get("contacto_pagos")
    if pagos:
        _upsert_contacto(cliente, CONTACTO_PAGOS, pagos, actor)
    else:
        _remove_contacto(cliente, CONTACTO_PAGOS)

    try:
        if changed:
            audit.log(actor.id, "cliente", cliente.id, audit.MODIFICAR, changed)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise ConflictError("No se pudo actualizar el cliente") from exc

    return cliente


def _upsert_contacto(cliente: Cliente, tipo: str, data: dict, actor) -> None:
    existente = next((c for c in cliente.contactos if c.tipo == tipo and c.deleted_at is None), None)
    if existente is None:
        db.session.add(
            ContactoCliente(
                cliente_id=cliente.id,
                tipo=tipo,
                nombre_completo=data["nombre_completo"],
                telefono=data["telefono"],
                correo=data["correo"],
                cargo=data["cargo"],
                created_by=actor.id,
                updated_by=actor.id,
            )
        )
        return

    existente.nombre_completo = data["nombre_completo"]
    existente.telefono = data["telefono"]
    existente.correo = data["correo"]
    existente.cargo = data["cargo"]
    existente.updated_by = actor.id


def _remove_contacto(cliente: Cliente, tipo: str) -> None:
    existente = next((c for c in cliente.contactos if c.tipo == tipo and c.deleted_at is None), None)
    if existente is not None:
        db.session.delete(existente)


# ---------------------------------------------------------------------------
# HU_15: dar de baja
# ---------------------------------------------------------------------------
def deactivate_client(actor, cliente_id: int, motivo: str) -> Cliente:
    """HU_15. Pasa el cliente a Baja (RG-03: no se elimina). Las tareas y el historial no se tocan."""
    cliente = client_repository.get_by_id(cliente_id)
    if cliente is None:
        raise NotFoundError("Cliente no encontrado")

    before = cliente.estatus
    cliente.estatus = ESTATUS_BAJA
    cliente.motivo_baja = motivo
    cliente.updated_by = actor.id

    audit.log(
        actor.id, "cliente", cliente.id, audit.ESTATUS,
        {"estatus": {"antes": before, "despues": ESTATUS_BAJA}, "motivo": motivo},
    )
    db.session.commit()
    return cliente


# ---------------------------------------------------------------------------
# HU_12
# ---------------------------------------------------------------------------
def list_client_options(actor, filtros: dict | None = None) -> list[dict]:
    """Clientes para selectores, respetando el alcance del Contador (RG-12)."""
    scope_contador_id = actor.id if actor.rol == ROL_CONTADOR else None
    return client_repository.list_options(
        scope_contador_id=scope_contador_id,
        incluir_baja=bool((filtros or {}).get("incluir_baja")),
    )


def list_clients(actor, filtros: dict):
    """HU_12. Listado paginado de clientes con alcance por rol (RG-12).

    El Contador solo ve los asignados a él o con permiso de atención vigente.
    El filtro `contador` (query param) se ignora para el Contador.
    """
    scope_contador_id = actor.id if actor.rol == ROL_CONTADOR else None

    # El Contador no puede filtrar por otro contador (no lo ve).
    contador_id = None if scope_contador_id is not None else filtros.get("contador")

    return client_repository.search(
        q=filtros.get("q"),
        estatus=filtros["estatus"],
        contador_id=contador_id,
        tipo_persona=filtros.get("tipo_persona"),
        scope_contador_id=scope_contador_id,
        page=filtros["page"],
        per_page=PER_PAGE,
    )


# ---------------------------------------------------------------------------
# HU_69: notificación in-app al alta de cliente
# ---------------------------------------------------------------------------
def _notificar_alta_cliente(cliente: Cliente, actor) -> None:
    from sqlalchemy import select

    from app.models.notification import Notificacion
    from app.models.user import (
        ESTATUS_ACTIVO,
        ROL_ADMINISTRADOR,
        ROL_COORDINADOR,
        ROL_DUENO,
        Colaborador,
    )

    destinatarios = db.session.execute(
        select(Colaborador).where(
            Colaborador.rol.in_((ROL_DUENO, ROL_ADMINISTRADOR, ROL_COORDINADOR)),
            Colaborador.estatus == ESTATUS_ACTIVO,
            Colaborador.deleted_at.is_(None),
            Colaborador.id != actor.id,
        )
    ).scalars().all()

    contador = db.session.get(Colaborador, cliente.contador_asignado_id)
    contador_nombre = contador.nombre_completo if contador else "sin contador asignado"

    for u in destinatarios:
        db.session.add(
            Notificacion(
                usuario_id=u.id,
                tipo="CLIENTE_NUEVO",
                titulo="Nuevo cliente registrado",
                mensaje=(
                    f"{cliente.nombre_completo} — contador asignado: {contador_nombre} "
                    f"(registrado por {actor.nombre_completo})"
                ),
                entidad_tipo="CLIENTE",
                entidad_id=cliente.id,
            )
        )
