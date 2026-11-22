"""Reportes ejecutivos. Prefijo /api/v1/reports."""
from flask import Blueprint, g, request

from app.core.permissions import require_permission
from app.core.responses import ok
from app.schemas.dashboard_schema import DashboardQuerySchema
from app.schemas.report_schema import ReporteEjecutivoSchema
from app.services import report_service

bp = Blueprint("reports", __name__, url_prefix="/reports")


@bp.get("/summary")
@require_permission("report:view")
def get_summary():
    """Reporte ejecutivo del periodo (Dueño, Administrador y Coordinador).

    Acepta los mismos filtros que el dashboard: periodo, rango personalizado,
    cliente y colaborador. Incluye tarjetas, agrupaciones y tareas completadas.
    """
    filtros = DashboardQuerySchema().load(request.args.to_dict())
    data = report_service.get_executive_report(g.current_user, filtros)
    return ok(ReporteEjecutivoSchema().dump(data))
