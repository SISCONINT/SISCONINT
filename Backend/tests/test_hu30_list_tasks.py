"""HU_30: Consultar listado de tareas."""
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.core.semaforo import (
    SEMAFORO_AMARILLO,
    SEMAFORO_GRIS,
    SEMAFORO_ROJO,
    SEMAFORO_VERDE,
    calcular_semaforo,
)
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import Tarea

URL = "/api/v1/tasks"


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
    creador=None,
    fecha_limite: date | None = None,
    hora_limite: time = time(23, 59),
    prioridad: str = "MEDIA",
    estado: str = "POR_HACER",
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=(creador or asignado).id,
        fecha_limite=fecha_limite or today_mx(),
        hora_limite=hora_limite,
        prioridad=prioridad,
        estado=estado,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


@pytest.fixture()
def escenario(make_user):
    """6 tareas que cubren alcance RG-12, filtros y los 4 colores del semáforo."""
    admin = make_user("admin.tareas@despacho.com", "ADMINISTRADOR")
    contador1 = make_user("contador1.tareas@despacho.com", "CONTADOR")
    contador2 = make_user("contador2.tareas@despacho.com", "CONTADOR")

    cliente1 = _crear_cliente(contador1, "Cliente Uno", "XUno010101000")
    cliente2 = _crear_cliente(contador2, "Cliente Dos", "XDos010101000")

    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)
    contabilidad = _crear_categoria("Contabilidad")

    hoy = today_mx()
    tareas = {
        # clave: (título, cliente, categoría, asignado, creador, fecha, prioridad, estado)
        "verde": _crear_tarea(
            titulo="Declaración anual",
            cliente=cliente1,
            categoria=declaraciones,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy + timedelta(days=5),
            hora_limite=time(10, 5),
            prioridad="ALTA",
        ),
        "amarilla": _crear_tarea(
            titulo="Cálculo de nómina",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador2,
            creador=admin,
            fecha_limite=hoy + timedelta(days=2),
            prioridad="MEDIA",
            estado="EN_PROGRESO",
        ),
        "roja_vencida": _crear_tarea(
            titulo="Declaración vencida",
            cliente=cliente2,
            categoria=contabilidad,
            asignado=contador1,
            creador=contador1,
            fecha_limite=hoy - timedelta(days=1),
            prioridad="BAJA",
            estado="EN_REVISION",
        ),
        "gris": _crear_tarea(
            titulo="Conciliación cerrada",
            cliente=cliente2,
            categoria=contabilidad,
            asignado=contador2,
            creador=admin,
            fecha_limite=hoy - timedelta(days=10),
            prioridad="MEDIA",
            estado="COMPLETADO",
        ),
        "creada_contador1": _crear_tarea(
            titulo="Revisión interna",
            cliente=cliente1,
            categoria=contabilidad,
            asignado=contador2,
            creador=contador1,
            fecha_limite=hoy + timedelta(days=4),
            prioridad="ALTA",
        ),
        "roja_hoy": _crear_tarea(
            titulo="Entrega de hoy",
            cliente=cliente2,
            categoria=declaraciones,
            asignado=contador2,
            creador=admin,
            fecha_limite=hoy,
            prioridad="BAJA",
        ),
    }

    return SimpleNamespace(
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        cliente1=cliente1,
        cliente2=cliente2,
        fiscal=fiscal,
        declaraciones=declaraciones,
        contabilidad=contabilidad,
        tareas=tareas,
        hoy=hoy,
    )


def _ids(data: list[dict]) -> set[int]:
    return {item["id"] for item in data}


# ---------------------------------------------------------------------------
# RG-11: cálculo del semáforo
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dias,estado,esperado",
    [
        (5, "POR_HACER", SEMAFORO_VERDE),
        (3, "POR_HACER", SEMAFORO_VERDE),
        (2, "POR_HACER", SEMAFORO_AMARILLO),
        (1, "EN_PROGRESO", SEMAFORO_AMARILLO),
        (0, "POR_HACER", SEMAFORO_ROJO),
        (-1, "EN_REVISION", SEMAFORO_ROJO),
        (-30, "COMPLETADO", SEMAFORO_GRIS),
        (10, "COMPLETADO", SEMAFORO_GRIS),
    ],
)
def test_semaforo_rg11_por_dias_naturales(dias, estado, esperado):
    hoy = date(2026, 10, 25)
    assert calcular_semaforo(estado, hoy + timedelta(days=dias), hoy) == esperado


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client):
    assert client.get(URL).status_code == 401


def test_inactive_user_is_rejected(client, auth_headers, make_user):
    inactivo = make_user("inactivo.tareas@despacho.com", "CONTADOR", estatus="INACTIVO")
    assert client.get(URL, headers=auth_headers(inactivo)).status_code == 401


@pytest.mark.parametrize("rol", ["DUENO", "ADMINISTRADOR", "COORDINADOR", "CONTADOR"])
def test_all_four_roles_can_list(client, auth_headers, make_user, rol):
    actor = make_user(f"{rol.lower()}.listado@despacho.com", rol)
    res = client.get(URL, headers=auth_headers(actor))
    assert res.status_code == 200
    assert res.get_json()["data"] == []


# ---------------------------------------------------------------------------
# Alcance del Contador (RG-12)
# ---------------------------------------------------------------------------
def test_owner_admin_and_coordinator_see_all_tasks(client, auth_headers, escenario, make_user):
    coordinador = make_user("coordinador.tareas@despacho.com", "COORDINADOR")
    dueno = make_user("dueno.tareas@despacho.com", "DUENO")
    esperado = 6

    for actor in (escenario.admin, coordinador, dueno):
        res = client.get(URL, headers=auth_headers(actor))
        assert res.status_code == 200
        assert res.get_json()["meta"]["total"] == esperado


def test_accountant_only_sees_assigned_or_created_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))
    assert res.status_code == 200

    data = res.get_json()["data"]
    assert _ids(data) == {
        escenario.tareas["verde"].id,
        escenario.tareas["roja_vencida"].id,
        escenario.tareas["creada_contador1"].id,
    }
    assert res.get_json()["meta"]["total"] == 3


def test_accountant_cannot_filter_by_another_responsible(client, auth_headers, escenario):
    """El filtro responsable no está disponible para Contador: se ignora (HU_30)."""
    res = client.get(
        URL,
        query_string={"responsable": escenario.contador2.id},
        headers=auth_headers(escenario.contador1),
    )
    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] == 3
    assert _ids(res.get_json()["data"]) == {
        escenario.tareas["verde"].id,
        escenario.tareas["roja_vencida"].id,
        escenario.tareas["creada_contador1"].id,
    }


# ---------------------------------------------------------------------------
# Columnas y semáforo
# ---------------------------------------------------------------------------
def test_columns_and_calculated_semaforo(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente1.id},
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 200

    item = next(
        t for t in res.get_json()["data"] if t["id"] == escenario.tareas["verde"].id
    )
    assert item == {
        "id": escenario.tareas["verde"].id,
        "titulo": "Declaración anual",
        "cliente_id": escenario.cliente1.id,
        "cliente_nombre": "Cliente Uno",
        "categoria_id": escenario.declaraciones.id,
        "categoria_nombre": "Declaraciones",
        "categoria_padre_nombre": "Fiscal",
        "asignado_id": escenario.contador1.id,
        "asignado_nombre": "Usuario Contador",
        "prioridad": "ALTA",
        "estado": "POR_HACER",
        "fecha_limite": (escenario.hoy + timedelta(days=5)).isoformat(),
        "hora_limite": "10:05",
        "semaforo": SEMAFORO_VERDE,
        "dias_restantes": 5,
    }


def test_semaforo_colors_in_response(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))
    colores = {item["id"]: item["semaforo"] for item in res.get_json()["data"]}

    assert colores[escenario.tareas["verde"].id] == SEMAFORO_VERDE
    assert colores[escenario.tareas["amarilla"].id] == SEMAFORO_AMARILLO
    assert colores[escenario.tareas["roja_vencida"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["roja_hoy"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["gris"].id] == SEMAFORO_GRIS


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "filtro,claves",
    [
        ("cliente", ("verde", "amarilla", "creada_contador1")),
        ("responsable", ("amarilla", "gris", "creada_contador1", "roja_hoy")),
        ("categoria_padre", ("verde", "amarilla", "roja_hoy")),
        ("categoria_subcategoria", ("verde", "roja_hoy")),
    ],
)
def test_filters_by_cliente_responsable_and_categoria(
    client, auth_headers, escenario, filtro, claves
):
    query = {
        "cliente": {"cliente": escenario.cliente1.id},
        "responsable": {"responsable": escenario.contador2.id},
        "categoria_padre": {"categoria": escenario.fiscal.id},
        "categoria_subcategoria": {"categoria": escenario.declaraciones.id},
    }[filtro]

    res = client.get(URL, query_string=query, headers=auth_headers(escenario.admin))
    assert res.status_code == 200
    assert _ids(res.get_json()["data"]) == {escenario.tareas[c].id for c in claves}


@pytest.mark.parametrize(
    "query,claves",
    [
        ({"estado": "COMPLETADO"}, ("gris",)),
        ({"prioridad": "ALTA"}, ("verde", "creada_contador1")),
        ({"semaforo": SEMAFORO_VERDE}, ("verde", "creada_contador1")),
        ({"semaforo": SEMAFORO_AMARILLO}, ("amarilla",)),
        ({"semaforo": SEMAFORO_ROJO}, ("roja_vencida", "roja_hoy")),
        ({"semaforo": SEMAFORO_GRIS}, ("gris",)),
    ],
)
def test_filters_by_estado_prioridad_and_semaforo(
    client, auth_headers, escenario, query, claves
):
    res = client.get(URL, query_string=query, headers=auth_headers(escenario.admin))
    assert res.status_code == 200
    assert _ids(res.get_json()["data"]) == {escenario.tareas[c].id for c in claves}


def test_filter_by_fecha_limite_range_is_inclusive(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "fecha_limite_desde": (escenario.hoy + timedelta(days=2)).isoformat(),
            "fecha_limite_hasta": (escenario.hoy + timedelta(days=4)).isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 200
    assert _ids(res.get_json()["data"]) == {
        escenario.tareas["amarilla"].id,
        escenario.tareas["creada_contador1"].id,
    }


def test_enums_and_dates_are_case_insensitive_and_empty_filters_are_ignored(
    client, auth_headers, escenario
):
    res = client.get(
        URL,
        query_string={
            "estado": "completado",
            "prioridad": "",
            "semaforo": "gris",
            "cliente": "",
        },
        headers=auth_headers(escenario.admin),
    )
    assert res.status_code == 200
    assert _ids(res.get_json()["data"]) == {escenario.tareas["gris"].id}


# ---------------------------------------------------------------------------
# Orden y paginación (RG-07)
# ---------------------------------------------------------------------------
def test_default_order_is_deadline_ascending(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))
    titulos = [item["titulo"] for item in res.get_json()["data"]]

    assert titulos == [
        "Conciliación cerrada",      # hoy - 10
        "Declaración vencida",       # hoy - 1
        "Entrega de hoy",            # hoy
        "Cálculo de nómina",         # hoy + 2
        "Revisión interna",          # hoy + 4
        "Declaración anual",         # hoy + 5
    ]


def test_pagination_is_fixed_to_twenty(client, auth_headers, escenario):
    for i in range(19):
        _crear_tarea(
            titulo=f"Tarea adicional {i:02d}",
            cliente=escenario.cliente1,
            categoria=escenario.contabilidad,
            asignado=escenario.contador1,
            creador=escenario.admin,
            fecha_limite=escenario.hoy + timedelta(days=30),
        )

    res1 = client.get(URL, headers=auth_headers(escenario.admin))
    body1 = res1.get_json()
    assert res1.status_code == 200
    assert len(body1["data"]) == 20
    assert body1["meta"] == {"page": 1, "per_page": 20, "total": 25, "pages": 2}

    res2 = client.get(URL, query_string={"page": 2}, headers=auth_headers(escenario.admin))
    body2 = res2.get_json()
    assert res2.status_code == 200
    assert len(body2["data"]) == 5
    assert body2["meta"]["page"] == 2
    assert body2["meta"]["total"] == 25

    ids_pagina_1 = _ids(body1["data"])
    ids_pagina_2 = _ids(body2["data"])
    assert ids_pagina_1.isdisjoint(ids_pagina_2)


# ---------------------------------------------------------------------------
# Soft delete (RG-03)
# ---------------------------------------------------------------------------
def test_deleted_tasks_are_excluded(client, auth_headers, escenario):
    tarea = escenario.tareas["verde"]
    tarea.deleted_at = utcnow()
    db.session.commit()

    res = client.get(URL, headers=auth_headers(escenario.admin))
    assert res.status_code == 200
    assert tarea.id not in _ids(res.get_json()["data"])
    assert res.get_json()["meta"]["total"] == 5


# ---------------------------------------------------------------------------
# Validación de query params (RG-09)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "query",
    [
        {"cliente": "abc"},
        {"cliente": 0},
        {"responsable": 0},
        {"categoria": -1},
        {"estado": "FINALIZADO"},
        {"prioridad": "URGENTE"},
        {"semaforo": "AZUL"},
        {"page": 0},
        {"page": "abc"},
        {"fecha_limite_desde": "2026-13-01"},
        {"fecha_limite_desde": "2026-10-10", "fecha_limite_hasta": "2026-10-01"},
    ],
)
def test_invalid_query_params_return_422(client, auth_headers, escenario, query):
    res = client.get(URL, query_string=query, headers=auth_headers(escenario.admin))
    assert res.status_code == 422
    assert res.get_json()["error"]["code"] == "VALIDATION_ERROR"
