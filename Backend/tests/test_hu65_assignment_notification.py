"""HU_65: notificar la asignación de una tarea al contador."""
from datetime import time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx
from app.extensions import db, mail
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.notification import Notificacion
from app.models.task import ESTADO_COMPLETADO, Tarea
from app.services import task_service

URL_TAREAS = "/api/v1/tasks"
URL_NOTIFICACIONES = "/api/v1/notifications"


# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------
def _crear_cliente(contador, nombre: str, rfc: str) -> Cliente:
    cliente = Cliente(
        nombre_completo=nombre,
        rfc=rfc,
        tipo_persona="FISICA",
        forma_pago="EFECTIVO",
        contador_asignado_id=contador.id,
        giro="Servicios",
        telefono="4420000000",
        correo=f"{rfc.lower()}@cliente.com",
        codigo_postal="90000",
        calle="Calle 1",
        no_exterior="1",
        colonia="Centro",
        ciudad="Tlaxcala",
        estado="Tlaxcala",
        tiene_trabajadores=False,
        estatus="ACTIVO",
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente


def _crear_categoria(nombre: str) -> CategoriaProyecto:
    categoria = CategoriaProyecto(nombre=nombre, activa=True, orden=0)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def _payload(escenario, **overrides) -> dict:
    payload = {
        "titulo": "Declaración mensual de IVA",
        "descripcion": "Presentar la declaración del periodo",
        "cliente_id": escenario.cliente.id,
        "categoria_id": escenario.categoria.id,
        "asignado_id": escenario.contador1.id,
        "fecha_limite": (escenario.hoy + timedelta(days=3)).isoformat(),
        "hora_limite": "15:30",
        "prioridad": "ALTA",
        "horas_estimadas": 2.0,
        "notificar_cliente": True,
    }
    payload.update(overrides)
    return payload


def _notificaciones(usuario_id: int, tipo: str | None = None) -> list[Notificacion]:
    from sqlalchemy import select

    stmt = select(Notificacion).where(Notificacion.usuario_id == usuario_id)
    if tipo is not None:
        stmt = stmt.where(Notificacion.tipo == tipo)
    return list(db.session.execute(stmt.order_by(Notificacion.id)).scalars())


@pytest.fixture()
def escenario(make_user):
    admin = make_user("admin.hu65@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    coordinador = make_user(
        "carla.hu65@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user("ana.hu65@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.hu65@despacho.com", "CONTADOR", nombre="Beto Contador")

    cliente = _crear_cliente(contador1, "Cliente Uno", "XHu65010101000")
    categoria = _crear_categoria("Fiscal")

    return SimpleNamespace(
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
        cliente=cliente,
        categoria=categoria,
        hoy=today_mx(),
    )


# ---------------------------------------------------------------------------
# Alta de tarea
# ---------------------------------------------------------------------------
def test_creating_a_task_notifies_the_assignee(client, auth_headers, escenario):
    res = client.post(
        URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 201
    tarea = db.session.get(Tarea, res.get_json()["data"]["id"])
    (notificacion,) = _notificaciones(escenario.contador1.id)

    assert notificacion.tipo == "ASIGNACION"
    assert notificacion.titulo == "Nueva tarea asignada"
    assert tarea.titulo in notificacion.mensaje
    assert escenario.cliente.nombre_completo in notificacion.mensaje
    assert "ALTA" in notificacion.mensaje
    assert tarea.fecha_limite.isoformat() in notificacion.mensaje
    assert notificacion.entidad_tipo == "TAREA"
    assert notificacion.entidad_id == tarea.id
    assert notificacion.leida is False


def test_assignment_notification_is_in_app_only_in_the_mvp(
    client, auth_headers, escenario
):
    with mail.record_messages() as outbox:
        res = client.post(
            URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
        )

    assert res.status_code == 201
    assert outbox == []


def test_assignee_sees_the_notification_with_the_task_link(
    client, auth_headers, escenario
):
    res = client.post(
        URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
    )
    tarea_id = res.get_json()["data"]["id"]

    bandeja = client.get(
        URL_NOTIFICACIONES, headers=auth_headers(escenario.contador1)
    )

    assert bandeja.status_code == 200
    (fila,) = bandeja.get_json()["data"]
    assert fila["tipo"] == "ASIGNACION"
    assert fila["entidad_tipo"] == "TAREA"
    assert fila["entidad_id"] == tarea_id
    assert fila["enlace"] == f"/tareas/{tarea_id}"
    assert bandeja.get_json()["meta"]["no_leidas"] == 1


def test_other_users_do_not_see_the_assignment(client, auth_headers, escenario):
    client.post(URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin))

    bandeja = client.get(
        URL_NOTIFICACIONES, headers=auth_headers(escenario.contador2)
    )

    assert bandeja.get_json()["data"] == []


def test_no_notification_when_the_assignee_creates_the_task(escenario):
    data = {
        "titulo": "Tarea de la propia contadora",
        "descripcion": "Sin aviso porque se asigna a sí misma",
        "cliente_id": escenario.cliente.id,
        "categoria_id": escenario.categoria.id,
        "asignado_id": escenario.contador1.id,
        "fecha_limite": escenario.hoy + timedelta(days=2),
        "hora_limite": time(15, 30),
        "prioridad": "MEDIA",
        "horas_estimadas": None,
        "notificar_cliente": False,
    }

    tarea = task_service.create_task(escenario.contador1, data)

    assert tarea.id is not None
    assert _notificaciones(escenario.contador1.id) == []


# ---------------------------------------------------------------------------
# Reasignación (HU_32 + HU_65)
# ---------------------------------------------------------------------------
def test_reassignment_notifies_the_new_assignee_with_context(
    client, auth_headers, escenario
):
    creada = client.post(
        URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
    )
    tarea_id = creada.get_json()["data"]["id"]

    res = client.put(
        f"{URL_TAREAS}/{tarea_id}",
        json={"asignado_id": escenario.contador2.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    (nueva,) = _notificaciones(escenario.contador2.id, tipo="REASIGNACION")
    assert nueva.titulo == "Tarea reasignada a ti"
    assert "Declaración mensual de IVA" in nueva.mensaje
    assert escenario.cliente.nombre_completo in nueva.mensaje
    assert "ALTA" in nueva.mensaje
    assert nueva.entidad_tipo == "TAREA"
    assert nueva.entidad_id == tarea_id


def test_reassignment_to_the_same_accountant_does_not_notify(
    client, auth_headers, escenario
):
    creada = client.post(
        URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
    )
    tarea_id = creada.get_json()["data"]["id"]

    res = client.put(
        f"{URL_TAREAS}/{tarea_id}",
        json={"asignado_id": escenario.contador1.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _notificaciones(escenario.contador1.id, tipo="REASIGNACION") == []
    assert _notificaciones(escenario.contador2.id) == []


# ---------------------------------------------------------------------------
# La notificación no altera la tarea
# ---------------------------------------------------------------------------
def test_assignment_does_not_change_the_task(client, auth_headers, escenario):
    res = client.post(
        URL_TAREAS, json=_payload(escenario), headers=auth_headers(escenario.admin)
    )

    tarea = db.session.get(Tarea, res.get_json()["data"]["id"])
    assert tarea.estado != ESTADO_COMPLETADO
    assert tarea.cliente_notificado is False
    assert tarea.completada_en is None
    assert tarea.updated_by == escenario.admin.id
