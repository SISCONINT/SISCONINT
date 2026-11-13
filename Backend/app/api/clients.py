"""Módulo 3: Clientes. Prefijo /api/v1/clients. HU_11-16."""
from flask import Blueprint, g, request

from app.core.errors import ValidationAppError
from app.core.pagination import pagination_meta
from app.core.permissions import require_permission
from app.core.responses import ok
from app.repositories import client_repository
from app.schemas.cliente_list_schema import ClienteListItemSchema, ClienteListQuerySchema
from app.schemas.cliente_schema import (
    ClienteCreateSchema,
    ClienteDeactivateSchema,
    ClienteUpdateSchema,
)
from app.services import client_service

bp = Blueprint("clients", __name__, url_prefix="/clients")


@bp.get("")
@require_permission("client:list")
def list_clients():
    """HU_12: Consultar la lista de clientes (Dueño, Admin, Coordinador y Contador)."""
    filtros = ClienteListQuerySchema().load(request.args.to_dict())  # errores -> 422
    page = client_service.list_clients(g.current_user, filtros)

    ids = [c.id for c in page.items]
    indicadores = client_repository.indicators_for(ids)

    items = []
    for cliente in page.items:
        ind = indicadores.get(cliente.id, {})
        items.append(
            {
                "id": cliente.id,
                "nombre_completo": cliente.nombre_completo,
                "razon_social": cliente.razon_social,
                "rfc": cliente.rfc,
                "tipo_persona": cliente.tipo_persona,
                "contacto_principal_correo": ind.get("contacto_principal_correo"),
                "tareas_activas": ind.get("tareas_activas", 0),
                "horas_registradas": ind.get("horas_registradas", 0.0),
                "estatus": cliente.estatus,
            }
        )

    return ok(
        ClienteListItemSchema(many=True).dump(items),
        meta=pagination_meta(page),
    )


@bp.post("")
@require_permission("client:create")
def create_client():
    """HU_11: Registrar cliente (Dueño o Administrador)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = ClienteCreateSchema().load(payload)  # errores -> 422
    cliente = client_service.create_client(g.current_user, data)
    return ok(cliente.to_dict(), status=201)


@bp.get("/options")
@require_permission("client:list")
def list_client_options():
    """Clientes para selectores (tareas, obligaciones y minutas).

    Por defecto excluye a los clientes en Baja. El Contador solo recibe los
    clientes asignados a él o con permiso de atención vigente.
    """
    incluir_baja = str(request.args.get("incluir_baja", "")).lower() in (
        "1",
        "true",
        "si",
        "sí",
        "yes",
    )
    return ok(
        client_service.list_client_options(
            g.current_user, {"incluir_baja": incluir_baja}
        )
    )


@bp.get("/<int:cliente_id>")
@require_permission("client:view")
def get_client(cliente_id: int):
    """HU_13: Consultar el expediente completo de un cliente."""
    cliente = client_service.get_client(g.current_user, cliente_id)
    return ok(cliente.to_dict())


@bp.put("/<int:cliente_id>")
@require_permission("client:edit")
def update_client(cliente_id: int):
    """HU_14: Editar los datos del cliente (Dueño o Administrador)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = ClienteUpdateSchema().load(payload)  # errores -> 422
    cliente = client_service.update_client(g.current_user, cliente_id, data)
    return ok(cliente.to_dict())


@bp.post("/<int:cliente_id>/deactivate")
@require_permission("client:deactivate")
def deactivate_client(cliente_id: int):
    """HU_15: Dar de baja al cliente (Dueño o Administrador)."""
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValidationAppError("El cuerpo de la petición debe ser un objeto JSON")

    data = ClienteDeactivateSchema().load(payload)  # errores -> 422
    cliente = client_service.deactivate_client(g.current_user, cliente_id, data["motivo"])
    return ok(cliente.to_dict())