"""HU_11-12. Lógica de negocio de clientes."""
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.core.pagination import PER_PAGE
from app.core.permissions import ROL_CONTADOR
from app.extensions import db
from app.models.client import (
    CONTACTO_PAGOS,
    CONTACTO_PRINCIPAL,
    Cliente,
    ClienteRegimen,
    ContactoCliente,
)
from app.repositories import client_repository


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
# HU_12
# ---------------------------------------------------------------------------
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

    for u in destinatarios:
        db.session.add(
            Notificacion(
                usuario_id=u.id,
                tipo="CLIENTE_NUEVO",
                titulo="Nuevo cliente registrado",
                mensaje=f"{cliente.nombre_completo} fue registrado por {actor.nombre_completo}",
                entidad_tipo="CLIENTE",
                entidad_id=cliente.id,
            )
        )