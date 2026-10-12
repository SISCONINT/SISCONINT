"""HU_08: Modificar colaborador (datos, rol y grado escalafón)."""
from datetime import date

import pytest
from sqlalchemy import select

from app.core.datetime_utils import utcnow
from app.core.errors import ConflictError
from app.core.security import hash_password
from app.extensions import db
from app.models.audit_log import BitacoraAuditoria
from app.models.time_entry import RegistroTiempo
from app.models.user import Colaborador
from app.services import user_service
from app.services.user_service import MSG_LAST_OWNER_ROLE, MSG_OWN_ROLE

USERS = "/api/v1/users"
ME = "/api/v1/auth/me"
LOGIN = "/api/v1/auth/login"
PASSWORD = "Password1!"

REQUIRED = {
    "nombre_completo", "telefono_despacho", "correo_institucional", "rol",
    "grado_escalafon", "telefono_personal", "emergencia_nombre", "emergencia_telefono",
}


@pytest.fixture()
def owner(make_user):
    return make_user("dueno@despacho.com", "DUENO")


@pytest.fixture()
def admin(make_user):
    return make_user("admin@despacho.com", "ADMINISTRADOR")


@pytest.fixture()
def accountant(make_user):
    return make_user("contador@despacho.com", "CONTADOR")


def _ficha(user: Colaborador, **overrides) -> dict:
    body = {
        "nombre_completo": user.nombre_completo,
        "telefono_despacho": user.telefono_despacho,
        "correo_institucional": user.correo_institucional,
        "rol": user.rol,
        "grado_escalafon": user.grado_escalafon,
        "telefono_personal": user.telefono_personal,
        "emergencia_nombre": user.emergencia_nombre,
        "emergencia_telefono": user.emergencia_telefono,
        "licenciatura": user.licenciatura,
        "cedula": user.cedula,
        "calle": user.calle,
        "no_ext_int": user.no_ext_int,
        "colonia": user.colonia,
        "municipio": user.municipio,
        "estado": user.estado,
    }
    body.update(overrides)
    return body


def _url(user_id: int) -> str:
    return f"{USERS}/{user_id}"


def _with_password(user: Colaborador) -> Colaborador:
    user.password_hash = hash_password(PASSWORD)
    db.session.commit()
    return user


# ---------------------------------------------------------------- GET ficha
def test_get_returns_current_data_for_the_form(client, auth_headers, owner, accountant):
    res = client.get(_url(accountant.id), headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["id"] == accountant.id
    assert data["correo_institucional"] == accountant.correo_institucional
    assert data["rol"] == "CONTADOR"
    assert data["grado_escalafon"] == "ADMIN"
    assert "password_hash" not in data


def test_get_unknown_user_is_404(client, auth_headers, owner):
    res = client.get(_url(999999), headers=auth_headers(owner))
    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"


def test_get_soft_deleted_user_is_404(client, auth_headers, owner, accountant):
    accountant.deleted_at = utcnow()
    db.session.commit()
    assert client.get(_url(accountant.id), headers=auth_headers(owner)).status_code == 404


# ---------------------------------------------------------------- éxito
def test_owner_updates_collaborator_and_ficha_reflects_it(client, auth_headers, owner, accountant):
    payload = _ficha(
        accountant,
        nombre_completo="María Fernanda López Ruiz",
        telefono_despacho="2461234567",
        grado_escalafon="JUNIOR",
        licenciatura="Contaduría Pública",
        cedula="1234567",
    )
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["nombre_completo"] == "María Fernanda López Ruiz"
    assert data["grado_escalafon"] == "JUNIOR"
    assert data["cedula"] == "1234567"
    assert data["rol"] == "CONTADOR"

    ficha = client.get(_url(accountant.id), headers=auth_headers(owner)).get_json()["data"]
    assert ficha["nombre_completo"] == "María Fernanda López Ruiz"
    assert ficha["grado_escalafon"] == "JUNIOR"


def test_same_payload_as_get_is_accepted(client, auth_headers, owner, accountant):
    """El formulario se abre precargado y se puede guardar sin cambios."""
    data = client.get(_url(accountant.id), headers=auth_headers(owner)).get_json()["data"]
    payload = {k: data[k] for k in REQUIRED}
    for key in ("licenciatura", "cedula", "calle", "no_ext_int", "colonia", "municipio", "estado"):
        payload[key] = data.get(key)
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 200


def test_update_is_audited(client, auth_headers, owner, accountant):
    client.put(_url(accountant.id), json=_ficha(accountant, nombre_completo="Nuevo Nombre"), headers=auth_headers(owner))
    entry = db.session.execute(
        select(BitacoraAuditoria).where(BitacoraAuditoria.accion == "MODIFICAR")
    ).scalar_one()
    assert (entry.usuario_id, entry.entidad, entry.entidad_id) == (owner.id, "colaborador", accountant.id)
    assert entry.detalle["nombre_completo"]["antes"] == "Usuario Contador"
    assert entry.detalle["nombre_completo"]["despues"] == "Nuevo Nombre"


def test_empty_optional_strings_become_null_and_enums_are_case_insensitive(
    client, auth_headers, owner, accountant
):
    payload = _ficha(accountant, cedula="", licenciatura="  ", rol="coordinador", grado_escalafon="senior")
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["cedula"] is None and data["licenciatura"] is None
    assert data["rol"] == "COORDINADOR" and data["grado_escalafon"] == "SENIOR"


# ---------------------------------------------------------------- quién edita a quién
def test_admin_can_edit_coordinator_or_accountant(client, auth_headers, admin, make_user):
    coord = make_user("coord@despacho.com", "COORDINADOR")
    payload = _ficha(coord, nombre_completo="Coordinador Editado")
    assert client.put(_url(coord.id), json=payload, headers=auth_headers(admin)).status_code == 200


@pytest.mark.parametrize("rol", ["DUENO", "ADMINISTRADOR"])
def test_admin_cannot_edit_owner_or_admin(client, auth_headers, admin, make_user, rol):
    target = make_user(f"{rol.lower()}@despacho.com", rol)
    original = target.nombre_completo
    res = client.put(_url(target.id), json=_ficha(target, nombre_completo="Hack"), headers=auth_headers(admin))
    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == "No tienes permiso para esta acción"
    assert db.session.get(Colaborador, target.id).nombre_completo == original


@pytest.mark.parametrize("rol", ["DUENO", "ADMINISTRADOR"])
def test_admin_cannot_assign_owner_or_admin(client, auth_headers, admin, accountant, rol):
    res = client.put(_url(accountant.id), json=_ficha(accountant, rol=rol), headers=auth_headers(admin))
    assert res.status_code == 403
    assert db.session.get(Colaborador, accountant.id).rol == "CONTADOR"


def test_nobody_can_change_own_role(client, auth_headers, owner):
    res = client.put(_url(owner.id), json=_ficha(owner, rol="ADMINISTRADOR"), headers=auth_headers(owner))
    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_OWN_ROLE
    assert db.session.get(Colaborador, owner.id).rol == "DUENO"


def test_owner_can_edit_own_data_keeping_role(client, auth_headers, owner):
    res = client.put(
        _url(owner.id),
        json=_ficha(owner, nombre_completo="Dueño Actualizado", telefono_personal="4429999999"),
        headers=auth_headers(owner),
    )
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["nombre_completo"] == "Dueño Actualizado"
    assert data["rol"] == "DUENO"


def test_second_owner_can_change_another_owners_role(client, auth_headers, owner, make_user):
    other = make_user("otro.dueno@despacho.com", "DUENO")
    res = client.put(_url(other.id), json=_ficha(other, rol="COORDINADOR"), headers=auth_headers(owner))
    assert res.status_code == 200
    assert db.session.get(Colaborador, other.id).rol == "COORDINADOR"


def test_last_active_owner_role_cannot_be_changed(app, make_user):
    """Un Dueño inactivo no cuenta: queda un solo Dueño activo y su rol no se mueve."""
    last = make_user("ultimo@despacho.com", "DUENO")
    ghost = make_user("inactivo@despacho.com", "DUENO")
    ghost.estatus = "INACTIVO"
    db.session.commit()

    with pytest.raises(ConflictError) as exc:
        user_service.update_user(ghost, last.id, _ficha(last, rol="CONTADOR"))
    assert MSG_LAST_OWNER_ROLE in str(exc.value)
    assert db.session.get(Colaborador, last.id).rol == "DUENO"


@pytest.mark.parametrize("rol", ["COORDINADOR", "CONTADOR"])
def test_coordinator_and_accountant_are_denied(client, auth_headers, make_user, accountant, rol):
    actor = make_user(f"actor.{rol.lower()}@despacho.com", rol)
    res = client.put(_url(accountant.id), json=_ficha(accountant), headers=auth_headers(actor))
    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == "No tienes permiso para esta acción"
    assert "fields" not in res.get_json()["error"]


def test_requires_authentication(client, accountant):
    assert client.put(_url(accountant.id), json=_ficha(accountant)).status_code == 401
    assert client.get(_url(accountant.id)).status_code == 401


# ---------------------------------------------------------------- validaciones (mismas del alta)
def test_all_required_fields_are_reported(client, auth_headers, owner, accountant):
    res = client.put(_url(accountant.id), json={}, headers=auth_headers(owner))
    assert res.status_code == 422
    fields = res.get_json()["error"]["fields"]
    assert set(fields) == REQUIRED
    assert all(msgs == ["Campo obligatorio"] for msgs in fields.values())


@pytest.mark.parametrize("field", sorted(REQUIRED))
def test_each_required_field_rejects_blank(client, auth_headers, owner, accountant, field):
    payload = _ficha(accountant)
    payload[field] = "   "
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 422
    assert res.get_json()["error"]["fields"][field] == ["Campo obligatorio"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("correo_institucional", "no-es-correo"),
        ("telefono_despacho", "123456789"),
        ("cedula", "12A4567"),
        ("rol", "SUPERUSUARIO"),
        ("grado_escalafon", "MASTER"),
    ],
)
def test_invalid_formats_are_rejected(client, auth_headers, owner, accountant, field, value):
    payload = _ficha(accountant)
    payload[field] = value
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 422
    assert field in res.get_json()["error"]["fields"]
    assert db.session.get(Colaborador, accountant.id).nombre_completo == accountant.nombre_completo


def test_duplicate_email_is_rejected(client, auth_headers, owner, accountant):
    payload = _ficha(accountant, correo_institucional=owner.correo_institucional)
    res = client.put(_url(accountant.id), json=payload, headers=auth_headers(owner))
    assert res.status_code == 409
    err = res.get_json()["error"]
    assert err["fields"]["correo_institucional"] == ["El correo ya está registrado"]
    assert db.session.get(Colaborador, accountant.id).correo_institucional == "contador@despacho.com"


def test_keeping_own_email_is_allowed(client, auth_headers, owner, accountant):
    res = client.put(_url(accountant.id), json=_ficha(accountant, nombre_completo="Mismo correo"), headers=auth_headers(owner))
    assert res.status_code == 200


def test_body_must_be_a_json_object(client, auth_headers, owner, accountant):
    res = client.put(_url(accountant.id), data="no es json", headers=auth_headers(owner))
    assert res.status_code == 422


def test_put_unknown_user_is_404(client, auth_headers, owner, valid_payload):
    assert client.put(_url(999999), json=valid_payload, headers=auth_headers(owner)).status_code == 404


# ---------------------------------------------------------------- sesión al cambiar rol
def test_role_change_closes_current_session_and_applies_on_next_login(
    client, auth_headers, owner, make_user
):
    target = _with_password(make_user("cambio.rol@despacho.com", "CONTADOR"))
    target_headers = auth_headers(target)
    owner_headers = auth_headers(owner)

    assert client.get(ME, headers=target_headers).status_code == 200
    assert client.get(ME, headers=owner_headers).status_code == 200

    res = client.put(_url(target.id), json=_ficha(target, rol="COORDINADOR"), headers=owner_headers)
    assert res.status_code == 200
    assert res.get_json()["data"]["rol"] == "COORDINADOR"

    blocked = client.get(ME, headers=target_headers)
    assert blocked.status_code == 401
    assert blocked.get_json()["error"]["code"] == "UNAUTHORIZED"
    # quien hizo el cambio sigue en sesión
    assert client.get(ME, headers=owner_headers).status_code == 200

    login = client.post(LOGIN, json={"correo_institucional": target.correo_institucional, "password": PASSWORD})
    assert login.status_code == 200
    assert login.get_json()["data"]["rol"] == "COORDINADOR"


def test_grade_change_does_not_close_session(client, auth_headers, owner, accountant):
    headers = auth_headers(accountant)
    client.put(_url(accountant.id), json=_ficha(accountant, grado_escalafon="JUNIOR"), headers=auth_headers(owner))
    assert client.get(ME, headers=headers).status_code == 200


# ---------------------------------------------------------------- grado no reescribe histórico
def test_grade_change_does_not_rewrite_past_time_entries(client, auth_headers, owner, accountant):
    past = RegistroTiempo(colaborador_id=accountant.id, grado_escalafon=accountant.grado_escalafon, fecha=date.today())
    db.session.add(past)
    db.session.commit()
    past_id = past.id
    old_grade = past.grado_escalafon

    res = client.put(_url(accountant.id), json=_ficha(accountant, grado_escalafon="JUNIOR"), headers=auth_headers(owner))
    assert res.status_code == 200
    assert res.get_json()["data"]["grado_escalafon"] == "JUNIOR"
    assert db.session.get(Colaborador, accountant.id).grado_escalafon == "JUNIOR"
    assert db.session.get(RegistroTiempo, past_id).grado_escalafon == old_grade == "ADMIN"
