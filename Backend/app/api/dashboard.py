"""Módulo 12: Dashboard. Prefijo /api/v1/dashboard. HU_79-85."""
from flask import Blueprint, g, request

from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.dashboard_schema import (
    DashboardPersonalSchema,
    DashboardQuerySchema,
    DashboardSchema,
)
from app.services import dashboard_service

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@bp.get("")
@require_permission("dashboard:view")
def get_dashboard():
    """HU_79-84: tarjetas, gráficas y estado de tareas del despacho.

    Dueño, Administrador y Coordinador. El periodo por defecto es el mes actual y
    acepta Hoy, Esta semana, Mes actual, Mes anterior o un rango personalizado de
    máximo 12 meses. Cliente y colaborador son opcionales y se aplican a todas las
    secciones a la vez. El Coordinador no recibe el costo estimado.
    """
    filtros = DashboardQuerySchema().load(request.args.to_dict())
    dashboard = dashboard_service.get_dashboard(g.current_user, filtros)
    return ok(DashboardSchema().dump(dashboard))


@bp.get("/me")
@require_permission("dashboard:personal")
def get_my_dashboard():
    """HU_85: dashboard personal del Contador.

    Solo muestra sus horas, sus clientes, sus categorías y sus tareas. No incluye
    costos ni datos de otros colaboradores. Permite filtrar por periodo.
    """
    filtros = DashboardQuerySchema().load(request.args.to_dict())
    dashboard = dashboard_service.get_personal_dashboard(g.current_user, filtros)
    return ok(DashboardPersonalSchema().dump(dashboard))
