"""HU_32: Editar tarea."""
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import today_mx, utcnow
from app.core.semaforo import SEMAFORO_ROJO, SEMAFORO_VERDE
from app.extensions import db
from app.models.audit_log import BitacoraAuditoria
from app.models.catalog import CategoriaProyecto
from app.models.client import ESTATUS_PAUSADO, Cliente
from app.models.notification import Notificacion
from app.models.task import Tarea
from app.models.time_entry import RegistroTiempo
from app.models.user import ESTATUS_INACTIVO
from app.services.task_service import MSG_TAREA_DE_ADMINISTRACION

URL = "/api/v1/tasks"
MSG_FORBIDDEN = "No tienes permiso para esta acción"


# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------
def _crear_cliente(contador, nombre: str, rfc: str, estatus: str = "ACTIVO") -> Cliente:
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
        estatus=estatus,
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente


def _crear_categoria(
    nombre: str, padre: CategoriaProyecto | None = None, activa: bool = True
) -> CategoriaProyecto:
    categoria = CategoriaProyecto(
        nombre=nombre,
        padre_id=padre.id if padre else None,
        activa=activa,
        orden=0,
    )
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
    estado: str = "EN_PROGRESO",
    prioridad: str = "ALTA",
    horas_estimadas: float | None = 4.0,
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Descripción completa de la tarea",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        obligacion_id=123,
        periodo="2026-10",
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad=prioridad,
        estado=estado,
        horas_estimadas=horas_estimadas,
        notificar_cliente=True,
        cliente_notificado=False,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _crear_tiempo(tarea: Tarea, colaborador, minutos: int) -> RegistroTiempo:
    registro = RegistroTiempo(
        tarea_id=tarea.id,
        colaborador_id=colaborador.id,
        fecha=today_mx(),
        duracion_minutos=minutos,
        tipo="MANUAL",
        descripcion="Registro de apoyo",
        nivel_escalafon=colaborador.grado_escalafon,
        created_by=colaborador.id,
    )
    db.session.add(registro)
    db.session.commit()
    return registro


def _payload(tarea: Tarea, **overrides) -> dict:
    """Cuerpo completo del formulario de edición (los mismos campos del alta)."""
    payload = {
        "titulo": tarea.titulo,
        "descripcion": tarea.descripcion,
        "cliente_id": tarea.cliente_id,
        "categoria_id": tarea.categoria_id,
        "asignado_id": tarea.asignado_id,
        "fecha_limite": tarea.fecha_limite.isoformat(),
        "hora_limite": tarea.hora_limite.strftime("%H:%M"),
        "prioridad": tarea.prioridad,
        "horas_estimadas": float(tarea.horas_estimadas),
        "notificar_cliente": tarea.notificar_cliente,
    }
    payload.update(overrides)
    return payload


def _notificaciones() -> list[Notificacion]:
    return list(
        db.session.execute(select(Notificacion).order_by(Notificacion.id)).scalars()
    )


def _recargar(tarea_id: int) -> Tarea:
    """Relee la tarea desde la BD (la petición usa otra sesión)."""
    db.session.expire_all()
    return db.session.get(Tarea, tarea_id)


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.edita@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.edita@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.edita@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.edita@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.edita@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente = _crear_cliente(contador1, "Cliente Editable", "XEdi010101000")
    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)

    hoy = today_mx()
    tarea = _crear_tarea(
        titulo="Declaración anual del cliente",
        cliente=cliente,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=2),
    )

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        coordinador=coordinador,
        cliente=cliente,
        fiscal=fiscal,
        declaraciones=declaraciones,
        tarea=tarea,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso (RG-02 / RG-12)
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    res = client.put(f"{URL}/{escenario.tarea.id}", json={"titulo": "Otro título"})
    assert res.status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador"])
def test_management_roles_edit_any_task(client, auth_headers, escenario, actor):
    usuario = getattr(escenario, actor)

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea, titulo="Título corregido"),
        headers=auth_headers(usuario),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["titulo"] == "Título corregido"
    assert data["updated_by"] == usuario.id
    assert _recargar(escenario.tarea.id).titulo == "Título corregido"


def test_accountant_edits_task_he_created(client, auth_headers, escenario):
    tarea = _crear_tarea(
        titulo="Tarea creada por contadora",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador2,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=4),
    )

    res = client.put(
        f"{URL}/{tarea.id}",
        json=_payload(tarea, prioridad="MEDIA"),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["prioridad"] == "MEDIA"


def test_accountant_cannot_edit_task_created_by_admin(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea, titulo="Cambio no permitido"),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    body = res.get_json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == MSG_TAREA_DE_ADMINISTRACION
    assert "data" not in body
    assert _recargar(escenario.tarea.id).titulo == escenario.tarea.titulo


def test_accountant_cannot_edit_task_created_by_coordinator(
    client, auth_headers, escenario
):
    tarea = _crear_tarea(
        titulo="Tarea de coordinación",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.coordinador,
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    res = client.put(
        f"{URL}/{tarea.id}",
        json=_payload(tarea, titulo="Cambio no permitido"),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_TAREA_DE_ADMINISTRACION


def test_accountant_cannot_edit_task_created_by_owner(client, auth_headers, escenario):
    tarea = _crear_tarea(
        titulo="Tarea de la dirección",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.dueno,
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    res = client.put(
        f"{URL}/{tarea.id}",
        json=_payload(tarea, titulo="Cambio no permitido"),
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN


def test_accountant_cannot_edit_task_outside_his_scope(client, auth_headers, escenario):
    """RG-02: si no puede verla, el 403 es genérico y no revela datos."""
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea, titulo="Cambio no permitido"),
        headers=auth_headers(escenario.contador2),
    )

    assert res.status_code == 403
    body = res.get_json()
    assert body["error"]["message"] == MSG_FORBIDDEN
    assert "data" not in body


def test_nonexistent_task_returns_404(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/999999",
        json={"titulo": "Título cualquiera"},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 404
    assert res.get_json()["error"]["message"] == "Tarea no encontrada"


def test_deleted_task_returns_404(client, auth_headers, escenario):
    escenario.tarea.deleted_at = utcnow()
    db.session.commit()

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Título cualquiera"},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 404


def test_invalid_json_body_returns_422(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        data="no es json",
        content_type="application/json",
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Validaciones del alta aplicadas a la edición
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("titulo", "abc"),
        ("titulo", "   "),
        ("prioridad", "URGENTE"),
        ("horas_estimadas", 2.3),
        ("cliente_id", 999999),
        ("categoria_id", 999999),
    ],
)
def test_creation_validations_apply(client, auth_headers, escenario, campo, valor):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={campo: valor},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code in (404, 422)
    assert campo in res.get_json()["error"]["fields"]


def test_past_deadline_is_rejected_when_it_changes(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"fecha_limite": (escenario.hoy - timedelta(days=1)).isoformat()},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["fecha_limite"] == [
        "La fecha límite debe ser hoy o posterior"
    ]


def test_overdue_task_can_be_edited_keeping_its_date(client, auth_headers, escenario):
    escenario.tarea.fecha_limite = escenario.hoy - timedelta(days=3)
    db.session.commit()

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea, descripcion="Descripción actualizada"),
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["descripcion"] == "Descripción actualizada"
    assert data["semaforo"] == SEMAFORO_ROJO


def test_paused_client_cannot_be_assigned(client, auth_headers, escenario):
    pausado = _crear_cliente(
        escenario.contador1, "Cliente Pausado", "XPau010101000", estatus=ESTATUS_PAUSADO
    )

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"cliente_id": pausado.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["cliente_id"] == ["El cliente no está Activo"]


def test_inactive_category_cannot_be_assigned(client, auth_headers, escenario):
    inactiva = _crear_categoria("Categoría retirada", activa=False)

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"categoria_id": inactiva.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["categoria_id"] == [
        "Selecciona una categoría activa"
    ]


def test_assignee_must_be_an_active_accountant(client, auth_headers, make_user, escenario):
    inactivo = make_user(
        "inactivo.edita@despacho.com", "CONTADOR", estatus=ESTATUS_INACTIVO
    )

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"asignado_id": inactivo.id},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["asignado_id"] == [
        "Debe ser un Contador Activo"
    ]

    no_contador = make_user("coordinador.edita@despacho.com", "COORDINADOR")
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"asignado_id": no_contador.id},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 422
    assert res.get_json()["error"]["fields"]["asignado_id"] == [
        "Debe ser un Contador Activo"
    ]


# ---------------------------------------------------------------------------
# Actualización parcial y campos que no se editan aquí
# ---------------------------------------------------------------------------
def test_partial_update_only_changes_sent_fields(client, auth_headers, escenario):
    antes = db.session.get(Tarea, escenario.tarea.id)
    original = SimpleNamespace(
        descripcion=antes.descripcion,
        asignado_id=antes.asignado_id,
        fecha_limite=antes.fecha_limite,
        hora_limite=antes.hora_limite,
        prioridad=antes.prioridad,
        horas_estimadas=antes.horas_estimadas,
    )

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Solo cambia el título"},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    tarea = _recargar(escenario.tarea.id)
    assert tarea.titulo == "Solo cambia el título"
    assert tarea.descripcion == original.descripcion
    assert tarea.asignado_id == original.asignado_id
    assert tarea.fecha_limite == original.fecha_limite
    assert tarea.hora_limite == original.hora_limite
    assert tarea.prioridad == original.prioridad
    assert tarea.horas_estimadas == original.horas_estimadas


def test_trimmed_text_is_saved(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "   Título con espacios   "},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).titulo == "Título con espacios"


def test_state_is_not_edited_here(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea, titulo="Título nuevo", estado="COMPLETADO"),
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).estado == "EN_PROGRESO"


def test_estimated_hours_can_be_cleared(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"horas_estimadas": None},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).horas_estimadas is None


# ---------------------------------------------------------------------------
# Notificaciones (HU_32)
# ---------------------------------------------------------------------------
def test_reassignment_notifies_new_and_previous_accountant(
    client, auth_headers, escenario
):
    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"asignado_id": escenario.contador2.id},
        headers=auth_headers(escenario.admin),
    )

    nuevas, anteriores = _notificaciones()
    assert nuevas.usuario_id == escenario.contador2.id
    assert nuevas.tipo == "REASIGNACION"
    assert nuevas.titulo == "Tarea reasignada a ti"
    assert escenario.tarea.titulo in nuevas.mensaje
    assert nuevas.entidad_tipo == "TAREA"
    assert nuevas.entidad_id == escenario.tarea.id
    assert nuevas.leida is False

    assert anteriores.usuario_id == escenario.contador1.id
    assert anteriores.tipo == "REASIGNACION"
    assert anteriores.titulo == "Tarea reasignada"
    assert escenario.tarea.titulo in anteriores.mensaje


def test_reassignment_keeps_time_attributed_to_who_recorded_it(
    client, auth_headers, escenario
):
    registro = _crear_tiempo(escenario.tarea, escenario.contador1, 90)

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"asignado_id": escenario.contador2.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    db.session.expire_all()
    assert (
        db.session.get(RegistroTiempo, registro.id).colaborador_id
        == escenario.contador1.id
    )
    por_colaborador = res.get_json()["data"]["tiempo"]["por_colaborador"]
    assert [(t["colaborador_nombre"], t["minutos"]) for t in por_colaborador] == [
        ("Ana Contadora", 90)
    ]


def test_deadline_change_notifies_the_assigned_accountant(client, auth_headers, escenario):
    nueva_fecha = escenario.hoy + timedelta(days=6)

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"fecha_limite": nueva_fecha.isoformat()},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["semaforo"] == SEMAFORO_VERDE
    (notificacion,) = _notificaciones()
    assert notificacion.usuario_id == escenario.contador1.id
    assert notificacion.tipo == "CAMBIO_FECHA"
    assert notificacion.titulo == "Cambió la fecha límite"
    assert nueva_fecha.isoformat() in notificacion.mensaje
    assert notificacion.entidad_tipo == "TAREA"
    assert notificacion.entidad_id == escenario.tarea.id


def test_reassignment_and_deadline_change_notify_once_per_recipient(
    client, auth_headers, escenario
):
    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={
            "asignado_id": escenario.contador2.id,
            "fecha_limite": (escenario.hoy + timedelta(days=6)).isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )

    notificaciones = _notificaciones()
    assert len(notificaciones) == 2
    assert {n.usuario_id for n in notificaciones} == {
        escenario.contador1.id,
        escenario.contador2.id,
    }
    assert {n.tipo for n in notificaciones} == {"REASIGNACION"}


def test_no_notification_when_nothing_relevant_changes(
    client, auth_headers, escenario
):
    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Título actualizado"},
        headers=auth_headers(escenario.admin),
    )

    assert _notificaciones() == []


def test_accountant_is_not_notified_of_his_own_change(client, auth_headers, escenario):
    tarea = _crear_tarea(
        titulo="Tarea de la contadora",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    client.put(
        f"{URL}/{tarea.id}",
        json={"fecha_limite": (escenario.hoy + timedelta(days=7)).isoformat()},
        headers=auth_headers(escenario.contador1),
    )

    assert _notificaciones() == []


# ---------------------------------------------------------------------------
# Auditoría (RG-13)
# ---------------------------------------------------------------------------
def test_update_is_audited_with_before_and_after(client, auth_headers, escenario):
    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Título auditado", "prioridad": "BAJA"},
        headers=auth_headers(escenario.admin),
    )

    (log,) = list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == "tarea")
        ).scalars()
    )
    assert log.usuario_id == escenario.admin.id
    assert log.entidad_id == escenario.tarea.id
    assert log.accion == "MODIFICAR"
    assert log.detalle["titulo"] == {
        "antes": "Declaración anual del cliente",
        "despues": "Título auditado",
    }
    assert log.detalle["prioridad"] == {"antes": "ALTA", "despues": "BAJA"}


def test_no_audit_when_payload_changes_nothing(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json=_payload(escenario.tarea),
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert db.session.execute(select(BitacoraAuditoria)).first() is None


def test_audit_serializes_dates_and_decimals(client, auth_headers, escenario):
    nueva_fecha = escenario.hoy + timedelta(days=5)

    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={
            "fecha_limite": nueva_fecha.isoformat(),
            "hora_limite": "18:45",
            "horas_estimadas": 7.5,
        },
        headers=auth_headers(escenario.admin),
    )

    (log,) = list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == "tarea")
        ).scalars()
    )
    assert log.detalle["fecha_limite"]["despues"] == nueva_fecha.isoformat()
    assert log.detalle["hora_limite"] == {"antes": "15:30:00", "despues": "18:45:00"}
    assert log.detalle["horas_estimadas"] == {"antes": 4.0, "despues": 7.5}


# ---------------------------------------------------------------------------
# Respuesta con el contrato del detalle (HU_31)
# ---------------------------------------------------------------------------
def test_response_returns_the_updated_detail(client, auth_headers, escenario):
    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Declaración anual 2026", "prioridad": "MEDIA"},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["id"] == escenario.tarea.id
    assert data["titulo"] == "Declaración anual 2026"
    assert data["prioridad"] == "MEDIA"
    assert data["creador_nombre"] == "Admin Tareas"
    assert data["asignado_nombre"] == "Ana Contadora"
    assert data["categoria_padre_nombre"] == "Fiscal"
    assert data["semaforo"] == "AMARILLO"
    assert data["tiempo"]["total_minutos"] == 0
    assert data["subtareas"]["avance"] == "0/0"
    assert data["comentarios"] == []


def test_updated_at_is_refreshed(client, auth_headers, escenario):
    antes = db.session.get(Tarea, escenario.tarea.id).updated_at
    assert isinstance(antes, datetime)

    client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Título con nueva marca"},
        headers=auth_headers(escenario.admin),
    )

    despues = _recargar(escenario.tarea.id).updated_at
    assert despues >= antes
