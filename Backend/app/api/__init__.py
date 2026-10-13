from flask import Blueprint

from app.api import auth, catalog, clients, tasks, users

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")
api_bp.register_blueprint(auth.bp)
api_bp.register_blueprint(users.bp)
api_bp.register_blueprint(clients.bp)
api_bp.register_blueprint(catalog.bp)
api_bp.register_blueprint(tasks.bp)