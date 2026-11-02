"""HU_79 y HU_84: tarjetas de resumen y filtros del dashboard."""
from datetime import timedelta

import pytest

from app.core.datetime_utils import today_mx
from tests.dashboard_helpers import crear_escenario
from tests.time_helpers import crear_registro

URL = "/api/v1/dashboard"


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
def test_allowed_roles_can_open_the_dashboard(client, auth_headers, escenario, rol):
    res = client.get(URL, headers=auth_headers(getattr(escenario, rol)))

    assert res.status_code == 200
    assert res.get_json()["data"]["tarjetas"]


def test_accountant_cannot_open_the_general_dashboard(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert res.status_code == 403


# ---------------------------------------------------------------------------
# Periodo por defecto (HU_79, HU_84)
# ---------------------------------------------------------------------------
def test_default_period_is_the_current_month(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    periodo = _data(res)["periodo"]
    hoy = today_mx()
    assert periodo["tipo"] == "MES_ACTUAL"
    assert periodo["etiqueta"] == "Mes actual"
    assert periodo["desde"] == hoy.replace(day=1).isoformat()
    assert periodo["hasta"] == hoy.isoformat()


def test_empty_query_params_use_the_default_period(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"periodo": "", "cliente": "", "colaborador": ""},
        headers=auth_headers(escenario.dueno),
    )

    assert res.status_code == 200
    assert _data(res)["periodo"]["tipo"] == "MES_ACTUAL"


def test_this_week_goes_from_monday_to_today(client, auth_headers, escenario):
    res = client.get(
        URL, query_string={"periodo": "semana"}, headers=auth_headers(escenario.dueno)
    )

    periodo = _data(res)["periodo"]
    hoy = today_mx()
    assert periodo["tipo"] == "SEMANA"
    assert periodo["etiqueta"] == "Esta semana"
    assert periodo["desde"] == (hoy - timedelta(days=hoy.weekday())).isoformat()
    assert periodo["hasta"] == hoy.isoformat()


def test_previous_month_is_the_full_previous_calendar_month(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={"periodo": "mes_anterior"},
        headers=auth_headers(escenario.dueno),
    )

    periodo = _data(res)["periodo"]
    hoy = today_mx()
    hasta = hoy.replace(day=1) - timedelta(days=1)
    desde = hasta.replace(day=1)
    assert periodo["tipo"] == "MES_ANTERIOR"
    assert periodo["etiqueta"] == "Mes anterior"
    assert periodo["desde"] == desde.isoformat()
    assert periodo["hasta"] == hasta.isoformat()


def test_previous_month_period_includes_its_entries(client, auth_headers, escenario):
    hoy = today_mx()
    hasta = hoy.replace(day=1) - timedelta(days=1)
    desde = hasta.replace(day=1)
    crear_registro(
        escenario.tarea1,
        escenario.contador1,
        fecha=desde,
        minutos=30,
        descripcion="Trabajo del mes anterior",
    )

    res = client.get(
        URL,
        query_string={"periodo": "mes_anterior"},
        headers=auth_headers(escenario.dueno),
    )

    assert _data(res)["tarjetas"]["horas_totales"]["horas"] == 0.5


def test_period_aliases_are_normalized(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"periodo": "esta_semana"},
        headers=auth_headers(escenario.dueno),
    )

    assert res.status_code == 200
    assert _data(res)["periodo"]["tipo"] == "SEMANA"


# ---------------------------------------------------------------------------
# Tarjetas (HU_79)
# ---------------------------------------------------------------------------
def test_cards_show_hours_active_overdue_and_state_counts(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    data = _data(res)
    tarjetas = data["tarjetas"]
    assert tarjetas["horas_totales"]["horas"] == 3.0
    assert tarjetas["horas_totales"]["minutos"] == 180
    assert tarjetas["tareas_activas"] == 3
    assert tarjetas["tareas_vencidas"] == 1

    estados = data["estado_tareas"]
    assert estados["POR_HACER"] == 1
    assert estados["EN_PROGRESO"] == 1
    assert estados["EN_REVISION"] == 1
    assert estados["COMPLETADO"] == 2
    assert estados["vencidas"] == 1
    assert estados["total"] == 5


def test_hours_variation_is_compared_with_the_previous_period(
    client, auth_headers, escenario
):
    crear_registro(
        escenario.tarea1,
        escenario.contador1,
        fecha=escenario.ayer,
        minutos=60,
        descripcion="Trabajo de ayer",
    )

    res = client.get(
        URL, query_string={"periodo": "hoy"}, headers=auth_headers(escenario.dueno)
    )

    horas = _data(res)["tarjetas"]["horas_totales"]
    assert horas["horas"] == 3.0
    assert horas["horas_periodo_anterior"] == 1.0
    assert horas["variacion_porcentaje"] == 200.0
    assert _data(res)["periodo_anterior"] == {
        "desde": escenario.ayer.isoformat(),
        "hasta": escenario.ayer.isoformat(),
    }


def test_variation_is_null_when_there_are_no_previous_hours(
    client, auth_headers, escenario
):
    res = client.get(
        URL, query_string={"periodo": "hoy"}, headers=auth_headers(escenario.dueno)
    )

    horas = _data(res)["tarjetas"]["horas_totales"]
    assert horas["horas_periodo_anterior"] == 0.0
    assert horas["variacion_porcentaje"] is None


@pytest.mark.parametrize("rol", ["dueno", "admin"])
def test_owner_and_admin_see_the_estimated_cost(client, auth_headers, escenario, rol):
    res = client.get(URL, headers=auth_headers(getattr(escenario, rol)))

    costo = _data(res)["tarjetas"]["costo_estimado"]
    assert costo == {
        "disponible": False,
        "monto": None,
        "horas_sin_tarifa": 3.0,
        "mensaje": "Sin tarifas configuradas",
    }


def test_coordinator_does_not_receive_the_estimated_cost(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.coordinador))

    assert "costo_estimado" not in _data(res)["tarjetas"]


# ---------------------------------------------------------------------------
# Filtros (HU_84)
# ---------------------------------------------------------------------------
def test_filter_by_client_applies_to_cards_and_charts(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente1.id},
        headers=auth_headers(escenario.dueno),
    )

    data = _data(res)
    assert data["filtros"] == {
        "cliente_id": escenario.cliente1.id,
        "cliente_nombre": "Cliente Uno",
        "colaborador_id": None,
        "colaborador_nombre": None,
    }
    assert data["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert data["tarjetas"]["tareas_activas"] == 2
    assert data["tarjetas"]["tareas_vencidas"] == 1
    assert data["estado_tareas"]["total"] == 3
    assert [fila["cliente_id"] for fila in data["tiempo_por_cliente"]] == [
        escenario.cliente1.id
    ]
    assert {fila["colaborador_id"] for fila in data["tiempo_por_empleado"]} == {
        escenario.contador1.id
    }


def test_filter_by_employee_applies_to_cards_and_charts(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={"colaborador": escenario.contador1.id},
        headers=auth_headers(escenario.dueno),
    )

    data = _data(res)
    assert data["filtros"]["colaborador_id"] == escenario.contador1.id
    assert data["filtros"]["colaborador_nombre"] == "Ana Contadora"
    assert data["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert data["tarjetas"]["tareas_activas"] == 2
    assert data["estado_tareas"]["total"] == 2
    assert [fila["colaborador_id"] for fila in data["tiempo_por_empleado"]] == [
        escenario.contador1.id
    ]


def test_client_and_employee_filters_are_combined(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "cliente": escenario.cliente1.id,
            "colaborador": escenario.contador1.id,
        },
        headers=auth_headers(escenario.dueno),
    )

    data = _data(res)
    assert data["tarjetas"]["horas_totales"]["horas"] == 2.0
    assert data["estado_tareas"]["total"] == 2
    assert data["estado_tareas"]["vencidas"] == 1


def test_no_data_returns_the_expected_message(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente3.id},
        headers=auth_headers(escenario.dueno),
    )

    data = _data(res)
    assert data["sin_informacion"] is True
    assert data["mensaje"] == "Sin información para los filtros seleccionados"
    assert data["tarjetas"]["horas_totales"]["horas"] == 0.0
    assert data["tarjetas"]["tareas_activas"] == 0
    assert data["tarjetas"]["tareas_vencidas"] == 0
    assert data["tiempo_por_empleado"] == []
    assert data["tiempo_por_cliente"] == []
    assert data["distribucion_por_categoria"] == []


def test_with_data_the_message_is_empty(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    data = _data(res)
    assert data["sin_informacion"] is False
    assert data["mensaje"] is None


# ---------------------------------------------------------------------------
# Rango personalizado (HU_84)
# ---------------------------------------------------------------------------
def test_custom_range_filters_time_entries(client, auth_headers, escenario):
    crear_registro(
        escenario.tarea1,
        escenario.contador1,
        fecha=escenario.ayer,
        minutos=45,
        descripcion="Trabajo de ayer",
    )

    res = client.get(
        URL,
        query_string={
            "periodo": "personalizado",
            "fecha_desde": escenario.ayer.isoformat(),
            "fecha_hasta": escenario.ayer.isoformat(),
        },
        headers=auth_headers(escenario.dueno),
    )

    data = _data(res)
    assert data["periodo"]["tipo"] == "PERSONALIZADO"
    assert data["tarjetas"]["horas_totales"]["horas"] == 0.8
    assert data["tarjetas"]["horas_totales"]["minutos"] == 45
    assert data["tiempo_por_cliente"][0]["cliente_id"] == escenario.cliente1.id


def test_dates_without_period_are_treated_as_custom_range(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={
            "fecha_desde": escenario.hoy.isoformat(),
            "fecha_hasta": escenario.hoy.isoformat(),
        },
        headers=auth_headers(escenario.dueno),
    )

    assert res.status_code == 200
    assert _data(res)["periodo"]["tipo"] == "PERSONALIZADO"


@pytest.mark.parametrize(
    ("query_string", "campo"),
    [
        ({"periodo": "personalizado"}, "fecha_desde"),
        (
            {
                "periodo": "personalizado",
                "fecha_desde": "2026-02-01",
                "fecha_hasta": "2026-01-01",
            },
            "fecha_desde",
        ),
        (
            {
                "periodo": "personalizado",
                "fecha_desde": "2025-01-01",
                "fecha_hasta": "2026-01-02",
            },
            "fecha_hasta",
        ),
        (
            {"periodo": "hoy", "fecha_desde": "2026-01-01"},
            "fecha_desde",
        ),
    ],
)
def test_invalid_custom_ranges_return_422(
    client, auth_headers, escenario, query_string, campo
):
    res = client.get(URL, query_string=query_string, headers=auth_headers(escenario.dueno))

    assert res.status_code == 422
    assert campo in res.get_json()["error"]["fields"]


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
def test_invalid_period_returns_422(client, auth_headers, escenario):
    res = client.get(
        URL, query_string={"periodo": "trimestre"}, headers=auth_headers(escenario.dueno)
    )

    assert res.status_code == 422
    assert "periodo" in res.get_json()["error"]["fields"]


def test_invalid_client_or_employee_id_returns_422(client, auth_headers, escenario):
    cliente = client.get(
        URL, query_string={"cliente": "abc"}, headers=auth_headers(escenario.dueno)
    )
    colaborador = client.get(
        URL, query_string={"colaborador": "0"}, headers=auth_headers(escenario.dueno)
    )

    assert cliente.status_code == 422
    assert "cliente" in cliente.get_json()["error"]["fields"]
    assert colaborador.status_code == 422
    assert "colaborador" in colaborador.get_json()["error"]["fields"]
