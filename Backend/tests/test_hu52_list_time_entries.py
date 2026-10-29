"""HU_52: Consultar registros de tiempo."""
from datetime import timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.extensions import db
from tests.time_helpers import crear_categoria, crear_cliente, crear_registro, crear_tarea

URL = "/api/v1/time-entries"


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.list@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.list@despacho.com", "ADMINISTRADOR", nombre="Admin Lista")
    coordinador = make_user(
        "carla.list@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user("ana.list@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.list@despacho.com", "CONTADOR", nombre="Beto Contador")

    cliente1 = crear_cliente(contador1, "Cliente Uno", "XUNO010101000")
    cliente2 = crear_cliente(contador1, "Cliente Dos", "XDOS010101000")
    categoria = crear_categoria("Fiscal")
    hoy = today_mx()

    tarea_c1 = crear_tarea(
        titulo="Declaración de Cliente Uno",
        cliente=cliente1,
        categoria=categoria,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )
    tarea_c2 = crear_tarea(
        titulo="Nómina de Cliente Dos",
        cliente=cliente2,
        categoria=categoria,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )
    tarea_ajena = crear_tarea(
        titulo="Tarea de Beto",
        cliente=cliente1,
        categoria=categoria,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
    )

    registros = {
        "hoy_c1": crear_registro(tarea_c1, contador1, minutos=60, descripcion="Trabajo de hoy"),
        "hoy_c2": crear_registro(tarea_ajena, contador2, minutos=30, descripcion="Trabajo de Beto"),
        "ayer_c1": crear_registro(
            tarea_c2,
            contador1,
            fecha=hoy - timedelta(days=1),
            minutos=90,
            descripcion="Trabajo de ayer",
        ),
        "viejo_c1": crear_registro(
            tarea_c1,
            contador1,
            fecha=hoy - timedelta(days=60),
            minutos=120,
            descripcion="Trabajo viejo",
        ),
    }
    eliminado = crear_registro(
        tarea_c1, contador1, minutos=45, descripcion="Registro eliminado"
    )
    eliminado.deleted_at = utcnow()
    db.session.commit()

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
        cliente1=cliente1,
        cliente2=cliente2,
        categoria=categoria,
        tarea_c1=tarea_c1,
        tarea_c2=tarea_c2,
        tarea_ajena=tarea_ajena,
        registros=registros,
        hoy=hoy,
    )


def _ids(res) -> set[int]:
    return {item["id"] for item in res.get_json()["data"]}


# ---------------------------------------------------------------------------
# Acceso y alcance (RG-12)
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401


def test_inactive_user_is_rejected(client, auth_headers, make_user, escenario):
    inactivo = make_user("inactivo.list@despacho.com", "CONTADOR", estatus="INACTIVO")
    assert client.get(URL, headers=auth_headers(inactivo)).status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador", "contador1"])
def test_all_four_roles_can_list(client, auth_headers, escenario, actor):
    res = client.get(URL, headers=auth_headers(getattr(escenario, actor)))
    assert res.status_code == 200
    assert "data" in res.get_json()
    assert "meta" in res.get_json()


def test_accountant_sees_only_his_records(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))
    ids = _ids(res)

    assert escenario.registros["hoy_c1"].id in ids
    assert escenario.registros["hoy_c2"].id not in ids
    assert escenario.registros["ayer_c1"].id in ids


def test_management_roles_see_everyones_records(client, auth_headers, escenario):
    for actor in ("dueno", "admin", "coordinador"):
        res = client.get(URL, headers=auth_headers(getattr(escenario, actor)))
        ids = _ids(res)
        assert escenario.registros["hoy_c1"].id in ids
        assert escenario.registros["hoy_c2"].id in ids


def test_deleted_records_are_excluded(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))
    descripciones = {item["descripcion"] for item in res.get_json()["data"]}
    assert "Registro eliminado" not in descripciones


# ---------------------------------------------------------------------------
# Filtros (HU_52)
# ---------------------------------------------------------------------------
def test_default_range_is_current_week(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))
    ids = _ids(res)

    assert escenario.registros["hoy_c1"].id in ids
    assert escenario.registros["viejo_c1"].id not in ids


def test_date_range_filter(client, auth_headers, escenario):
    viejo = escenario.registros["viejo_c1"]
    res = client.get(
        URL,
        query_string={"fecha_desde": viejo.fecha.isoformat(), "fecha_hasta": viejo.fecha.isoformat()},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _ids(res) == {viejo.id}


def test_employee_filter_for_management(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"empleado": escenario.contador2.id},
        headers=auth_headers(escenario.admin),
    )

    assert _ids(res) == {escenario.registros["hoy_c2"].id}


def test_employee_filter_is_ignored_for_accountant(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"empleado": escenario.contador2.id},
        headers=auth_headers(escenario.contador1),
    )
    ids = _ids(res)

    assert escenario.registros["hoy_c2"].id not in ids
    assert escenario.registros["hoy_c1"].id in ids


def test_client_filter(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "cliente": escenario.cliente1.id,
            "fecha_desde": escenario.hoy.isoformat(),
            "fecha_hasta": escenario.hoy.isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )

    ids = _ids(res)
    assert escenario.registros["hoy_c1"].id in ids
    assert escenario.registros["hoy_c2"].id in ids
    assert escenario.registros["ayer_c1"].id not in ids


def test_invalid_date_range(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"fecha_desde": "2026-10-10", "fecha_hasta": "2026-10-01"},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 422
    assert "fecha_desde" in res.get_json()["error"]["fields"]


def test_invalid_page(client, auth_headers, escenario):
    res = client.get(URL, query_string={"page": 0}, headers=auth_headers(escenario.admin))
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# Columnas y totales
# ---------------------------------------------------------------------------
def test_columns_and_hours(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "fecha_desde": escenario.hoy.isoformat(),
            "fecha_hasta": escenario.hoy.isoformat(),
        },
        headers=auth_headers(escenario.contador1),
    )
    item = next(
        fila for fila in res.get_json()["data"] if fila["id"] == escenario.registros["hoy_c1"].id
    )

    assert item["fecha"] == escenario.hoy.isoformat()
    assert item["empleado_nombre"] == "Ana Contadora"
    assert item["cliente_nombre"] == "Cliente Uno"
    assert item["tarea_titulo"] == "Declaración de Cliente Uno"
    assert item["tipo"] == "MANUAL"
    assert item["duracion_minutos"] == 60
    assert item["horas"] == 1.0
    assert item["descripcion"] == "Trabajo de hoy"


def test_total_hours_of_the_filter(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "fecha_desde": escenario.hoy.isoformat(),
            "fecha_hasta": escenario.hoy.isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )
    meta = res.get_json()["meta"]

    assert meta["total_minutos"] == 90
    assert meta["total_horas"] == 1.5
    assert meta["total"] == 2
    assert meta["page"] == 1
    assert meta["per_page"] == 20


def test_pagination_uses_20_per_page(client, auth_headers, escenario):
    for _ in range(21):
        crear_registro(escenario.tarea_ajena, escenario.contador2, minutos=10)

    query = {
        "empleado": escenario.contador2.id,
        "fecha_desde": escenario.hoy.isoformat(),
        "fecha_hasta": escenario.hoy.isoformat(),
    }
    headers = auth_headers(escenario.admin)

    primera = client.get(URL, query_string=query, headers=headers)
    segunda = client.get(URL, query_string={**query, "page": 2}, headers=headers)

    assert primera.status_code == 200
    assert len(primera.get_json()["data"]) == 20
    assert primera.get_json()["meta"]["total"] == 22  # 21 nuevos + el de Beto
    assert primera.get_json()["meta"]["pages"] == 2
    assert len(segunda.get_json()["data"]) == 2
