"""HU_43: Mover tarea entre columnas."""
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import today_mx, utcnow
from app.extensions import db, mail
from app.models.audit_log import BitacoraAuditoria
from app.models.catalog import CategoriaProyecto
from app.models.client import CONTACTO_PRINCIPAL, Cliente, ContactoCliente
from app.models.notification import TIPO_CAMBIO_ESTADO, Notificacion
from app.models.task import (
    ESTADO_COMPLETADO,
    ESTADO_EN_PROGRESO,
    ESTADO_EN_REVISION,
    ESTADO_POR_HACER,
    HistorialEstadoTarea,
    Subtarea,
    Tarea,
)
from app.services import email_service
from app.services.task_service import (
    MSG_SUBTAREAS_PENDIENTES,
    MSG_TAREA_DE_ADMINISTRACION,
)

URL = "/api/v1/tasks"
MSG_FORBIDDEN = "No tienes permiso para esta acción"


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


def _crear_contacto_principal(cliente: Cliente, correo: str) -> ContactoCliente:
    contacto = ContactoCliente(
        cliente_id=cliente.id,
        tipo=CONTACTO_PRINCIPAL,
        nombre_completo="Contacto Principal",
        telefono="4421234567",
        correo=correo,
        cargo="Representante legal",
    )
    db.session.add(contacto)
    db.session.commit()
    return contacto


def _crear_categoria(nombre: str, padre: CategoriaProyecto | None = None) -> CategoriaProyecto:
    categoria = CategoriaProyecto(
        nombre=nombre,
        padre_id=padre.id if padre else None,
        activa=True,
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
    estado: str = ESTADO_POR_HACER,
    notificar_cliente: bool = True,
    completada_en=None,
    completada_por=None,
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Tarea para mover entre columnas",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad="ALTA",
        estado=estado,
        horas_estimadas=4.0,
        notificar_cliente=notificar_cliente,
        cliente_notificado=False,
        completada_en=completada_en,
        completada_por=completada_por,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _crear_subtarea(tarea: Tarea, titulo: str, completada: bool = False) -> Subtarea:
    subtarea = Subtarea(
        tarea_id=tarea.id,
        titulo=titulo,
        completada=completada,
        completada_en=utcnow() if completada else None,
    )
    db.session.add(subtarea)
    db.session.commit()
    return subtarea


def _recargar(tarea_id: int) -> Tarea:
    """Relee la tarea desde la BD (la petición usa otra sesión)."""
    db.session.expire_all()
    return db.session.get(Tarea, tarea_id)


def _data(res) -> dict:
    return res.get_json()["data"]


def _patch(client, headers, tarea, estado: str, **extra):
    return client.patch(
        f"{URL}/{tarea.id}/estado",
        json={"estado": estado, **extra},
        headers=headers,
    )


def _historial(tarea_id: int) -> list[HistorialEstadoTarea]:
    return list(
        db.session.execute(
            select(HistorialEstadoTarea).where(HistorialEstadoTarea.tarea_id == tarea_id)
        ).scalars()
    )


def _notificaciones() -> list[Notificacion]:
    return list(
        db.session.execute(select(Notificacion).order_by(Notificacion.id)).scalars()
    )


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.mueve@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.mueve@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.mueve@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.mueve@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.mueve@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente = _crear_cliente(contador1, "Cliente Kanban", "XKan010101000")
    contacto = _crear_contacto_principal(cliente, "principal@cliente.com")
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
    creada_por_contador = _crear_tarea(
        titulo="Tarea creada por el contador",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador2,
        creador=contador1,
        fecha_limite=hoy + timedelta(days=4),
    )
    ajena = _crear_tarea(
        titulo="Tarea de coordinación",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador2,
        creador=coordinador,
        fecha_limite=hoy + timedelta(days=3),
        estado=ESTADO_EN_REVISION,
    )

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        coordinador=coordinador,
        cliente=cliente,
        contacto=contacto,
        fiscal=fiscal,
        declaraciones=declaraciones,
        tarea=tarea,
        creada_por_contador=creada_por_contador,
        ajena=ajena,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert _patch(client, {}, escenario.tarea, ESTADO_EN_PROGRESO).status_code == 401


def test_unknown_task_returns_404(client, auth_headers, escenario):
    res = client.patch(
        f"{URL}/999999/estado",
        json={"estado": ESTADO_EN_PROGRESO},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 404
    assert res.get_json()["error"]["message"] == "Tarea no encontrada"


def test_deleted_task_returns_404(client, auth_headers, escenario):
    escenario.tarea.deleted_at = utcnow()
    db.session.commit()

    res = _patch(client, auth_headers(escenario.admin), escenario.tarea, ESTADO_EN_PROGRESO)

    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Roles y alcance (RG-12)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("rol", ["dueno", "admin", "coordinador"])
def test_owner_admin_and_coordinator_move_any_task(
    client, auth_headers, escenario, rol
):
    actor = getattr(escenario, rol)

    res = _patch(client, auth_headers(actor), escenario.ajena, ESTADO_EN_PROGRESO)

    assert res.status_code == 200
    assert _data(res)["estado"] == ESTADO_EN_PROGRESO
    assert _recargar(escenario.ajena.id).estado == ESTADO_EN_PROGRESO


def test_accountant_moves_task_assigned_to_him(client, auth_headers, escenario):
    """Aunque la haya creado Administración, puede moverla porque está asignada a él."""
    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO
    )

    assert res.status_code == 200
    assert _data(res)["estado"] == ESTADO_EN_PROGRESO
    assert _data(res)["asignado_id"] == escenario.contador1.id


def test_accountant_cannot_move_a_task_created_by_him_but_assigned_elsewhere(
    client, auth_headers, escenario
):
    res = _patch(
        client,
        auth_headers(escenario.contador1),
        escenario.creada_por_contador,
        ESTADO_EN_PROGRESO,
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN
    assert _recargar(escenario.creada_por_contador.id).estado == ESTADO_POR_HACER


def test_accountant_cannot_move_an_unrelated_task(client, auth_headers, escenario):
    res = _patch(
        client, auth_headers(escenario.contador1), escenario.ajena, ESTADO_EN_PROGRESO
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN


# ---------------------------------------------------------------------------
# Transiciones
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("origen", "destino"),
    [
        (ESTADO_POR_HACER, ESTADO_EN_PROGRESO),
        (ESTADO_EN_PROGRESO, ESTADO_EN_REVISION),
        (ESTADO_EN_REVISION, ESTADO_COMPLETADO),
        (ESTADO_COMPLETADO, ESTADO_EN_PROGRESO),
        (ESTADO_EN_REVISION, ESTADO_POR_HACER),
        (ESTADO_EN_PROGRESO, ESTADO_POR_HACER),
    ],
)
def test_all_transitions_forward_and_backward(
    client, auth_headers, escenario, origen, destino
):
    tarea = escenario.tarea
    tarea.estado = origen
    if origen == ESTADO_COMPLETADO:
        tarea.completada_en = utcnow() - timedelta(days=1)
        tarea.completada_por = escenario.admin.id
    db.session.commit()

    res = _patch(client, auth_headers(escenario.admin), tarea, destino)

    assert res.status_code == 200
    assert _data(res)["estado"] == destino
    assert _recargar(tarea.id).estado == destino


def test_state_is_trimmed_and_uppercased(client, auth_headers, escenario):
    res = _patch(
        client, auth_headers(escenario.admin), escenario.tarea, "  en_progreso  "
    )

    assert res.status_code == 200
    assert _data(res)["estado"] == ESTADO_EN_PROGRESO


def test_same_state_is_a_no_op(client, auth_headers, escenario):
    res = _patch(
        client, auth_headers(escenario.admin), escenario.tarea, ESTADO_POR_HACER
    )

    assert res.status_code == 200
    assert _data(res)["estado"] == ESTADO_POR_HACER
    assert _historial(escenario.tarea.id) == []
    assert db.session.execute(select(BitacoraAuditoria)).first() is None
    assert _notificaciones() == []


# ---------------------------------------------------------------------------
# Completar y reabrir
# ---------------------------------------------------------------------------
def test_completion_stores_date_and_user(client, auth_headers, escenario):
    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_COMPLETADO
    )

    assert res.status_code == 200
    data = _data(res)
    assert data["estado"] == ESTADO_COMPLETADO
    assert data["completada_en"] is not None
    assert data["completada_por"] == escenario.contador1.id
    tarea = _recargar(escenario.tarea.id)
    assert tarea.completada_en is not None
    assert tarea.completada_por == escenario.contador1.id


def test_reopening_clears_completion_data(client, auth_headers, escenario):
    escenario.tarea.estado = ESTADO_COMPLETADO
    escenario.tarea.completada_en = utcnow() - timedelta(days=1)
    escenario.tarea.completada_por = escenario.admin.id
    db.session.commit()

    res = _patch(
        client, auth_headers(escenario.admin), escenario.tarea, ESTADO_EN_PROGRESO
    )

    assert res.status_code == 200
    assert _data(res)["completada_en"] is None
    assert _data(res)["completada_por"] is None
    tarea = _recargar(escenario.tarea.id)
    assert tarea.completada_en is None
    assert tarea.completada_por is None


# ---------------------------------------------------------------------------
# Subtareas pendientes (confirmación RG-14)
# ---------------------------------------------------------------------------
def test_completing_with_pending_subtasks_returns_409(client, auth_headers, escenario):
    _crear_subtarea(escenario.tarea, "Paso pendiente 1")
    _crear_subtarea(escenario.tarea, "Paso pendiente 2")

    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_COMPLETADO
    )

    assert res.status_code == 409
    error = res.get_json()["error"]
    assert error["message"] == MSG_SUBTAREAS_PENDIENTES
    assert error["subtareas_pendientes"] == 2
    assert _recargar(escenario.tarea.id).estado == ESTADO_POR_HACER
    assert _historial(escenario.tarea.id) == []
    assert db.session.execute(select(BitacoraAuditoria)).first() is None


def test_confirmed_move_to_completed_succeeds(client, auth_headers, escenario):
    _crear_subtarea(escenario.tarea, "Paso pendiente")

    res = _patch(
        client,
        auth_headers(escenario.contador1),
        escenario.tarea,
        ESTADO_COMPLETADO,
        confirmar_subtareas_pendientes=True,
    )

    assert res.status_code == 200
    assert _data(res)["estado"] == ESTADO_COMPLETADO
    assert _data(res)["completada_en"] is not None


def test_completed_subtasks_do_not_ask_for_confirmation(
    client, auth_headers, escenario
):
    _crear_subtarea(escenario.tarea, "Paso terminado", completada=True)

    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_COMPLETADO
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).estado == ESTADO_COMPLETADO


def test_pending_subtasks_only_matter_when_completing(
    client, auth_headers, escenario
):
    _crear_subtarea(escenario.tarea, "Paso pendiente")

    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_REVISION
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).estado == ESTADO_EN_REVISION


# ---------------------------------------------------------------------------
# Historial (HU_31/HU_43)
# ---------------------------------------------------------------------------
def test_move_is_recorded_in_the_history(client, auth_headers, escenario):
    res = _patch(
        client,
        auth_headers(escenario.contador1),
        escenario.tarea,
        ESTADO_EN_REVISION,
    )

    assert res.status_code == 200
    historial = _data(res)["historial_estados"]
    assert len(historial) == 1
    assert historial[0]["estado_anterior"] == ESTADO_POR_HACER
    assert historial[0]["estado_nuevo"] == ESTADO_EN_REVISION
    assert historial[0]["usuario_id"] == escenario.contador1.id
    assert historial[0]["usuario_nombre"] == "Ana Contadora"
    assert historial[0]["created_at"] is not None


def test_successive_moves_append_to_the_history(client, auth_headers, escenario):
    headers = auth_headers(escenario.admin)

    _patch(client, headers, escenario.tarea, ESTADO_EN_PROGRESO)
    res = _patch(client, headers, escenario.tarea, ESTADO_EN_REVISION)

    assert [(h["estado_anterior"], h["estado_nuevo"]) for h in _data(res)["historial_estados"]] == [
        (ESTADO_POR_HACER, ESTADO_EN_PROGRESO),
        (ESTADO_EN_PROGRESO, ESTADO_EN_REVISION),
    ]


# ---------------------------------------------------------------------------
# Auditoría (RG-13)
# ---------------------------------------------------------------------------
def test_move_is_audited(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO)

    (log,) = list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == "tarea")
        ).scalars()
    )
    assert log.usuario_id == escenario.contador1.id
    assert log.entidad_id == escenario.tarea.id
    assert log.accion == "ESTATUS"
    assert log.detalle["estado_anterior"] == ESTADO_POR_HACER
    assert log.detalle["estado_nuevo"] == ESTADO_EN_PROGRESO
    assert log.detalle["completada_en"] is None


def test_completion_audit_includes_the_closing_date(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO)

    (log,) = list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == "tarea")
        ).scalars()
    )
    assert log.detalle["estado_nuevo"] == ESTADO_COMPLETADO
    completada_en = _recargar(escenario.tarea.id).completada_en
    assert log.detalle["completada_en"].startswith(completada_en.isoformat())


# ---------------------------------------------------------------------------
# Notificación de cambio de estado (HU_67)
# ---------------------------------------------------------------------------
def test_creator_receives_the_state_change_notification(
    client, auth_headers, escenario
):
    res = _patch(
        client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO
    )

    assert res.status_code == 200
    (notificacion,) = _notificaciones()
    assert notificacion.usuario_id == escenario.admin.id
    assert notificacion.tipo == TIPO_CAMBIO_ESTADO
    assert notificacion.entidad_tipo == "TAREA"
    assert notificacion.entidad_id == escenario.tarea.id
    assert "Por hacer" in notificacion.mensaje
    assert "En progreso" in notificacion.mensaje
    assert "Ana Contadora" in notificacion.mensaje


def test_no_notification_when_the_creator_moves_the_task(
    client, auth_headers, escenario
):
    res = _patch(
        client, auth_headers(escenario.admin), escenario.tarea, ESTADO_EN_PROGRESO
    )

    assert res.status_code == 200
    assert _notificaciones() == []


# ---------------------------------------------------------------------------
# Mover no concede edición ni eliminación (HU_43)
# ---------------------------------------------------------------------------
def test_moving_does_not_grant_edit_permission(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO)

    res = client.put(
        f"{URL}/{escenario.tarea.id}",
        json={"titulo": "Intento de edición"},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_TAREA_DE_ADMINISTRACION


def test_moving_does_not_grant_delete_permission(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO)

    res = client.delete(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.contador1)
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN
    assert _recargar(escenario.tarea.id).deleted_at is None


# ---------------------------------------------------------------------------
# Aviso al cliente (HU_70)
# ---------------------------------------------------------------------------
def test_completion_sends_the_client_email_once(client, auth_headers, escenario):
    with mail.record_messages() as outbox:
        res = _patch(
            client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_COMPLETADO
        )

    assert res.status_code == 200
    assert len(outbox) == 1
    assert outbox[0].recipients == ["principal@cliente.com"]
    assert escenario.tarea.titulo in outbox[0].subject
    assert "concluyó" in outbox[0].body
    assert _recargar(escenario.tarea.id).cliente_notificado is True


def test_email_falls_back_to_the_client_address(client, auth_headers, escenario):
    escenario.contacto.deleted_at = utcnow()
    db.session.commit()

    with mail.record_messages() as outbox:
        _patch(
            client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO
        )

    assert len(outbox) == 1
    assert outbox[0].recipients == [escenario.cliente.correo]


def test_no_email_when_the_client_is_not_to_be_notified(
    client, auth_headers, escenario
):
    escenario.tarea.notificar_cliente = False
    db.session.commit()

    with mail.record_messages() as outbox:
        _patch(
            client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO
        )

    assert outbox == []
    assert _recargar(escenario.tarea.id).cliente_notificado is False


def test_email_failure_does_not_mark_the_client_as_notified(
    client, auth_headers, escenario, monkeypatch
):
    monkeypatch.setattr(
        email_service, "send_task_completed_email", lambda *args, **kwargs: False
    )

    with mail.record_messages() as outbox:
        res = _patch(
            client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO
        )

    assert res.status_code == 200
    assert outbox == []
    assert _recargar(escenario.tarea.id).cliente_notificado is False
    assert _recargar(escenario.tarea.id).estado == ESTADO_COMPLETADO


def test_email_is_not_repeated_after_reopening_and_completing_again(
    client, auth_headers, escenario
):
    with mail.record_messages() as outbox:
        _patch(client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO)
        _patch(client, auth_headers(escenario.admin), escenario.tarea, ESTADO_EN_PROGRESO)
        _patch(client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO)

    assert len(outbox) == 1
    assert _recargar(escenario.tarea.id).cliente_notificado is True


def test_completing_an_already_completed_task_sends_nothing(
    client, auth_headers, escenario
):
    escenario.tarea.estado = ESTADO_COMPLETADO
    escenario.tarea.completada_en = utcnow() - timedelta(days=1)
    escenario.tarea.completada_por = escenario.admin.id
    db.session.commit()

    with mail.record_messages() as outbox:
        res = _patch(
            client, auth_headers(escenario.admin), escenario.tarea, ESTADO_COMPLETADO
        )

    assert res.status_code == 200
    assert outbox == []
    assert _recargar(escenario.tarea.id).cliente_notificado is False


# ---------------------------------------------------------------------------
# Tablero (HU_41/HU_43)
# ---------------------------------------------------------------------------
def test_the_board_reflects_the_new_column(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_EN_PROGRESO)

    res = client.get(f"{URL}/board", headers=auth_headers(escenario.admin))

    columnas = {columna["estado"]: columna for columna in _data(res)["columnas"]}
    assert escenario.tarea.id in [
        tarjeta["id"] for tarjeta in columnas[ESTADO_EN_PROGRESO]["tareas"]
    ]
    assert escenario.tarea.id not in [
        tarjeta["id"] for tarjeta in columnas[ESTADO_POR_HACER]["tareas"]
    ]


def test_the_board_shows_the_task_in_completed(client, auth_headers, escenario):
    _patch(client, auth_headers(escenario.contador1), escenario.tarea, ESTADO_COMPLETADO)

    res = client.get(f"{URL}/board", headers=auth_headers(escenario.admin))

    columnas = {columna["estado"]: columna for columna in _data(res)["columnas"]}
    completadas = {tarjeta["id"]: tarjeta for tarjeta in columnas[ESTADO_COMPLETADO]["tareas"]}
    assert escenario.tarea.id in completadas
    assert completadas[escenario.tarea.id]["completada_en"] is not None


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
def test_missing_state_returns_422(client, auth_headers, escenario):
    res = client.patch(
        f"{URL}/{escenario.tarea.id}/estado", json={}, headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 422
    assert "estado" in res.get_json()["error"]["fields"]


def test_invalid_state_returns_422(client, auth_headers, escenario):
    res = _patch(client, auth_headers(escenario.admin), escenario.tarea, "ARCHIVADO")

    assert res.status_code == 422
    fields = res.get_json()["error"]["fields"]
    assert fields["estado"] == [
        "Estado no válido. Valores: POR_HACER, EN_PROGRESO, EN_REVISION, COMPLETADO"
    ]


def test_invalid_confirmation_flag_returns_422(client, auth_headers, escenario):
    res = _patch(
        client,
        auth_headers(escenario.admin),
        escenario.tarea,
        ESTADO_COMPLETADO,
        confirmar_subtareas_pendientes="quizá",
    )

    assert res.status_code == 422
    assert "confirmar_subtareas_pendientes" in res.get_json()["error"]["fields"]


def test_body_must_be_a_json_object(client, auth_headers, escenario):
    res = client.patch(
        f"{URL}/{escenario.tarea.id}/estado",
        json=[ESTADO_EN_PROGRESO],
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    assert (
        res.get_json()["error"]["message"]
        == "El cuerpo de la petición debe ser un objeto JSON"
    )
