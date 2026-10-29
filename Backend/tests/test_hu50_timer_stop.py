"""HU_50: Detener temporizador y guardar el registro."""
from datetime import datetime, time, timedelta, timezone
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import TZ_MX, today_mx, utcnow
from app.extensions import db
from app.models.notification import TIPO_CIERRE_AUTOMATICO, Notificacion
from app.models.time_entry import RegistroTiempo, TemporizadorActivo
from app.services.time_service import (
    MSG_MENOS_DE_UN_MINUTO,
    MSG_SIN_TIMER,
    MSG_TIMER_NO_COINCIDE,
)
from tests.time_helpers import crear_categoria, crear_cliente, crear_tarea, crear_temporizador

URL = "/api/v1/time-entries/timer"
STOP_URL = "/api/v1/time-entries/timer/stop"


@pytest.fixture()
def escenario(make_user):
    contador = make_user(
        "ana.stop@despacho.com", "CONTADOR", nombre="Ana Contadora", grado="SENIOR"
    )
    cliente = crear_cliente(contador)
    categoria = crear_categoria("Fiscal")
    hoy = today_mx()
    tarea = crear_tarea(
        titulo="Declaración anual",
        cliente=cliente,
        categoria=categoria,
        asignado=contador,
        creador=contador,
        fecha_limite=hoy + timedelta(days=5),
    )
    otra = crear_tarea(
        titulo="Otra tarea",
        cliente=cliente,
        categoria=categoria,
        asignado=contador,
        creador=contador,
        fecha_limite=hoy + timedelta(days=5),
    )
    return SimpleNamespace(
        contador=contador,
        cliente=cliente,
        categoria=categoria,
        tarea=tarea,
        otra=otra,
        hoy=hoy,
    )


def _registros() -> list[RegistroTiempo]:
    db.session.expire_all()
    return list(db.session.execute(select(RegistroTiempo)).scalars().all())


def _notificaciones(usuario_id: int) -> list[Notificacion]:
    db.session.expire_all()
    stmt = select(Notificacion).where(Notificacion.usuario_id == usuario_id)
    return list(db.session.execute(stmt).scalars().all())


def _inicio_utc(fecha, hora: time) -> datetime:
    return datetime.combine(fecha, hora, tzinfo=TZ_MX).astimezone(timezone.utc)


# ---------------------------------------------------------------------------
# Acceso y casos base
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.post(STOP_URL, json={"descripcion": "Trabajo de prueba"}).status_code == 401


def test_stop_without_active_timer(client, auth_headers, escenario):
    res = client.post(
        STOP_URL,
        json={"descripcion": "Trabajo de prueba"},
        headers=auth_headers(escenario.contador),
    )
    assert res.status_code == 404
    assert res.get_json()["error"]["message"] == MSG_SIN_TIMER


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"descripcion": "abc"},
        {"descripcion": "x" * 501},
    ],
)
def test_description_is_required_and_has_length(client, auth_headers, escenario, payload):
    crear_temporizador(
        escenario.contador, escenario.tarea, utcnow() - timedelta(minutes=5)
    )
    res = client.post(STOP_URL, json=payload, headers=auth_headers(escenario.contador))
    assert res.status_code == 422
    assert "descripcion" in res.get_json()["error"]["fields"]


def test_temporizador_id_must_match(client, auth_headers, escenario):
    crear_temporizador(
        escenario.contador, escenario.tarea, utcnow() - timedelta(minutes=5)
    )
    res = client.post(
        STOP_URL,
        json={"descripcion": "Trabajo de prueba", "temporizador_id": 999999},
        headers=auth_headers(escenario.contador),
    )
    assert res.status_code == 409
    assert res.get_json()["error"]["message"] == MSG_TIMER_NO_COINCIDE
    assert len(_registros()) == 0


# ---------------------------------------------------------------------------
# Guardado del registro
# ---------------------------------------------------------------------------
def test_stop_saves_timer_record(client, auth_headers, escenario):
    crear_temporizador(
        escenario.contador,
        escenario.tarea,
        utcnow() - timedelta(minutes=5, seconds=20),
    )

    res = client.post(
        STOP_URL,
        json={"descripcion": "Revisión de declaración anual"},
        headers=auth_headers(escenario.contador),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["guardado"] is True
    assert data["descartado"] is False
    assert data["cierre_automatico"] is False

    registro = data["registro"]
    assert registro["tarea_id"] == escenario.tarea.id
    assert registro["empleado_nombre"] == "Ana Contadora"
    assert registro["cliente_nombre"] == "Cliente Tiempos"
    assert registro["tipo"] == "TIMER"
    assert registro["duracion_minutos"] == 5
    assert registro["horas"] == 0.08
    assert registro["fecha"] == escenario.hoy.isoformat()
    assert registro["nivel_escalafon"] == "SENIOR"
    assert registro["descripcion"] == "Revisión de declaración anual"

    db.session.expire_all()
    assert db.session.execute(select(TemporizadorActivo)).scalar_one_or_none() is None
    guardado = db.session.execute(select(RegistroTiempo)).scalar_one()
    assert guardado.created_by == escenario.contador.id


def test_duration_rounds_to_nearest_minute(client, auth_headers, escenario):
    crear_temporizador(
        escenario.contador, escenario.tarea, utcnow() - timedelta(seconds=90)
    )

    res = client.post(
        STOP_URL,
        json={"descripcion": "Tiempo corto"},
        headers=auth_headers(escenario.contador),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["registro"]["duracion_minutos"] == 2


def test_less_than_one_minute_is_discarded_with_notice(client, auth_headers, escenario):
    crear_temporizador(
        escenario.contador, escenario.tarea, utcnow() - timedelta(seconds=20)
    )

    res = client.post(
        STOP_URL,
        json={"descripcion": "Tiempo insuficiente"},
        headers=auth_headers(escenario.contador),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["guardado"] is False
    assert data["descartado"] is True
    assert data["registro"] is None
    assert data["mensaje"] == MSG_MENOS_DE_UN_MINUTO
    assert len(_registros()) == 0
    db.session.expire_all()
    assert db.session.execute(select(TemporizadorActivo)).scalar_one_or_none() is None


def test_stop_twice_returns_not_found(client, auth_headers, escenario):
    crear_temporizador(
        escenario.contador, escenario.tarea, utcnow() - timedelta(minutes=5)
    )
    headers = auth_headers(escenario.contador)

    assert client.post(
        STOP_URL, json={"descripcion": "Primer guardado"}, headers=headers
    ).status_code == 200

    res = client.post(STOP_URL, json={"descripcion": "Segundo guardado"}, headers=headers)
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Cierre automático a las 23:59
# ---------------------------------------------------------------------------
def test_timer_from_previous_day_is_closed_automatically(client, auth_headers, escenario):
    ayer = escenario.hoy - timedelta(days=1)
    crear_temporizador(
        escenario.contador, escenario.tarea, _inicio_utc(ayer, time(22, 0))
    )

    res = client.get(URL, headers=auth_headers(escenario.contador))

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["activo"] is None
    aviso = data["aviso_cierre_automatico"]
    assert aviso["guardado"] is True
    assert aviso["cierre_automatico"] is True

    registro = aviso["registro"]
    assert registro["fecha"] == ayer.isoformat()
    assert registro["descripcion"] == "Cierre automático"
    assert registro["cierre_automatico"] is True
    assert registro["duracion_minutos"] == 120  # 22:00 a 23:59:59 redondeado

    db.session.expire_all()
    assert db.session.execute(select(TemporizadorActivo)).scalar_one_or_none() is None
    notificaciones = _notificaciones(escenario.contador.id)
    assert len(notificaciones) == 1
    assert notificaciones[0].tipo == TIPO_CIERRE_AUTOMATICO
    assert notificaciones[0].entidad_id == registro["id"]


def test_stop_on_previous_day_timer_returns_auto_close(client, auth_headers, escenario):
    ayer = escenario.hoy - timedelta(days=1)
    crear_temporizador(
        escenario.contador, escenario.tarea, _inicio_utc(ayer, time(8, 0))
    )

    res = client.post(
        STOP_URL,
        json={"descripcion": "No debería usarse"},
        headers=auth_headers(escenario.contador),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["cierre_automatico"] is True
    assert data["registro"]["descripcion"] == "Cierre automático"
    assert len(_registros()) == 1


def test_auto_close_discards_a_previous_day_timer_shorter_than_one_minute(
    client, auth_headers, escenario
):
    ayer = escenario.hoy - timedelta(days=1)
    crear_temporizador(
        escenario.contador, escenario.tarea, _inicio_utc(ayer, time(23, 59, 40))
    )

    res = client.get(URL, headers=auth_headers(escenario.contador))

    data = res.get_json()["data"]
    assert data["activo"] is None
    aviso = data["aviso_cierre_automatico"]
    assert aviso["guardado"] is False
    assert aviso["descartado"] is True
    assert aviso["cierre_automatico"] is True
    assert len(_registros()) == 0
