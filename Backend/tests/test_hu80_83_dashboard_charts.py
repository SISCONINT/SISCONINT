"""HU_80, HU_81, HU_82 y HU_83: gráficas y estado de tareas del dashboard."""
import pytest

from app.services.dashboard_service import _filas_categoria
from tests.dashboard_helpers import crear_escenario
from tests.time_helpers import crear_registro

URL = "/api/v1/dashboard"


def _data(res) -> dict:
    return res.get_json()["data"]


@pytest.fixture()
def escenario(make_user):
    return crear_escenario(make_user)


# ---------------------------------------------------------------------------
# HU_80: tiempo por empleado
# ---------------------------------------------------------------------------
def test_time_by_employee_is_ordered_from_most_to_least(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    filas = _data(res)["tiempo_por_empleado"]
    assert [fila["colaborador_id"] for fila in filas] == [
        escenario.contador1.id,
        escenario.contador2.id,
    ]
    assert [fila["horas"] for fila in filas] == [2.0, 1.0]
    assert [fila["minutos"] for fila in filas] == [120, 60]
    assert [fila["nombre"] for fila in filas] == ["Ana Contadora", "Beto Contador"]


def test_time_by_employee_rounds_hours_to_one_decimal(
    client, auth_headers, escenario
):
    crear_registro(
        escenario.tarea1,
        escenario.contador1,
        fecha=escenario.hoy,
        minutos=50,
        descripcion="Trabajo extra",
    )

    res = client.get(URL, headers=auth_headers(escenario.dueno))

    filas = {fila["colaborador_id"]: fila for fila in _data(res)["tiempo_por_empleado"]}
    assert filas[escenario.contador1.id]["minutos"] == 170
    assert filas[escenario.contador1.id]["horas"] == 2.8


# ---------------------------------------------------------------------------
# HU_81: tiempo por cliente
# ---------------------------------------------------------------------------
def test_time_by_client_is_ordered_from_most_to_least(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    filas = _data(res)["tiempo_por_cliente"]
    assert [fila["cliente_id"] for fila in filas] == [
        escenario.cliente1.id,
        escenario.cliente2.id,
    ]
    assert [fila["horas"] for fila in filas] == [2.0, 1.0]
    assert [fila["nombre"] for fila in filas] == ["Cliente Uno", "Cliente Dos"]


# ---------------------------------------------------------------------------
# HU_82: distribución por categoría
# ---------------------------------------------------------------------------
def test_category_distribution_rolls_subcategories_up_to_the_root(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    filas = _data(res)["distribucion_por_categoria"]
    assert [fila["nombre"] for fila in filas] == ["Fiscal", "Laboral"]
    assert [fila["horas"] for fila in filas] == [2.0, 1.0]
    assert [fila["minutos"] for fila in filas] == [120, 60]
    assert [fila["porcentaje"] for fila in filas] == [66.7, 33.3]
    assert sum(fila["porcentaje"] for fila in filas) == 100.0
    assert filas[0]["categoria_id"] == escenario.fiscal.id


def test_categories_without_hours_are_omitted(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    nombres = {
        fila["nombre"] for fila in _data(res)["distribucion_por_categoria"]
    }
    assert "Sin horas" not in nombres


def test_category_percentages_are_adjusted_to_sum_100():
    filas = _filas_categoria(
        [
            {"categoria_id": 1, "nombre": "A", "minutos": 1},
            {"categoria_id": 2, "nombre": "B", "minutos": 1},
            {"categoria_id": 3, "nombre": "C", "minutos": 1},
        ]
    )

    assert [fila["porcentaje"] for fila in filas] == [33.4, 33.3, 33.3]
    assert sum(fila["porcentaje"] for fila in filas) == 100.0


# ---------------------------------------------------------------------------
# HU_83: estado de tareas
# ---------------------------------------------------------------------------
def test_task_state_counts_are_a_current_snapshot(client, auth_headers, escenario):
    res = client.get(
        URL, query_string={"periodo": "hoy"}, headers=auth_headers(escenario.dueno)
    )

    estados = _data(res)["estado_tareas"]
    assert estados == {
        "POR_HACER": 1,
        "EN_PROGRESO": 1,
        "EN_REVISION": 1,
        "COMPLETADO": 2,
        "vencidas": 1,
        "total": 5,
    }


def test_overdue_excludes_completed_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.dueno))

    estados = _data(res)["estado_tareas"]
    assert estados["COMPLETADO"] == 2
    assert estados["vencidas"] == 1
    assert escenario.tarea2.fecha_limite < escenario.hoy
    assert escenario.tarea4.fecha_limite < escenario.hoy


def test_task_counts_respect_the_client_filter(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente1.id},
        headers=auth_headers(escenario.dueno),
    )

    estados = _data(res)["estado_tareas"]
    assert estados["POR_HACER"] == 1
    assert estados["EN_PROGRESO"] == 1
    assert estados["EN_REVISION"] == 0
    assert estados["COMPLETADO"] == 1
    assert estados["total"] == 3


def test_task_counts_respect_the_employee_filter(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"colaborador": escenario.contador1.id},
        headers=auth_headers(escenario.dueno),
    )

    estados = _data(res)["estado_tareas"]
    assert estados["POR_HACER"] == 1
    assert estados["EN_PROGRESO"] == 1
    assert estados["COMPLETADO"] == 0
    assert estados["total"] == 2
