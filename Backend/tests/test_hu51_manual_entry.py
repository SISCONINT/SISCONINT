"""HU_51: Registrar tiempo manualmente."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import today_mx
from app.extensions import db
from app.models.time_entry import RegistroTiempo
from app.services.time_service import (
    MSG_LIMITE_DIARIO,
    MSG_TAREA_NO_ASIGNADA,
    MSG_TOTAL_CERO,
)
from tests.time_helpers import crear_categoria, crear_cliente, crear_registro, crear_tarea

URL = "/api/v1/time-entries"


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.manual@despacho.com", "DUENO", nombre="Dora Dueña", grado="ADMIN")
    admin = make_user(
        "admin.manual@despacho.com", "ADMINISTRADOR", nombre="Admin Manual", grado="ADMIN"
    )
    coordinador = make_user(
        "carla.manual@despacho.com", "COORDINADOR", nombre="Carla Coordinadora", grado="SENIOR"
    )
    contador1 = make_user(
        "ana.manual@despacho.com", "CONTADOR", nombre="Ana Contadora", grado="JUNIOR"
    )
    contador2 = make_user(
        "beto.manual@despacho.com", "CONTADOR", nombre="Beto Contador", grado="JUNIOR"
    )

    cliente = crear_cliente(contador1)
    categoria = crear_categoria("Fiscal")
    hoy = today_mx()

    tareas = {}
    for nombre, usuario in (
        ("dueno", dueno),
        ("admin", admin),
        ("coordinador", coordinador),
        ("contador1", contador1),
        ("contador2", contador2),
    ):
        tareas[nombre] = crear_tarea(
            titulo=f"Tarea manual de {nombre}",
            cliente=cliente,
            categoria=categoria,
            asignado=usuario,
            creador=admin,
            fecha_limite=hoy + timedelta(days=5),
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
        hoy=hoy,
    )


def _payload(escenario, **cambios) -> dict:
    data = {
        "tarea_id": escenario.tareas["contador1"].id,
        "horas": 1,
        "minutos": 30,
        "descripcion": "Revisión de papeles de trabajo",
    }
    data.update(cambios)
    return data


def _registros() -> list[RegistroTiempo]:
    db.session.expire_all()
    return list(db.session.execute(select(RegistroTiempo)).scalars().all())


# ---------------------------------------------------------------------------
# Acceso y alta
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.post(URL, json=_payload(escenario)).status_code == 401


def test_inactive_user_is_rejected(client, auth_headers, make_user, escenario):
    inactivo = make_user("inactivo.manual@despacho.com", "CONTADOR", estatus="INACTIVO")
    res = client.post(URL, json=_payload(escenario), headers=auth_headers(inactivo))
    assert res.status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador", "contador1"])
def test_all_roles_register_manual_time(client, auth_headers, escenario, actor):
    usuario = getattr(escenario, actor)
    res = client.post(
        URL,
        json=_payload(escenario, tarea_id=escenario.tareas[actor].id),
        headers=auth_headers(usuario),
    )

    assert res.status_code == 201
    data = res.get_json()["data"]
    assert data["tarea_id"] == escenario.tareas[actor].id
    assert data["empleado_id"] == usuario.id
    assert data["empleado_nombre"] == usuario.nombre_completo
    assert data["tipo"] == "MANUAL"
    assert data["duracion_minutos"] == 90
    assert data["horas"] == 1.5
    assert data["fecha"] == escenario.hoy.isoformat()
    assert data["nivel_escalafon"] == usuario.grado_escalafon
    assert data["cierre_automatico"] is False


def test_manual_entry_persists_author_and_level(client, auth_headers, escenario):
    client.post(URL, json=_payload(escenario), headers=auth_headers(escenario.contador1))

    registro = _registros()[0]
    assert registro.created_by == escenario.contador1.id
    assert registro.colaborador_id == escenario.contador1.id
    assert registro.nivel_escalafon == "JUNIOR"
    assert registro.permiso_fuera_plazo_id is None


# ---------------------------------------------------------------------------
# Validaciones de campos
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cambios,campo",
    [
        ({"tarea_id": None, "horas": 1, "minutos": 0}, "tarea_id"),
        ({"horas": None}, "horas"),
        ({"minutos": None}, "minutos"),
        ({"descripcion": None}, "descripcion"),
        ({"descripcion": "abc"}, "descripcion"),
        ({"descripcion": "x" * 501}, "descripcion"),
        ({"horas": 24, "minutos": 0}, "horas"),
        ({"horas": 0, "minutos": 60}, "minutos"),
    ],
)
def test_field_validations(client, auth_headers, escenario, cambios, campo):
    res = client.post(
        URL,
        json=_payload(escenario, **cambios),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422
    assert campo in res.get_json()["error"]["fields"]
    assert _registros() == []


def test_total_must_be_greater_than_zero(client, auth_headers, escenario):
    res = client.post(
        URL,
        json=_payload(escenario, horas=0, minutos=0),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["minutos"] == [MSG_TOTAL_CERO]


def test_task_must_be_assigned_to_the_user(client, auth_headers, escenario):
    res = client.post(
        URL,
        json=_payload(escenario, tarea_id=escenario.tareas["contador2"].id),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_TAREA_NO_ASIGNADA
    assert _registros() == []


def test_task_not_found(client, auth_headers, escenario):
    res = client.post(
        URL,
        json=_payload(escenario, tarea_id=999999),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Fecha (RG-04)
# ---------------------------------------------------------------------------
def test_fecha_por_defecto_es_hoy(client, auth_headers, escenario):
    res = client.post(
        URL,
        json=_payload(escenario, fecha=None),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 201
    assert res.get_json()["data"]["fecha"] == escenario.hoy.isoformat()


def test_past_date_requires_permission(client, auth_headers, escenario):
    ayer = escenario.hoy - timedelta(days=1)
    res = client.post(
        URL,
        json=_payload(escenario, fecha=ayer.isoformat()),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 403
    assert "permiso vigente" in res.get_json()["error"]["message"]
    assert _registros() == []


def test_future_date_is_rejected(client, auth_headers, escenario):
    manana = escenario.hoy + timedelta(days=1)
    res = client.post(
        URL,
        json=_payload(escenario, fecha=manana.isoformat()),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422
    assert "fecha" in res.get_json()["error"]["fields"]
    assert _registros() == []


def test_invalid_date_format(client, auth_headers, escenario):
    res = client.post(
        URL,
        json=_payload(escenario, fecha="31/12/2026"),
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422
    assert "fecha" in res.get_json()["error"]["fields"]


# ---------------------------------------------------------------------------
# Límite de 24 horas por día
# ---------------------------------------------------------------------------
def test_cannot_exceed_24_hours_per_day(client, auth_headers, escenario):
    crear_registro(escenario.tareas["contador1"], escenario.contador1, minutos=23 * 60)

    res = client.post(
        URL,
        json=_payload(escenario, horas=2, minutos=0),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 422
    assert res.get_json()["error"]["message"] == MSG_LIMITE_DIARIO
    assert res.get_json()["error"]["minutos_registrados"] == 23 * 60
    assert len(_registros()) == 1


def test_exactly_24_hours_is_allowed(client, auth_headers, escenario):
    crear_registro(escenario.tareas["contador1"], escenario.contador1, minutos=23 * 60)

    res = client.post(
        URL,
        json=_payload(escenario, horas=1, minutos=0),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 201
    assert len(_registros()) == 2


def test_daily_limit_is_per_user(client, auth_headers, escenario):
    crear_registro(escenario.tareas["contador2"], escenario.contador2, minutos=23 * 60)

    res = client.post(
        URL,
        json=_payload(escenario, horas=2, minutos=0),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 201
