"""Reportes ejecutivos: reutiliza las agregaciones del dashboard."""
from app.core.datetime_utils import utcnow
from app.repositories import report_repository
from app.services import dashboard_service


def get_executive_report(actor, filtros: dict) -> dict:
    """Resumen ejecutivo del periodo con los filtros de cliente y colaborador.

    La base es el dashboard general (mismas tarjetas y agrupaciones) más el
    número de tareas completadas dentro del periodo y la marca de generación.
    """
    data = dashboard_service.get_dashboard(actor, filtros)
    periodo = data["periodo"]

    data["tareas_completadas"] = report_repository.count_completed_tasks(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=filtros.get("cliente"),
        colaborador_id=filtros.get("colaborador"),
    )
    data["generado_en"] = utcnow()
    return data
