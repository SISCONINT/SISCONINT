"""HU_11. Lógica de negocio de clientes (registro)."""
from sqlalchemy.exc import IntegrityError

from app.core import audit
from app.core.errors import ConflictError, NotFoundError, ValidationAppError
from app.extensions import db
from app.models.client import (
    CONTACTO_PAGOS,
    CONTACTO_PRINCIPAL,
    Cliente,
    ClienteRegimen,
    ContactoCliente,
)
from app.repositories import client_repository


def create_client(actor, data: dict) -> Cliente:
    """HU_11. Registra un cliente nuevo con sus regímenes y contactos.

    Reglas:
      - RFC único entre clientes no eliminados; el mensaje indica a qué cliente pertenece.
      - Contador asignado debe ser Contador Activo.
      - Todos los regímenes deben existir y estar activos en el catálogo SAT.
    """
    # 1) RFC único
    existente = client_repository.find_by_rfc(data["rfc"])
    if existente is not None:
        raise ConflictError(
            f"El RFC ya está registrado y pertenece al cliente: {existente.nombre_completo}",
            fields={"rfc": ["El RFC ya está registrado"]},
        )

    # 2) Contador Activo con rol CONTADOR
    contador = client_repository.get_contador_activo(data["contador_asignado_id"])
    if contador is None:
        raise ValidationAppError(
            "El contador asignado no es válido",
            fields={"contador_asignado_id": ["Debe ser un Contador Activo"]},
        )

    # 3) Regímenes SAT existentes y activos
    solicitados = set(data["regimenes"])
    validos = client_repository.regimenes_existen(list(solicitados))
    invalidos = solicitados - validos
    if invalidos:
        raise ValidationAppError(
            "Hay regímenes fiscales inválidos",
            fields={"regimenes": [f"Claves no válidas: {sorted(invalidos)}"]},
        )

    # 4) Alta del cliente
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

        # Regímenes
        for clave in solicitados:
            db.session.add(ClienteRegimen(cliente_id=cliente.id, regimen_clave=clave))

        # Contacto principal (obligatorio)
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

        # Contacto de pagos (opcional; el schema ya garantizó "todo o nada")
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

        # Auditoría (RG-13) + Notificación in-app (HU_69, sin correo)
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


def _notificar_alta_cliente(cliente: Cliente, actor) -> None:
    """HU_69: in-app a Dueños, Admins y Coordinadores Activos, excepto al creador."""
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