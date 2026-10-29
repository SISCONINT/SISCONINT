"""HU_49: Iniciar temporizador en una tarea."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select

from app.core.datetime_utils import today_mx
from app.extensions import db
from app.models.time_entry import TemporizadorActivo
from app.services.time_service import (
    MSG_TAREA_COMPLETADA,
    MSG_TAREA_NO_ASIGNADA,
    MSG_TIMER_ACTIVO,
)
from tests.time_helpers import crear_categoria, crear_cliente, crear_tarea

URL = "/api/v1/time-entries/timer"


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.timer@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.timer@despacho.com", "ADMINISTRADOR", nombre="Admin Timer")
    coordinador = make_user(
        "carla.timer@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user("ana.timer@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.timer@despacho.com", "CONTADOR", nombre="Beto Contador")

    cliente = crear_cliente(contador1)
    categoria = crear_categoria("Fiscal")
    hoy = today_mx()

    tareas = {
        "dueno": crear_tarea(
            titulo="Tarea del dueño",
            cliente=cliente,
            categoria=categoria,
            asignado=dueno,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "admin": crear_tarea(
            titulo="Tarea del administrador",
            cliente=cliente,
            categoria=categoria,
            asignado=admin,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "coordinador": crear_tarea(
            titulo="Tarea de la coordinadora",
            cliente=cliente,
            categoria=categoria,
            asignado=coordinador,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "contador1": crear_tarea(
            titulo="Declaración mensual",
            cliente=cliente,
            categoria=categoria,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "contador2": crear_tarea(
            titulo="Tarea de otro contador",
            cliente=cliente,
            categoria=categoria,
            asignado=contador2,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
    }
    completada = crear_tarea(
        titulo="Tarea ya completada",
        cliente=cliente,
        categoria=categoria,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy - timedelta(days=1),
        estado="COMPLETADO",
    )

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
        cliente=cliente,
        categoria=categoria,
        tareas=tareas,
        completada=completada,
    )


def _contar_temporizadores() -> int:
    return db.session.execute(select(func.count()).select_from(TemporizadorActivo)).scalar_one()


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={"tarea_id": escenario.tareas["contador1"].id}).status_code == 401


def test_inactive_user_is_rejected(client, auth_headers, make_user, escenario):
    inactivo = make_user("inactivo.timer@despacho.com", "CONTADOR", estatus="INACTIVO")
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador1"].id},
        headers=auth_headers(inactivo),
    )
    assert res.status_code == 401


# ---------------------------------------------------------------------------
# Inicio del temporizador
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador", "contador1"])
def test_all_roles_start_timer_on_their_task(client, auth_headers, escenario, actor):
    usuario = getattr(escenario, actor)
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas[actor].id},
        headers=auth_headers(usuario),
    )

    assert res.status_code == 201
    data = res.get_json()["data"]
    activo = data["activo"]
    assert activo["tarea_id"] == escenario.tareas[actor].id
    assert activo["tarea_titulo"] == escenario.tareas[actor].titulo
    assert activo["cliente_nombre"] == "Cliente Tiempos"
    assert activo["iniciado_en"] is not None
    assert len(activo["transcurrido"]) == 8
    assert activo["transcurrido_segundos"] >= 0
    assert data["aviso_cierre_automatico"] is None


def test_start_returns_server_start_time(client, auth_headers, escenario):
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador1"].id},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 201
    iniciado = res.get_json()["data"]["activo"]["iniciado_en"]
    assert iniciado.endswith("+00:00")  # RG-04: se guarda en UTC


def test_cannot_start_on_task_assigned_to_someone_else(client, auth_headers, escenario):
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador2"].id},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    body = res.get_json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == MSG_TAREA_NO_ASIGNADA
    assert _contar_temporizadores() == 0


def test_admin_cannot_start_on_a_task_assigned_to_a_contador(client, auth_headers, escenario):
    """HU_49: la tarea debe estar asignada al usuario, sin excepción de rol."""
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador1"].id},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 403


def test_cannot_start_on_completed_task(client, auth_headers, escenario):
    res = client.post(
        URL,
        json={"tarea_id": escenario.completada.id},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 422
    body = res.get_json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == MSG_TAREA_COMPLETADA


def test_task_not_found(client, auth_headers, escenario):
    res = client.post(
        URL,
        json={"tarea_id": 999999},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"


def test_task_id_is_required(client, auth_headers, escenario):
    res = client.post(URL, json={}, headers=auth_headers(escenario.contador1))
    assert res.status_code == 422
    assert "tarea_id" in res.get_json()["error"]["fields"]


def test_only_one_active_timer_per_user(client, auth_headers, escenario):
    headers = auth_headers(escenario.contador1)
    primera = client.post(
        URL, json={"tarea_id": escenario.tareas["contador1"].id}, headers=headers
    )
    assert primera.status_code == 201

    segunda = client.post(
        URL, json={"tarea_id": escenario.tareas["contador1"].id}, headers=headers
    )

    assert segunda.status_code == 409
    body = segunda.get_json()
    assert body["error"]["code"] == "CONFLICT"
    assert body["error"]["message"] == MSG_TIMER_ACTIVO
    activo = body["error"]["temporizador"]
    assert activo["tarea_id"] == escenario.tareas["contador1"].id
    assert _contar_temporizadores() == 1


# ---------------------------------------------------------------------------
# Consulta del temporizador (sigue corriendo al recargar)
# ---------------------------------------------------------------------------
def test_get_timer_returns_active_timer(client, auth_headers, escenario):
    headers = auth_headers(escenario.contador1)
    client.post(URL, json={"tarea_id": escenario.tareas["contador1"].id}, headers=headers)

    res = client.get(URL, headers=headers)

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["activo"] is not None
    assert data["activo"]["tarea_id"] == escenario.tareas["contador1"].id
    assert data["aviso_cierre_automatico"] is None


def test_get_timer_without_active_timer(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["activo"] is None
    assert data["aviso_cierre_automatico"] is None


def test_timers_are_independent_per_user(client, auth_headers, escenario):
    client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador1"].id},
        headers=auth_headers(escenario.contador1),
    )
    res = client.post(
        URL,
        json={"tarea_id": escenario.tareas["contador2"].id},
        headers=auth_headers(escenario.contador2),
    )
    assert res.status_code == 201
    assert _contar_temporizadores() == 2
