"""HU_85: dashboard personal del Contador."""
import pytest

from tests.dashboard_helpers import crear_escenario
from tests.time_helpers import crear_registro

URL = "/api/v1/dashboard/me"


def _data(res) -> dict:
    return res.get_json()["data"]


@pytest.fixture()
def escenario(make_user):
    return crear_escenario(make_user)


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("rol", ["dueno", "admin", "coordinador"])
def test_only_the_accountant_opens_the_personal_dashboard(
    client, auth_headers, escenario, rol
):
    res = client.get(URL, headers=auth_headers(getattr(escenario, rol)))

    assert res.status_code == 403


def test_accountant_opens_his_personal_dashboard(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    assert _data(res)["tarjetas"]


# ---------------------------------------------------------------------------
# Solo información propia
# ---------------------------------------------------------------------------
def test_shows_only_his_own_hours(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    data = _data(res)
    assert data["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert data["tarjetas"]["horas_totales"]["minutos"] == 120
    assert data["tiempo_por_cliente"] == [
        {
            "cliente_id": escenario.cliente1.id,
            "nombre": "Cliente Uno",
            "minutos": 120,
            "horas": 2.0,
        }
    ]


def test_does_not_include_other_employees_or_costs(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    data = _data(res)
    assert "costo_estimado" not in data["tarjetas"]
    assert "tiempo_por_empleado" not in data
    assert "Beto Contador" not in str(data)
    assert "Cliente Dos" not in str(data)


def test_shows_only_his_own_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    estados = _data(res)["estado_tareas"]
    assert estados == {
        "POR_HACER": 1,
        "EN_PROGRESO": 1,
        "EN_REVISION": 0,
        "COMPLETADO": 0,
        "vencidas": 1,
        "total": 2,
    }
    assert _data(res)["tarjetas"]["tareas_activas"] == 2
    assert _data(res)["tarjetas"]["tareas_vencidas"] == 1


def test_shows_only_his_own_categories(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    filas = _data(res)["distribucion_por_categoria"]
    assert [fila["nombre"] for fila in filas] == ["Fiscal"]
    assert filas[0]["horas"] == 2.0
    assert filas[0]["porcentaje"] == 100.0


# ---------------------------------------------------------------------------
# Periodo
# ---------------------------------------------------------------------------
def test_default_period_is_the_current_month(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert _data(res)["periodo"]["tipo"] == "MES_ACTUAL"


def test_period_filter_limits_his_hours(client, auth_headers, escenario):
    crear_registro(
        escenario.tarea1,
        escenario.contador1,
        fecha=escenario.ayer,
        minutos=60,
        descripcion="Trabajo de ayer",
    )

    res = client.get(
        URL, query_string={"periodo": "hoy"}, headers=auth_headers(escenario.contador1)
    )

    assert _data(res)["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert _data(res)["periodo_anterior"]["desde"] == escenario.ayer.isoformat()


def test_employee_filter_is_ignored_for_the_accountant(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={"colaborador": escenario.contador2.id},
        headers=auth_headers(escenario.contador1),
    )

    data = _data(res)
    assert data["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert data["estado_tareas"]["total"] == 2


def test_no_data_returns_the_expected_message(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador3))

    data = _data(res)
    assert data["sin_informacion"] is True
    assert data["mensaje"] == "Sin información para los filtros seleccionados"
    assert data["tarjetas"]["horas_totales"]["horas"] == 0.0
    assert data["tiempo_por_cliente"] == []
    assert data["distribucion_por_categoria"] == []


def test_with_data_the_message_is_empty(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    data = _data(res)
    assert data["sin_informacion"] is False
    assert data["mensaje"] is None
