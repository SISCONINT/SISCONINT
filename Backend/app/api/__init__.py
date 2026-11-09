from flask import Blueprint

from app.api import (
    auth,
    catalog,
    clients,
    dashboard,
    minutes,
    notifications,
    obligations,
    rates,
    tasks,
    templates,
    time_entries,
    users,
)

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api_bp.register_blueprint(auth.bp)
api_bp.register_blueprint(users.bp)
api_bp.register_blueprint(clients.bp)
api_bp.register_blueprint(notifications.bp)
api_bp.register_blueprint(catalog.bp)
api_bp.register_blueprint(tasks.bp)
api_bp.register_blueprint(time_entries.bp)
api_bp.register_blueprint(dashboard.bp)
api_bp.register_blueprint(rates.bp)
api_bp.register_blueprint(obligations.bp)
api_bp.register_blueprint(minutes.bp)
api_bp.register_blueprint(templates.bp)
