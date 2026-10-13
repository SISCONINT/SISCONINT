"""HU_09: Desactivar colaborador (sin eliminarlo, con reasignación de clientes y tareas)."""
from datetime import date, time

import pytest
from sqlalchemy import select

from app.core.datetime_utils import utcnow
from app.core.errors import ConflictError
from app.core.security import hash_password, user_generation
from app.extensions import db
from app.models.audit_log import BitacoraAuditoria
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.notification import Notificacion
from app.models.task import Tarea
from app.models.time_entry import RegistroTiempo
from app.models.user import Colaborador
from app.services import user_service
from app.services.user_service import (
    MSG_ALREADY_INACTIVE,
    MSG_LAST_OWNER_DEACTIVATE,
    MSG_OWN_DEACTIVATE,
)

USERS = "/api/v1/users"
ME = "/api/v1/auth/me"
LOGIN = "/api/v1/auth/login"
PASSWORD = "Password1!"


@pytest.fixture()
def owner(make_user):
    return make_user("dueno@despacho.com", "DUENO")


@pytest.fixture()
def admin(make_user):
    return make_user("admin@despacho.com", "ADMINISTRADOR")


@pytest.fixture()
def coordinator(make_user):
    return make_user("coordinador@despacho.com", "COORDINADOR")


@pytest.fixture()
def accountant(make_user):
    """El colaborador que se desactiva en la mayoría de las pruebas."""
    return make_user("contador@despacho.com", "CONTADOR", nombre="Carlos Contador")


@pytest.fixture()
def successor(make_user):
    return make_user("sucesor@despacho.com", "CONTADOR", nombre="Sara Sucesora")


@pytest.fixture()
def categoria(app):
    cat = CategoriaProyecto(nombre="Impuestos", activa=True, orden=1)
    db.session.add(cat)
    db.session.commit()
    return cat


_rfc_seq = iter(range(1, 10_000))


def _cliente(contador: Colaborador, estatus: str = "ACTIVO", deleted: bool = False) -> Cliente:
    n = next(_rfc_seq)
    cliente = Cliente(
        nombre_completo=f"Cliente {n}", rfc=f"AAA{n:06d}XX1", tipo_persona="MORAL", razon_social=f"Cliente {n} SA",
        forma_pago="TRANSFERENCIA", contador_asignado_id=contador.id, giro="Comercio", telefono="4421234567",
        correo=f"c{n}@cliente.com", codigo_postal="76000", calle="Calle", no_exterior="1", colonia="Centro",
        ciudad="Querétaro", estado="Querétaro", tiene_trabajadores=False, estatus=estatus,
        deleted_at=utcnow() if deleted else None,
    )
    db.session.add(cliente)
    db.session.commit()
    return cliente


def _tarea(asignado: Colaborador, cliente: Cliente, categoria, estado: str = "POR_HACER", creador=None) -> Tarea:
    tarea = Tarea(
        titulo="Declaración mensual", cliente_id=cliente.id, categoria_id=categoria.id, asignado_id=asignado.id,
        creador_id=(creador or asignado).id, fecha_limite=date(2026, 12, 17), hora_limite=time(23, 59),
        prioridad="MEDIA", estado=estado,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _url(user_id: int) -> str:
    return f"{USERS}/{user_id}/deactivate"


def _impact_url(user_id: int) -> str:
    return f"{USERS}/{user_id}/deactivation-impact"


def _refresh(*records):
    for record in records:
        db.session.refresh(record)


def _audit(entidad: str, accion: str):
    return list(
        db.session.execute(
            select(BitacoraAuditoria).where(BitacoraAuditoria.entidad == entidad, BitacoraAuditoria.accion == accion)
        ).scalars()
    )


# ---------------------------------------------------------------- sin pendientes
def test_owner_deactivates_collaborator_without_pending_work(client, auth_headers, owner, accountant):
    res = client.post(_url(accountant.id), headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["estatus"] == "INACTIVO"
    assert data["reasignacion"] == {"reasignado_a": None, "clientes": 0, "tareas": 0}
    assert "password_hash" not in data

    _refresh(accountant)
    assert accountant.estatus == "INACTIVO"
    assert accountant.deleted_at is None  # RG-03: no se elimina físicamente
    assert db.session.get(Colaborador, accountant.id) is not None


def test_admin_can_deactivate_accountant_and_coordinator(client, auth_headers, admin, accountant, coordinator):
    assert client.post(_url(accountant.id), headers=auth_headers(admin)).status_code == 200
    assert client.post(_url(coordinator.id), headers=auth_headers(admin)).status_code == 200


def test_deactivated_user_still_listed_and_viewable(client, auth_headers, owner, accountant):
    client.post(_url(accountant.id), headers=auth_headers(owner))

    listed = client.get(f"{USERS}?estatus=INACTIVO", headers=auth_headers(owner)).get_json()["data"]
    assert [u["id"] for u in listed] == [accountant.id]
    assert client.get(f"{USERS}/{accountant.id}", headers=auth_headers(owner)).status_code == 200


def test_deactivation_is_audited(client, auth_headers, owner, accountant):
    client.post(_url(accountant.id), headers=auth_headers(owner))
    (entry,) = _audit("colaborador", "ESTATUS")
    assert (entry.usuario_id, entry.entidad_id) == (owner.id, accountant.id)
    assert entry.detalle["estatus"] == {"antes": "ACTIVO", "despues": "INACTIVO"}
    assert entry.detalle["reasignado_a"] is None


# ---------------------------------------------------------------- reasignación obligatoria
def test_pending_work_requires_a_target_and_nothing_changes(client, auth_headers, owner, accountant, categoria):
    cliente = _cliente(accountant)
    _cliente(accountant, "PAUSADO")
    _tarea(accountant, cliente, categoria, "EN_PROGRESO")

    res = client.post(_url(accountant.id), headers=auth_headers(owner))
    assert res.status_code == 422
    error = res.get_json()["error"]
    assert error["code"] == "REASSIGNMENT_REQUIRED"
    assert "reasignar_a" in error["fields"]
    assert (error["clientes_asignados"], error["tareas_abiertas"]) == (2, 1)

    _refresh(accountant, cliente)
    assert accountant.estatus == "ACTIVO"
    assert cliente.contador_asignado_id == accountant.id
    assert _audit("colaborador", "ESTATUS") == []


def test_only_tasks_pending_also_requires_target(client, auth_headers, owner, accountant, successor, categoria):
    other_client = _cliente(successor)
    _tarea(accountant, other_client, categoria, "EN_REVISION")  # sin clientes propios, solo una tarea
    res = client.post(_url(accountant.id), headers=auth_headers(owner))
    assert res.status_code == 422
    assert res.get_json()["error"]["tareas_abiertas"] == 1


def test_impact_reports_counts_and_candidates(client, auth_headers, owner, admin, coordinator, accountant, successor, make_user, categoria):
    make_user("inactivo@despacho.com", "CONTADOR", estatus="INACTIVO")
    c1 = _cliente(accountant)
    _cliente(accountant, "PAUSADO")
    _cliente(accountant, "BAJA")  # ya no se atiende: no cuenta
    _cliente(accountant, deleted=True)  # eliminado: no cuenta
    for estado in ("POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"):
        _tarea(accountant, c1, categoria, estado)

    res = client.get(_impact_url(accountant.id), headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["clientes_asignados"] == 2
    assert data["tareas_abiertas"] == 3  # la completada no cuenta
    assert data["requiere_reasignacion"] is True
    # Solo Contadores/Coordinadores Activos, sin el propio colaborador, Dueño, Administrador ni Inactivos.
    assert {d["id"] for d in data["destinos"]} == {coordinator.id, successor.id}
    assert set(data["destinos"][0]) == {"id", "nombre_completo", "rol"}


def test_impact_without_pending_does_not_require_reassignment(client, auth_headers, owner, accountant):
    data = client.get(_impact_url(accountant.id), headers=auth_headers(owner)).get_json()["data"]
    assert (data["clientes_asignados"], data["tareas_abiertas"], data["requiere_reasignacion"]) == (0, 0, False)


# ---------------------------------------------------------------- reasignación
def test_reassigns_clients_and_open_tasks_and_notifies_target(
    client, auth_headers, owner, accountant, successor, coordinator, categoria
):
    active, paused, closed = _cliente(accountant), _cliente(accountant, "PAUSADO"), _cliente(accountant, "BAJA")
    open_tasks = [_tarea(accountant, active, categoria, e, creador=coordinator) for e in ("POR_HACER", "EN_PROGRESO", "EN_REVISION")]
    done = _tarea(accountant, active, categoria, "COMPLETADO", creador=coordinator)

    res = client.post(_url(accountant.id), json={"reasignar_a": successor.id}, headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["estatus"] == "INACTIVO"
    assert data["reasignacion"] == {
        "reasignado_a": {"id": successor.id, "nombre_completo": "Sara Sucesora", "rol": "CONTADOR"},
        "clientes": 2,
        "tareas": 3,
    }

    _refresh(active, paused, closed, done, *open_tasks)
    assert active.contador_asignado_id == paused.contador_asignado_id == successor.id
    assert closed.contador_asignado_id == accountant.id  # Baja: conserva su historial
    assert all(t.asignado_id == successor.id for t in open_tasks)
    assert all(t.creador_id == coordinator.id for t in open_tasks)  # quién la creó no cambia
    assert done.asignado_id == accountant.id  # completada: sigue atribuida a él


def test_notifies_only_the_target(client, auth_headers, owner, accountant, successor, coordinator, categoria):
    cliente = _cliente(accountant)
    _tarea(accountant, cliente, categoria)
    _tarea(accountant, cliente, categoria)

    client.post(_url(accountant.id), json={"reasignar_a": successor.id}, headers=auth_headers(owner))

    (note,) = db.session.execute(select(Notificacion)).scalars()
    assert note.usuario_id == successor.id
    assert note.tipo == "REASIGNACION"
    assert note.leida is False
    assert "1 cliente y 2 tareas" in note.mensaje
    assert "Carlos Contador" in note.mensaje


def test_coordinator_is_a_valid_target(client, auth_headers, owner, accountant, coordinator):
    cliente = _cliente(accountant)
    res = client.post(_url(accountant.id), json={"reasignar_a": coordinator.id}, headers=auth_headers(owner))
    assert res.status_code == 200
    _refresh(cliente)
    assert cliente.contador_asignado_id == coordinator.id


def test_reassignment_is_audited_per_record(client, auth_headers, owner, accountant, successor, categoria):
    cliente = _cliente(accountant)
    tarea = _tarea(accountant, cliente, categoria)

    client.post(_url(accountant.id), json={"reasignar_a": successor.id}, headers=auth_headers(owner))

    (c_entry,) = _audit("cliente", "MODIFICAR")
    assert c_entry.entidad_id == cliente.id
    assert c_entry.detalle["contador_asignado_id"] == {"antes": accountant.id, "despues": successor.id}
    (t_entry,) = _audit("tarea", "MODIFICAR")
    assert t_entry.entidad_id == tarea.id
    assert t_entry.detalle["asignado_id"] == {"antes": accountant.id, "despues": successor.id}
    (u_entry,) = _audit("colaborador", "ESTATUS")
    assert (u_entry.detalle["reasignado_a"], u_entry.detalle["clientes_reasignados"], u_entry.detalle["tareas_reasignadas"]) == (
        successor.id, 1, 1,
    )


def test_target_without_pending_work_is_accepted_but_nobody_is_notified(client, auth_headers, owner, accountant, successor):
    res = client.post(_url(accountant.id), json={"reasignar_a": successor.id}, headers=auth_headers(owner))
    assert res.status_code == 200
    assert res.get_json()["data"]["reasignacion"] == {"reasignado_a": None, "clientes": 0, "tareas": 0}
    assert db.session.execute(select(Notificacion)).first() is None


def test_history_stays_attributed_to_the_deactivated_user(client, auth_headers, owner, accountant, successor, categoria):
    cliente = _cliente(accountant)
    done = _tarea(accountant, cliente, categoria, "COMPLETADO")
    entry = RegistroTiempo(
        tarea_id=done.id, colaborador_id=accountant.id, fecha=date(2026, 10, 1), duracion_minutos=90, tipo="MANUAL",
        descripcion="Revisión", nivel_escalafon="SENIOR",
    )
    db.session.add(entry)
    db.session.commit()

    client.post(_url(accountant.id), json={"reasignar_a": successor.id}, headers=auth_headers(owner))

    _refresh(done, entry)
    assert done.asignado_id == accountant.id
    assert entry.colaborador_id == accountant.id
    assert entry.deleted_at is None


# ---------------------------------------------------------------- destino inválido
@pytest.mark.parametrize("kind", ["admin", "owner", "inactive", "self", "missing", "deleted"])
def test_invalid_target_is_rejected_and_nothing_changes(
    client, auth_headers, owner, admin, accountant, make_user, categoria, kind
):
    cliente = _cliente(accountant)
    inactive = make_user("baja@despacho.com", "CONTADOR", estatus="INACTIVO")
    deleted = make_user("borrado@despacho.com", "CONTADOR")
    deleted.deleted_at = utcnow()
    db.session.commit()
    target_id = {
        "admin": admin.id, "owner": owner.id, "inactive": inactive.id, "self": accountant.id,
        "missing": 999999, "deleted": deleted.id,
    }[kind]

    res = client.post(_url(accountant.id), json={"reasignar_a": target_id}, headers=auth_headers(owner))
    assert res.status_code == 422
    assert "reasignar_a" in res.get_json()["error"]["fields"]

    _refresh(accountant, cliente)
    assert accountant.estatus == "ACTIVO"
    assert cliente.contador_asignado_id == accountant.id


@pytest.mark.parametrize("value", ["5", True, 0, -3, 1.5, [1]])
def test_malformed_target_is_rejected(client, auth_headers, owner, accountant, value):
    res = client.post(_url(accountant.id), json={"reasignar_a": value}, headers=auth_headers(owner))
    assert res.status_code == 422
    assert "reasignar_a" in res.get_json()["error"]["fields"]


def test_non_object_body_is_rejected(client, auth_headers, owner, accountant):
    assert client.post(_url(accountant.id), json=[1, 2], headers=auth_headers(owner)).status_code == 422


# ---------------------------------------------------------------- reglas de protección
def test_cannot_deactivate_yourself(client, auth_headers, owner, make_user):
    make_user("otro.dueno@despacho.com", "DUENO")  # no es "último Dueño": es uno mismo
    res = client.post(_url(owner.id), headers=auth_headers(owner))
    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_OWN_DEACTIVATE
    _refresh(owner)
    assert owner.estatus == "ACTIVO"


def test_owner_can_deactivate_another_owner_while_one_remains(client, auth_headers, owner, make_user):
    other = make_user("otro.dueno@despacho.com", "DUENO")
    assert client.post(_url(other.id), headers=auth_headers(owner)).status_code == 200


def test_cannot_deactivate_the_last_active_owner(app, owner, make_user):
    """Un Dueño nunca puede quedar sin otro Dueño activo, aunque quien actúa llegue con una sesión desfasada."""
    stale_actor = make_user("dueno.viejo@despacho.com", "DUENO")
    stale_actor.estatus = "INACTIVO"
    db.session.commit()

    with pytest.raises(ConflictError) as exc:
        user_service.deactivate_user(stale_actor, owner.id)
    assert exc.value.status == 409
    assert exc.value.message == MSG_LAST_OWNER_DEACTIVATE
    _refresh(owner)
    assert owner.estatus == "ACTIVO"


@pytest.mark.parametrize("rol", ["DUENO", "ADMINISTRADOR"])
def test_admin_cannot_deactivate_owner_or_admin(client, auth_headers, admin, make_user, rol):
    target = make_user("protegido@despacho.com", rol)
    assert client.post(_url(target.id), headers=auth_headers(admin)).status_code == 403
    _refresh(target)
    assert target.estatus == "ACTIVO"


@pytest.mark.parametrize("rol", ["COORDINADOR", "CONTADOR"])
def test_coordinator_and_accountant_are_denied(client, auth_headers, make_user, accountant, rol):
    actor = make_user(f"{rol.lower()}.actor@despacho.com", rol)
    assert client.post(_url(accountant.id), headers=auth_headers(actor)).status_code == 403
    assert client.get(_impact_url(accountant.id), headers=auth_headers(actor)).status_code == 403
    _refresh(accountant)
    assert accountant.estatus == "ACTIVO"


def test_requires_authentication(client, accountant):
    assert client.post(_url(accountant.id)).status_code == 401


def test_already_inactive_is_a_conflict(client, auth_headers, owner, make_user):
    inactive = make_user("baja@despacho.com", "CONTADOR", estatus="INACTIVO")
    res = client.post(_url(inactive.id), headers=auth_headers(owner))
    assert res.status_code == 409
    assert res.get_json()["error"]["message"] == MSG_ALREADY_INACTIVE


def test_unknown_or_deleted_user_is_404(client, auth_headers, owner, accountant):
    assert client.post(_url(999999), headers=auth_headers(owner)).status_code == 404
    accountant.deleted_at = utcnow()
    db.session.commit()
    assert client.post(_url(accountant.id), headers=auth_headers(owner)).status_code == 404


# ---------------------------------------------------------------- sesiones
def test_sessions_are_closed_immediately(app, client, auth_headers, owner, accountant):
    accountant.password_hash = hash_password(PASSWORD)
    db.session.commit()

    session = app.test_client()  # sesión del colaborador, con sus cookies
    assert session.post(LOGIN, json={"correo_institucional": accountant.correo_institucional, "password": PASSWORD}).status_code == 200
    assert session.get(ME).status_code == 200

    assert client.post(_url(accountant.id), headers=auth_headers(owner)).status_code == 200

    assert session.get(ME).status_code == 401  # la sesión que ya tenía abierta deja de servir
    assert user_generation(accountant.id) == 1  # y cualquier token previo queda revocado
    res = session.post(LOGIN, json={"correo_institucional": accountant.correo_institucional, "password": PASSWORD})
    assert res.status_code == 403
    assert res.get_json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_failed_deactivation_does_not_close_sessions(client, auth_headers, owner, accountant, categoria):
    _tarea(accountant, _cliente(accountant), categoria)
    client.post(_url(accountant.id), headers=auth_headers(owner))  # 422: falta el destino
    assert user_generation(accountant.id) == 0
    assert client.get(ME, headers=auth_headers(accountant)).status_code == 200
