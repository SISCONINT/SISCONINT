"""HU_66: recordatorio de tareas que vencen mañana (job diario de las 08:00)."""
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.notification import Notificacion
from app.models.task import (
    ESTADO_COMPLETADO,
    ESTADO_EN_PROGRESO,
    ESTADO_POR_HACER,
    Tarea,
)
from app.services import notification_service

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


def _crear_tarea(
    *,
    titulo: str,
    cliente: Cliente,
    categoria: CategoriaProyecto,
    asignado,
    creador,
    fecha_limite: date,
    estado: str = ESTADO_POR_HACER,
    prioridad: str = "ALTA",
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Tarea para el recordatorio",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad=prioridad,
        estado=estado,
        horas_estimadas=4.0,
        notificar_cliente=False,
        cliente_notificado=False,
        completada_en=utcnow() if estado == ESTADO_COMPLETADO else None,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _notificaciones(usuario_id: int | None = None) -> list[Notificacion]:
    from sqlalchemy import select

    stmt = select(Notificacion).order_by(Notificacion.id)
    if usuario_id is not None:
        stmt = stmt.where(Notificacion.usuario_id == usuario_id)
    return list(db.session.execute(stmt).scalars())


@pytest.fixture()
def escenario(make_user):
    admin = make_user("admin.hu66@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.hu66@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.hu66@despacho.com", "CONTADOR", nombre="Beto Contador")

    cliente1 = _crear_cliente(contador1, "Cliente Uno", "XHu66010101000")
    cliente2 = _crear_cliente(contador2, "Cliente Dos", "XHu66010101001")
    fiscal = _crear_categoria("Fiscal")
    hoy = today_mx()
    manana = hoy + timedelta(days=1)

    tareas = {
        "manana": _crear_tarea(
            titulo="Declaración de mañana",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=manana,
            estado=ESTADO_EN_PROGRESO,
            prioridad="ALTA",
        ),
        "manana_otro": _crear_tarea(
            titulo="Pago de mañana",
            cliente=cliente2,
            categoria=fiscal,
            asignado=contador2,
            creador=admin,
            fecha_limite=manana,
            prioridad="BAJA",
        ),
        "hoy": _crear_tarea(
            titulo="Vence hoy",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy,
        ),
        "pasado": _crear_tarea(
            titulo="Vence en dos días",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy + timedelta(days=2),
        ),
        "completada": _crear_tarea(
            titulo="Completada para mañana",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=manana,
            estado=ESTADO_COMPLETADO,
        ),
        "eliminada": _crear_tarea(
            titulo="Eliminada para mañana",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=manana,
        ),
    }
    tareas["eliminada"].deleted_at = utcnow()
    db.session.commit()

    return SimpleNamespace(
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        cliente1=cliente1,
        cliente2=cliente2,
        fiscal=fiscal,
        tareas=tareas,
        hoy=hoy,
        manana=manana,
    )


# ---------------------------------------------------------------------------
# Generación del recordatorio
# ---------------------------------------------------------------------------
def test_creates_a_reminder_for_each_open_task_due_tomorrow(escenario):
    resultado = notification_service.notify_upcoming_deadlines()

    assert resultado == {
        "fecha_limite": escenario.manana.isoformat(),
        "creadas": 2,
        "omitidas": 0,
    }
    notificaciones = _notificaciones()
    assert len(notificaciones) == 2
    assert {n.usuario_id for n in notificaciones} == {
        escenario.contador1.id,
        escenario.contador2.id,
    }


def test_reminder_has_the_expected_content(escenario):
    notification_service.notify_upcoming_deadlines()

    (notificacion,) = _notificaciones(escenario.contador1.id)
    assert notificacion.tipo == "VENCIMIENTO"
    assert notificacion.titulo == "Tarea próxima a vencer"
    assert "Declaración de mañana" in notificacion.mensaje
    assert "Cliente Uno" in notificacion.mensaje
    assert "ALTA" in notificacion.mensaje
    assert escenario.manana.isoformat() in notificacion.mensaje
    assert notificacion.entidad_tipo == "TAREA"
    assert notificacion.entidad_id == escenario.tareas["manana"].id
    assert notificacion.clave_unica == (
        f"VENCIMIENTO:{escenario.tareas['manana'].id}:{escenario.manana.isoformat()}"
    )
    assert notificacion.leida is False


def test_excludes_tasks_due_today_later_completed_or_deleted(escenario):
    notification_service.notify_upcoming_deadlines()

    ids = {n.entidad_id for n in _notificaciones()}
    assert ids == {
        escenario.tareas["manana"].id,
        escenario.tareas["manana_otro"].id,
    }
    assert escenario.tareas["hoy"].id not in ids
    assert escenario.tareas["pasado"].id not in ids
    assert escenario.tareas["completada"].id not in ids
    assert escenario.tareas["eliminada"].id not in ids


def test_running_the_job_twice_does_not_duplicate_reminders(escenario):
    notification_service.notify_upcoming_deadlines()

    resultado = notification_service.notify_upcoming_deadlines()

    assert resultado == {
        "fecha_limite": escenario.manana.isoformat(),
        "creadas": 0,
        "omitidas": 2,
    }
    assert len(_notificaciones()) == 2


def test_reminder_appears_in_the_assignee_inbox(client, auth_headers, escenario):
    notification_service.notify_upcoming_deadlines()

    bandeja = client.get(
        URL_NOTIFICACIONES, headers=auth_headers(escenario.contador1)
    )

    assert bandeja.status_code == 200
    (fila,) = bandeja.get_json()["data"]
    assert fila["tipo"] == "VENCIMIENTO"
    assert fila["enlace"] == f"/tareas/{escenario.tareas['manana'].id}"
    assert bandeja.get_json()["meta"]["no_leidas"] == 1


# ---------------------------------------------------------------------------
# Comando programado (08:00)
# ---------------------------------------------------------------------------
def test_cli_command_creates_the_reminders(app, escenario):
    runner = app.test_cli_runner()

    resultado = runner.invoke(args=["recordatorios-vencimiento"])

    assert resultado.exit_code == 0
    assert "2 creados" in resultado.output
    assert len(_notificaciones()) == 2


# ---------------------------------------------------------------------------
# Retención de 90 días
# ---------------------------------------------------------------------------
def test_purge_removes_notifications_older_than_90_days(escenario):
    vieja = Notificacion(
        usuario_id=escenario.contador1.id,
        tipo="VENCIMIENTO",
        titulo="Vieja",
        mensaje="Más de 90 días",
        created_at=utcnow() - timedelta(days=91),
    )
    reciente = Notificacion(
        usuario_id=escenario.contador1.id,
        tipo="VENCIMIENTO",
        titulo="Reciente",
        mensaje="Dentro de la retención",
        created_at=utcnow() - timedelta(days=10),
    )
    db.session.add_all([vieja, reciente])
    db.session.commit()

    eliminadas = notification_service.purge_expired()

    assert eliminadas == 1
    assert _notificaciones() == [reciente]


def test_cli_command_purges_expired_notifications(app, escenario):
    db.session.add(
        Notificacion(
            usuario_id=escenario.contador1.id,
            tipo="VENCIMIENTO",
            titulo="Vieja",
            mensaje="Más de 90 días",
            created_at=utcnow() - timedelta(days=120),
        )
    )
    db.session.commit()
    runner = app.test_cli_runner()

    resultado = runner.invoke(args=["purgar-notificaciones"])

    assert resultado.exit_code == 0
    assert "1" in resultado.output
    assert _notificaciones() == []
