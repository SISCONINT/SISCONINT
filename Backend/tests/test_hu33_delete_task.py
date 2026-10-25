"""HU_33: Eliminar tarea."""
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import select

from app.core.datetime_utils import today_mx, utcnow
from app.extensions import db
from app.models.audit_log import BitacoraAuditoria
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import Comentario, Subtarea, Tarea
from app.models.time_entry import RegistroTiempo
from app.services.task_service import MSG_TAREA_CON_TIEMPO

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
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Descripción de la tarea a eliminar",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad="ALTA",
        estado="EN_PROGRESO",
        horas_estimadas=4.0,
        notificar_cliente=True,
        cliente_notificado=False,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _crear_subtarea(tarea: Tarea, titulo: str) -> Subtarea:
    subtarea = Subtarea(tarea_id=tarea.id, titulo=titulo, completada=False)
    db.session.add(subtarea)
    db.session.commit()
    return subtarea


def _crear_comentario(tarea: Tarea, autor, texto: str) -> Comentario:
    comentario = Comentario(
        tarea_id=tarea.id, autor_id=autor.id, texto=texto, editado=False
    )
    db.session.add(comentario)
    db.session.commit()
    return comentario


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


def _recargar(tarea_id: int) -> Tarea | None:
    """Relee la tarea desde la BD (la petición usa otra sesión)."""
    db.session.expire_all()
    return db.session.get(Tarea, tarea_id)


def _ids_del_listado(client, auth_headers, usuario) -> list[int]:
    res = client.get(URL, headers=auth_headers(usuario))
    assert res.status_code == 200
    return [tarea["id"] for tarea in res.get_json()["data"]]


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.borra@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.borra@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.borra@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.borra@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.borra@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente = _crear_cliente(contador1, "Cliente Borrable", "XBor010101000")
    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)

    hoy = today_mx()
    tarea = _crear_tarea(
        titulo="Tarea creada por error",
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
    assert client.delete(f"{URL}/{escenario.tarea.id}").status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador"])
def test_management_roles_delete_any_task(client, auth_headers, escenario, actor):
    usuario = getattr(escenario, actor)

    res = client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(usuario))

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["id"] == escenario.tarea.id
    assert data["titulo"] == "Tarea creada por error"
    assert data["mensaje"] == "Tarea eliminada"
    assert datetime.fromisoformat(data["eliminada_en"]) is not None
    assert _recargar(escenario.tarea.id).deleted_at is not None


def test_management_can_delete_a_task_created_by_an_accountant(
    client, auth_headers, escenario
):
    tarea = _crear_tarea(
        titulo="Tarea de la contadora",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    res = client.delete(f"{URL}/{tarea.id}", headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    assert _recargar(tarea.id).deleted_at is not None


def test_accountant_deletes_task_he_created(client, auth_headers, escenario):
    tarea = _crear_tarea(
        titulo="Tarea creada por la contadora",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador2,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    res = client.delete(f"{URL}/{tarea.id}", headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    assert _recargar(tarea.id).deleted_at is not None


@pytest.mark.parametrize("creador", ["admin", "coordinador"])
def test_accountant_cannot_delete_task_created_by_management(
    client, auth_headers, escenario, creador
):
    tarea = _crear_tarea(
        titulo="Tarea de administración",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=getattr(escenario, creador),
        fecha_limite=escenario.hoy + timedelta(days=1),
    )

    res = client.delete(f"{URL}/{tarea.id}", headers=auth_headers(escenario.contador1))

    assert res.status_code == 403
    body = res.get_json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == MSG_FORBIDDEN
    assert "data" not in body
    assert _recargar(tarea.id).deleted_at is None


def test_accountant_cannot_delete_task_outside_his_scope(client, auth_headers, escenario):
    res = client.delete(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.contador2)
    )

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN
    assert _recargar(escenario.tarea.id).deleted_at is None


def test_nonexistent_task_returns_404(client, auth_headers, escenario):
    res = client.delete(f"{URL}/999999", headers=auth_headers(escenario.admin))
    assert res.status_code == 404
    assert res.get_json()["error"]["message"] == "Tarea no encontrada"


def test_already_deleted_task_returns_404(client, auth_headers, escenario):
    client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    res = client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Tiempo registrado
# ---------------------------------------------------------------------------
def test_task_with_registered_time_cannot_be_deleted(client, auth_headers, escenario):
    _crear_tiempo(escenario.tarea, escenario.contador1, 60)
    _crear_tiempo(escenario.tarea, escenario.contador1, 30)

    res = client.delete(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 409
    error = res.get_json()["error"]
    assert error["code"] == "CONFLICT"
    assert error["message"] == MSG_TAREA_CON_TIEMPO
    assert error["registros_tiempo"] == 2
    assert error["minutos_registrados"] == 90
    assert _recargar(escenario.tarea.id).deleted_at is None


def test_deleted_time_entries_do_not_block_deletion(client, auth_headers, escenario):
    registro = _crear_tiempo(escenario.tarea, escenario.contador1, 60)
    registro.deleted_at = utcnow()
    db.session.commit()

    res = client.delete(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 200
    assert _recargar(escenario.tarea.id).deleted_at is not None


# ---------------------------------------------------------------------------
# Eliminación lógica (RG-03) y cascada
# ---------------------------------------------------------------------------
def test_task_is_hidden_from_list_and_detail(client, auth_headers, escenario):
    assert escenario.tarea.id in _ids_del_listado(client, auth_headers, escenario.admin)

    client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    assert escenario.tarea.id not in _ids_del_listado(
        client, auth_headers, escenario.admin
    )
    assert (
        client.get(
            f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
        ).status_code
        == 404
    )


def test_subtasks_and_comments_are_soft_deleted(client, auth_headers, escenario):
    subtarea = _crear_subtarea(escenario.tarea, "Paso uno")
    comentario = _crear_comentario(escenario.tarea, escenario.admin, "Comentario previo")
    actualizada_antes = subtarea.updated_at

    res = client.delete(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 200
    db.session.expire_all()
    subs = db.session.get(Subtarea, subtarea.id)
    comentarios = db.session.get(Comentario, comentario.id)
    assert subs is not None and subs.deleted_at is not None
    assert comentarios is not None and comentarios.deleted_at is not None
    assert subs.updated_by == escenario.admin.id
    assert comentarios.updated_by == escenario.admin.id
    assert subs.updated_at > actualizada_antes


def test_task_history_and_time_entries_are_preserved(client, auth_headers, escenario):
    tiempo = _crear_tiempo(escenario.tarea, escenario.contador1, 60)
    tiempo.deleted_at = utcnow()
    db.session.commit()

    client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    db.session.expire_all()
    assert db.session.get(RegistroTiempo, tiempo.id) is not None
    assert db.session.get(Tarea, escenario.tarea.id).titulo == "Tarea creada por error"


# ---------------------------------------------------------------------------
# Auditoría (RG-13)
# ---------------------------------------------------------------------------
def test_deletion_is_audited(client, auth_headers, escenario):
    _crear_subtarea(escenario.tarea, "Paso uno")
    _crear_comentario(escenario.tarea, escenario.admin, "Comentario previo")

    client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    (log,) = list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == "tarea")
        ).scalars()
    )
    assert log.usuario_id == escenario.admin.id
    assert log.entidad_id == escenario.tarea.id
    assert log.accion == "ELIMINAR"
    assert log.detalle["titulo"] == "Tarea creada por error"
    assert log.detalle["cliente_id"] == escenario.cliente.id
    assert log.detalle["subtareas_ocultas"] == 1
    assert log.detalle["comentarios_ocultos"] == 1


def test_no_audit_when_deletion_is_rejected(client, auth_headers, escenario):
    _crear_tiempo(escenario.tarea, escenario.contador1, 60)

    client.delete(f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin))

    assert db.session.execute(select(BitacoraAuditoria)).first() is None
