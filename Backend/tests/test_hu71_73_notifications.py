"""HU_71-73: bandeja de notificaciones, marcar una y marcar todas como leídas."""
from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import utcnow
from app.extensions import db
from app.models.notification import Notificacion

URL = "/api/v1/notifications"


# ---------------------------------------------------------------------------
# Datos de apoyo
# ---------------------------------------------------------------------------
def _crear_notificacion(
    usuario,
    *,
    titulo: str = "Aviso",
    mensaje: str = "Mensaje de la notificación",
    tipo: str = "ASIGNACION",
    entidad_tipo: str | None = "TAREA",
    entidad_id: int | None = 1,
    leida: bool = False,
    created_at=None,
    clave_unica: str | None = None,
) -> Notificacion:
    notificacion = Notificacion(
        usuario_id=usuario.id,
        tipo=tipo,
        titulo=titulo,
        mensaje=mensaje,
        entidad_tipo=entidad_tipo,
        entidad_id=entidad_id,
        leida=leida,
        clave_unica=clave_unica,
        created_at=created_at or utcnow(),
    )
    db.session.add(notificacion)
    db.session.commit()
    return notificacion


def _ids(res) -> list[int]:
    return [item["id"] for item in res.get_json()["data"]]


def _meta(res) -> dict:
    return res.get_json()["meta"]


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.bandeja@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.bandeja@despacho.com", "ADMINISTRADOR", nombre="Admin Bandeja")
    coordinador = make_user(
        "carla.bandeja@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user("ana.bandeja@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.bandeja@despacho.com", "CONTADOR", nombre="Beto Contador")

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
    )


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("rol", ["dueno", "admin", "coordinador", "contador1"])
def test_all_roles_can_open_their_own_inbox(client, auth_headers, escenario, rol):
    res = client.get(URL, headers=auth_headers(getattr(escenario, rol)))

    assert res.status_code == 200
    assert res.get_json()["data"] == []
    assert _meta(res) == {"page": 1, "per_page": 20, "total": 0, "pages": 0, "no_leidas": 0}


def test_only_shows_own_notifications(client, auth_headers, escenario):
    propia = _crear_notificacion(escenario.contador1, titulo="Para Ana")
    _crear_notificacion(escenario.contador2, titulo="Para Beto")

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    assert _ids(res) == [propia.id]
    assert res.get_json()["data"][0]["titulo"] == "Para Ana"
    assert _meta(res)["total"] == 1


# ---------------------------------------------------------------------------
# Orden, contador y filtros (HU_71)
# ---------------------------------------------------------------------------
def test_notifications_are_newest_first(client, auth_headers, escenario):
    ahora = utcnow()
    vieja = _crear_notificacion(
        escenario.contador1, titulo="Vieja", created_at=ahora - timedelta(hours=2)
    )
    media = _crear_notificacion(
        escenario.contador1, titulo="Media", created_at=ahora - timedelta(hours=1)
    )
    nueva = _crear_notificacion(escenario.contador1, titulo="Nueva", created_at=ahora)

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert _ids(res) == [nueva.id, media.id, vieja.id]


def test_unread_counter_is_in_meta(client, auth_headers, escenario):
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1, leida=True)
    _crear_notificacion(escenario.contador2)

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert _meta(res)["no_leidas"] == 2


@pytest.mark.parametrize(
    ("valor", "leida"),
    [
        ("true", True),
        ("false", False),
        ("1", True),
        ("0", False),
        ("leida", True),
        ("leidas", True),
        ("no_leida", False),
        ("no_leidas", False),
    ],
)
def test_filter_by_read_status(client, auth_headers, escenario, valor, leida):
    pendiente = _crear_notificacion(escenario.contador1, titulo="Pendiente", leida=False)
    revisada = _crear_notificacion(escenario.contador1, titulo="Revisada", leida=True)

    res = client.get(
        URL, query_string={"leida": valor}, headers=auth_headers(escenario.contador1)
    )

    assert res.status_code == 200
    assert _ids(res) == [(revisada if leida else pendiente).id]
    assert _meta(res)["total"] == 1


def test_filter_does_not_change_the_unread_counter(client, auth_headers, escenario):
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1, leida=True)

    leidas = client.get(
        URL, query_string={"leida": "true"}, headers=auth_headers(escenario.contador1)
    )

    assert _meta(leidas)["no_leidas"] == 2


def test_empty_query_params_are_ignored(client, auth_headers, escenario):
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1, leida=True)

    res = client.get(
        URL,
        query_string={"leida": "", "page": ""},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 200
    assert _meta(res)["total"] == 2


# ---------------------------------------------------------------------------
# Retención de 90 días (HU_71)
# ---------------------------------------------------------------------------
def test_notifications_older_than_90_days_are_hidden(client, auth_headers, escenario):
    ahora = utcnow()
    reciente = _crear_notificacion(
        escenario.contador1, titulo="Reciente", created_at=ahora - timedelta(days=89)
    )
    _crear_notificacion(
        escenario.contador1, titulo="Expirada", created_at=ahora - timedelta(days=91)
    )

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert _ids(res) == [reciente.id]
    assert _meta(res)["total"] == 1
    assert _meta(res)["no_leidas"] == 1


# ---------------------------------------------------------------------------
# Enlace a la entidad relacionada (HU_71)
# ---------------------------------------------------------------------------
def test_item_includes_link_to_the_related_entity(client, auth_headers, escenario):
    tarea = _crear_notificacion(
        escenario.contador1, entidad_tipo="TAREA", entidad_id=15
    )
    cliente = _crear_notificacion(
        escenario.contador1, entidad_tipo="CLIENTE", entidad_id=7
    )
    sin_entidad = _crear_notificacion(
        escenario.contador1, entidad_tipo=None, entidad_id=None
    )

    res = client.get(URL, headers=auth_headers(escenario.contador1))
    filas = {item["id"]: item for item in res.get_json()["data"]}

    assert filas[tarea.id]["enlace"] == "/tareas/15"
    assert filas[cliente.id]["enlace"] == "/clientes/7"
    assert filas[sin_entidad.id]["enlace"] is None


def test_item_has_the_inbox_contract(client, auth_headers, escenario):
    creada = _crear_notificacion(
        escenario.contador1,
        tipo="ASIGNACION",
        titulo="Nueva tarea asignada",
        mensaje="Declaración — Cliente Uno — prioridad ALTA — vence 2026-11-10",
    )

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    fila = res.get_json()["data"][0]
    assert set(fila) == {
        "id",
        "tipo",
        "titulo",
        "mensaje",
        "entidad_tipo",
        "entidad_id",
        "enlace",
        "leida",
        "created_at",
    }
    assert fila["id"] == creada.id
    assert fila["tipo"] == "ASIGNACION"
    assert fila["leida"] is False
    assert fila["created_at"]


# ---------------------------------------------------------------------------
# Paginación (RG-07)
# ---------------------------------------------------------------------------
def test_inbox_is_paginated_in_pages_of_20(client, auth_headers, escenario):
    for numero in range(21):
        _crear_notificacion(escenario.contador1, titulo=f"Aviso {numero}")

    primera = client.get(URL, headers=auth_headers(escenario.contador1))
    segunda = client.get(
        URL, query_string={"page": 2}, headers=auth_headers(escenario.contador1)
    )

    assert len(_ids(primera)) == 20
    assert len(_ids(segunda)) == 1
    assert _meta(primera) == {
        "page": 1,
        "per_page": 20,
        "total": 21,
        "pages": 2,
        "no_leidas": 21,
    }
    assert _meta(segunda)["page"] == 2
    assert set(_ids(primera)).isdisjoint(_ids(segunda))


# ---------------------------------------------------------------------------
# HU_72: marcar una notificación como leída
# ---------------------------------------------------------------------------
def test_mark_own_notification_as_read(client, auth_headers, escenario):
    notificacion = _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1)

    res = client.patch(
        f"{URL}/{notificacion.id}/leida", headers=auth_headers(escenario.contador1)
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["notificacion"]["id"] == notificacion.id
    assert data["notificacion"]["leida"] is True
    assert data["no_leidas"] == 1

    db.session.expire_all()
    assert db.session.get(Notificacion, notificacion.id).leida is True


def test_mark_as_read_is_idempotent(client, auth_headers, escenario):
    notificacion = _crear_notificacion(escenario.contador1, leida=True)

    res = client.patch(
        f"{URL}/{notificacion.id}/leida", headers=auth_headers(escenario.contador1)
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["notificacion"]["leida"] is True
    assert res.get_json()["data"]["no_leidas"] == 0


def test_cannot_mark_another_users_notification(client, auth_headers, escenario):
    ajena = _crear_notificacion(escenario.contador2)

    res = client.patch(
        f"{URL}/{ajena.id}/leida", headers=auth_headers(escenario.contador1)
    )

    assert res.status_code == 404
    assert res.get_json()["error"]["code"] == "NOT_FOUND"
    db.session.expire_all()
    assert db.session.get(Notificacion, ajena.id).leida is False


def test_mark_as_read_returns_404_when_it_does_not_exist(client, auth_headers, escenario):
    res = client.patch(f"{URL}/999999/leida", headers=auth_headers(escenario.contador1))

    assert res.status_code == 404


def test_marking_as_read_requires_authentication(client, escenario):
    notificacion = _crear_notificacion(escenario.contador1)

    assert client.patch(f"{URL}/{notificacion.id}/leida").status_code == 401


# ---------------------------------------------------------------------------
# HU_73: marcar todas como leídas
# ---------------------------------------------------------------------------
def test_mark_all_read_only_affects_own_notifications(client, auth_headers, escenario):
    _crear_notificacion(escenario.contador1)
    _crear_notificacion(escenario.contador1)
    ajena = _crear_notificacion(escenario.contador2)

    res = client.patch(f"{URL}/leidas", headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    assert res.get_json()["data"] == {"actualizadas": 2, "no_leidas": 0}

    db.session.expire_all()
    assert db.session.get(Notificacion, ajena.id).leida is False

    bandeja = client.get(URL, headers=auth_headers(escenario.contador1))
    assert _meta(bandeja)["no_leidas"] == 0


def test_mark_all_read_is_idempotent(client, auth_headers, escenario):
    _crear_notificacion(escenario.contador1)
    client.patch(f"{URL}/leidas", headers=auth_headers(escenario.contador1))

    res = client.patch(f"{URL}/leidas", headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    assert res.get_json()["data"] == {"actualizadas": 0, "no_leidas": 0}


def test_mark_all_read_requires_authentication(client, escenario):
    assert client.patch(f"{URL}/leidas").status_code == 401


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("parametro", "valor", "campo"),
    [
        ("page", "0", "page"),
        ("page", "abc", "page"),
        ("leida", "quizas", "leida"),
    ],
)
def test_invalid_filters_return_422(
    client, auth_headers, escenario, parametro, valor, campo
):
    res = client.get(
        URL,
        query_string={parametro: valor},
        headers=auth_headers(escenario.contador1),
    )

    assert res.status_code == 422
    assert campo in res.get_json()["error"]["fields"]
