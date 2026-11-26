"""Endpoints de salud que consulta Better Stack (monitoreo de disponibilidad)."""
from unittest.mock import patch

from sqlalchemy.exc import OperationalError

LIVENESS = "/health"
READINESS = "/api/v1/health"


def test_liveness_no_requiere_sesion(client):
    res = client.get(LIVENESS)
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_readiness_verifica_base_de_datos(client):
    res = client.get(READINESS)
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "database": "ok"}


def test_readiness_devuelve_503_si_la_base_de_datos_falla(client):
    error = OperationalError("SELECT 1", {}, Exception("conexión rechazada"))
    with patch("app.extensions.db.session.execute", side_effect=error):
        res = client.get(READINESS)
    assert res.status_code == 503
    assert res.get_json() == {"status": "error", "database": "down"}
