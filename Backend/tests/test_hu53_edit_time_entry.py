"""HU_53: Editar registro de tiempo."""
from datetime import timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import today_mx
from app.extensions import db
from app.models.audit_log import BitacoraAuditoria
from app.models.time_entry import RegistroTiempo
from app.services.time_service import MSG_LIMITE_DIARIO, MSG_TAREA_NO_ASIGNADA
from tests.time_helpers import crear_categoria, crear_cliente, crear_registro, crear_tarea

URL = "/api/v1/time-entries"


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.edit@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.edit@despacho.com", "ADMINISTRADOR", nombre="Admin Edita")
    coordinador = make_user(
        "carla.edit@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user("ana.edit@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.edit@despacho.com", "CONTADOR", nombre="Beto Contador")

    cliente = crear_cliente(contador1)
    categoria = crear_categoria("Fiscal")
    hoy = today_mx()

    tarea_c1 = crear_tarea(
        titulo="Declaración de Ana",
        cliente=cliente,
        categoria=categoria,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )
    tarea_c1_b = crear_tarea(
        titulo="Otra tarea de Ana",
        cliente=cliente,
        categoria=categoria,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )
    tarea_c2 = crear_tarea(
        titulo="Tarea de Beto",
        cliente=cliente,
        categoria=categoria,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )
    tarea_admin = crear_tarea(
        titulo="Tarea del administrador",
        cliente=cliente,
        categoria=categoria,
        asignado=admin,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )

    registros = {
        "hoy_c1": crear_registro(
            tarea_c1, contador1, minutos=60, descripcion="Trabajo de hoy"
        ),
        "ayer_c1": crear_registro(
            tarea_c1,
            contador1,
            fecha=hoy - timedelta(days=1),
            minutos=60,
            descripcion="Trabajo de ayer",
        ),
        "hoy_c2": crear_registro(
            tarea_c2, contador2, minutos=60, descripcion="Trabajo de Beto"
        ),
    }

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
        cliente=cliente,
        categoria=categoria,
        tarea_c1=tarea_c1,
        tarea_c1_b=tarea_c1_b,
        tarea_c2=tarea_c2,
        tarea_admin=tarea_admin,
        registros=registros,
        hoy=hoy,
    )


def _recargar(registro_id: int):
    db.session.expire_all()
    return db.session.get(RegistroTiempo, registro_id)


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert (
        client.put(
            f"{URL}/{escenario.registros['hoy_c1'].id}",
            json={"descripcion": "Sin sesión"},
        ).status_code
        == 401
    )


def test_record_not_found(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/999999",
        json={"descripcion": "No existe"},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Autor: mismo día natural
# ---------------------------------------------------------------------------
def test_author_edits_own_record_same_day(client, auth_headers, escenario):
    registro = escenario.registros["hoy_c1"]
    res = client.put(
        f"{URL}/{registro.id}",
        json={
            "horas": 2,
            "minutos": 15,
            "descripcion": "Trabajo corregido",
            "tarea_id": escenario.tarea_c1_b.id,
        },
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["duracion_minutos"] == 135
    assert data["horas"] == 2.25
    assert data["descripcion"] == "Trabajo corregido"
    assert data["tarea_id"] == escenario.tarea_c1_b.id

    guardado = _recargar(registro.id)
    assert guardado.updated_by == escenario.contador1.id
    assert guardado.updated_at is not None


def test_edit_only_hours_keeps_current_minutes(client, auth_headers, escenario):
    registro = crear_registro(
        escenario.tarea_c1, escenario.contador1, minutos=90, descripcion="Noventa minutos"
    )

    res = client.put(
        f"{URL}/{registro.id}",
        json={"horas": 2},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["duracion_minutos"] == 150


def test_edit_only_minutes_keeps_current_hours(client, auth_headers, escenario):
    registro = crear_registro(
        escenario.tarea_c1, escenario.contador1, minutos=90, descripcion="Noventa minutos"
    )

    res = client.put(
        f"{URL}/{registro.id}",
        json={"minutos": 45},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["duracion_minutos"] == 105


def test_edit_accepts_duration_in_minutes(client, auth_headers, escenario):
    registro = escenario.registros["hoy_c1"]
    res = client.put(
        f"{URL}/{registro.id}",
        json={"duracion_minutos": 45},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["duracion_minutos"] == 45


def test_author_cannot_edit_record_from_another_day(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['ayer_c1'].id}",
        json={"descripcion": "Intento fuera de plazo"},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    assert "permiso vigente" in res.get_json()["error"]["message"]


def test_author_cannot_edit_someone_elses_record(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['hoy_c2'].id}",
        json={"descripcion": "No es mío"},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 403


def test_coordinador_cannot_edit_someone_elses_record(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['hoy_c1'].id}",
        json={"descripcion": "No es mío"},
        headers=auth_headers(escenario.coordinador),
    )
    assert res.status_code == 403


def test_coordinador_edits_his_own_record_same_day(client, auth_headers, escenario):
    registro = crear_registro(
        escenario.tarea_c1, escenario.coordinador, minutos=30, descripcion="Trabajo propio"
    )

    res = client.put(
        f"{URL}/{registro.id}",
        json={"descripcion": "Trabajo propio corregido"},
        headers=auth_headers(escenario.coordinador),
    )

    assert res.status_code == 200


# ---------------------------------------------------------------------------
# Dueño y Administrador: cualquier registro
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("actor", ["dueno", "admin"])
def test_owner_and_admin_edit_any_record(client, auth_headers, escenario, actor):
    res = client.put(
        f"{URL}/{escenario.registros['ayer_c1'].id}",
        json={"descripcion": "Corrección de administración"},
        headers=auth_headers(getattr(escenario, actor)),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["descripcion"] == "Corrección de administración"
    assert _recargar(data["id"]).updated_by == getattr(escenario, actor).id


# ---------------------------------------------------------------------------
# Validaciones del registro manual
# ---------------------------------------------------------------------------
def test_new_task_must_be_assigned_to_the_record_author(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['hoy_c1'].id}",
        json={"tarea_id": escenario.tarea_admin.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_TAREA_NO_ASIGNADA


def test_total_zero_is_rejected(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['hoy_c1'].id}",
        json={"horas": 0, "minutos": 0},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422


def test_description_length_is_validated(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.registros['hoy_c1'].id}",
        json={"descripcion": "abc"},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 422
    assert "descripcion" in res.get_json()["error"]["fields"]


def test_cannot_exceed_24_hours_after_edit(client, auth_headers, escenario):
    crear_registro(
        escenario.tarea_c1, escenario.contador1, minutos=23 * 60, descripcion="Casi un día"
    )

    res = client.put(
        f"{URL}/{escenario.registros['hoy_c1'].id}",
        json={"horas": 2, "minutos": 0},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 422
    assert res.get_json()["error"]["message"] == MSG_LIMITE_DIARIO


def test_no_changes_returns_the_record(client, auth_headers, escenario):
    registro = escenario.registros["hoy_c1"]
    res = client.put(
        f"{URL}/{registro.id}",
        json={
            "horas": 1,
            "minutos": 0,
            "descripcion": "Trabajo de hoy",
            "tarea_id": escenario.tarea_c1.id,
        },
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == registro.id


# ---------------------------------------------------------------------------
# RG-13: auditoría
# ---------------------------------------------------------------------------
def test_edit_is_audited(client, auth_headers, escenario):
    registro = escenario.registros["hoy_c1"]
    client.put(
        f"{URL}/{registro.id}",
        json={"horas": 2, "minutos": 0, "descripcion": "Trabajo corregido"},
        headers=auth_headers(escenario.contador1),
    )

    db.session.expire_all()
    stmt = select(BitacoraAuditoria).where(
        BitacoraAuditoria.entidad == "registro_tiempo",
        BitacoraAuditoria.entidad_id == registro.id,
        BitacoraAuditoria.accion == "MODIFICAR",
    )
    auditoria = db.session.execute(stmt).scalars().all()

    assert len(auditoria) == 1
    assert auditoria[0].usuario_id == escenario.contador1.id
    assert "duracion_minutos" in auditoria[0].detalle
    assert auditoria[0].detalle["descripcion"]["despues"] == "Trabajo corregido"
