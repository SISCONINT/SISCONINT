"""HU_42: Filtrar tablero Kanban."""
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import (
    ESTADO_COMPLETADO,
    ESTADO_EN_PROGRESO,
    ESTADO_EN_REVISION,
    ESTADO_POR_HACER,
    Tarea,
)

URL = "/api/v1/tasks/board"
COLUMNAS = ("POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO")
MSG_SIN_RESULTADOS = "No hay tareas con los filtros seleccionados"


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
    estado: str = ESTADO_POR_HACER,
    prioridad: str = "ALTA",
    horas_estimadas: float | None = 4.0,
    completada_en: datetime | None = None,
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Tarea del tablero",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad=prioridad,
        estado=estado,
        horas_estimadas=horas_estimadas,
        notificar_cliente=True,
        cliente_notificado=False,
        completada_en=completada_en,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _data(res) -> dict:
    return res.get_json()["data"]


def _columnas(res) -> dict[str, dict]:
    return {columna["estado"]: columna for columna in _data(res)["columnas"]}


def _ids(res, estado: str) -> list[int]:
    return [tarea["id"] for tarea in _columnas(res)[estado]["tareas"]]


def _todos_los_ids(res) -> set[int]:
    return {
        tarea["id"]
        for columna in _data(res)["columnas"]
        for tarea in columna["tareas"]
    }


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.filtra@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.filtra@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.filtra@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.filtra@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.filtra@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente_a = _crear_cliente(contador1, "Cliente Alfa", "XAlf010101000")
    cliente_b = _crear_cliente(contador1, "Cliente Beta", "XBeta010101000")
    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)
    hoy = today_mx()

    alta_a = _crear_tarea(
        titulo="Alta del cliente Alfa",
        cliente=cliente_a,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=2),
        estado=ESTADO_POR_HACER,
        prioridad="ALTA",
    )
    media_a = _crear_tarea(
        titulo="Media del cliente Alfa",
        cliente=cliente_a,
        categoria=fiscal,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy + timedelta(days=6),
        estado=ESTADO_EN_PROGRESO,
        prioridad="MEDIA",
    )
    baja_b = _crear_tarea(
        titulo="Baja del cliente Beta",
        cliente=cliente_b,
        categoria=fiscal,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=10),
        estado=ESTADO_POR_HACER,
        prioridad="BAJA",
    )
    alta_b = _crear_tarea(
        titulo="Alta del cliente Beta",
        cliente=cliente_b,
        categoria=fiscal,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy - timedelta(days=1),
        estado=ESTADO_EN_REVISION,
        prioridad="ALTA",
    )
    completada_a = _crear_tarea(
        titulo="Completada del cliente Alfa",
        cliente=cliente_a,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy - timedelta(days=5),
        estado=ESTADO_COMPLETADO,
        prioridad="MEDIA",
        completada_en=utcnow() - timedelta(days=5),
    )
    ajena = _crear_tarea(
        titulo="Tarea de coordinación",
        cliente=cliente_b,
        categoria=fiscal,
        asignado=contador2,
        creador=coordinador,
        fecha_limite=hoy + timedelta(days=3),
        estado=ESTADO_POR_HACER,
        prioridad="ALTA",
    )

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        coordinador=coordinador,
        cliente_a=cliente_a,
        cliente_b=cliente_b,
        fiscal=fiscal,
        declaraciones=declaraciones,
        alta_a=alta_a,
        media_a=media_a,
        baja_b=baja_b,
        alta_b=alta_b,
        completada_a=completada_a,
        ajena=ajena,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401


# ---------------------------------------------------------------------------
# Sin filtros (HU_41 sigue igual)
# ---------------------------------------------------------------------------
def test_without_filters_returns_the_whole_board(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    assert _data(res)["total_tareas"] == 6
    assert "mensaje" not in _data(res)


# ---------------------------------------------------------------------------
# Filtros individuales
# ---------------------------------------------------------------------------
def test_filter_by_cliente(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_a.id},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 3
    assert _ids(res, ESTADO_POR_HACER) == [escenario.alta_a.id]
    assert _ids(res, ESTADO_EN_PROGRESO) == [escenario.media_a.id]
    assert _ids(res, ESTADO_EN_REVISION) == []
    assert _ids(res, ESTADO_COMPLETADO) == [escenario.completada_a.id]


def test_filter_by_responsable(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"responsable": escenario.contador2.id},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 3
    assert set(_todos_los_ids(res)) == {
        escenario.media_a.id,
        escenario.alta_b.id,
        escenario.ajena.id,
    }


def test_filter_by_prioridad(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"prioridad": "ALTA"},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 3
    assert set(_todos_los_ids(res)) == {
        escenario.alta_a.id,
        escenario.alta_b.id,
        escenario.ajena.id,
    }


def test_filter_by_date_range(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "fecha_limite_desde": escenario.hoy.isoformat(),
            "fecha_limite_hasta": (escenario.hoy + timedelta(days=6)).isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 3
    assert set(_todos_los_ids(res)) == {
        escenario.alta_a.id,
        escenario.media_a.id,
        escenario.ajena.id,
    }


def test_date_range_is_inclusive(client, auth_headers, escenario):
    dia = (escenario.hoy + timedelta(days=6)).isoformat()

    res = client.get(
        URL,
        query_string={"fecha_limite_desde": dia, "fecha_limite_hasta": dia},
        headers=auth_headers(escenario.admin),
    )

    assert _todos_los_ids(res) == {escenario.media_a.id}


# ---------------------------------------------------------------------------
# Filtros combinados
# ---------------------------------------------------------------------------
def test_filters_can_be_combined(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_a.id, "prioridad": "MEDIA"},
        headers=auth_headers(escenario.admin),
    )

    data = _data(res)
    columnas = _columnas(res)
    assert data["total_tareas"] == 2
    assert _ids(res, ESTADO_EN_PROGRESO) == [escenario.media_a.id]
    assert _ids(res, ESTADO_COMPLETADO) == [escenario.completada_a.id]
    assert columnas[ESTADO_POR_HACER]["total"] == 0
    assert columnas[ESTADO_EN_REVISION]["total"] == 0
    assert sum(columna["total"] for columna in columnas.values()) == 2


def test_combined_filters_with_date_range(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "cliente": escenario.cliente_b.id,
            "prioridad": "ALTA",
            "fecha_limite_desde": escenario.hoy.isoformat(),
            "fecha_limite_hasta": (escenario.hoy + timedelta(days=5)).isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 1
    assert _todos_los_ids(res) == {escenario.ajena.id}


# ---------------------------------------------------------------------------
# Sin resultados
# ---------------------------------------------------------------------------
def test_empty_result_returns_the_message(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_a.id, "prioridad": "BAJA"},
        headers=auth_headers(escenario.admin),
    )

    data = _data(res)
    assert res.status_code == 200
    assert data["total_tareas"] == 0
    assert data["mensaje"] == MSG_SIN_RESULTADOS
    assert [(columna["estado"], columna["total"]) for columna in data["columnas"]] == [
        (estado, 0) for estado in COLUMNAS
    ]
    assert all(columna["tareas"] == [] for columna in data["columnas"])


def test_message_is_absent_when_there_are_results(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"prioridad": "ALTA"},
        headers=auth_headers(escenario.admin),
    )

    assert "mensaje" not in _data(res)


def test_no_message_without_filters_on_empty_board(client, auth_headers, make_user):
    admin = make_user("admin.vacio@despacho.com", "ADMINISTRADOR", nombre="Admin Vacío")

    res = client.get(URL, headers=auth_headers(admin))

    assert _data(res)["total_tareas"] == 0
    assert "mensaje" not in _data(res)


# ---------------------------------------------------------------------------
# Alcance del Contador (RG-12) y el filtro responsable
# ---------------------------------------------------------------------------
def test_accountant_cannot_filter_by_responsable(client, auth_headers, escenario):
    """El filtro se ignora: el Contador sigue viendo solo sus tareas."""
    res = client.get(
        URL,
        query_string={"responsable": escenario.contador2.id},
        headers=auth_headers(escenario.contador1),
    )

    assert _data(res)["total_tareas"] == 3
    assert set(_todos_los_ids(res)) == {
        escenario.alta_a.id,
        escenario.baja_b.id,
        escenario.completada_a.id,
    }


def test_accountant_scope_is_kept_with_filters(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_b.id},
        headers=auth_headers(escenario.contador1),
    )

    assert _data(res)["total_tareas"] == 1
    assert _todos_los_ids(res) == {escenario.baja_b.id}
    assert escenario.ajena.id not in _todos_los_ids(res)
    assert escenario.alta_b.id not in _todos_los_ids(res)


# ---------------------------------------------------------------------------
# Normalización y validaciones
# ---------------------------------------------------------------------------
def test_priority_is_trimmed_and_uppercased(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"prioridad": "  alta  "},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 3


def test_empty_query_params_are_ignored(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "cliente": "",
            "responsable": "",
            "prioridad": "",
            "fecha_limite_desde": "",
            "fecha_limite_hasta": "",
        },
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _data(res)["total_tareas"] == 6
    assert "mensaje" not in _data(res)


@pytest.mark.parametrize(
    ("parametro", "valor"),
    [
        ("prioridad", "URGENTE"),
        ("fecha_limite_desde", "2026-13-01"),
        ("fecha_limite_hasta", "mañana"),
        ("cliente", "abc"),
        ("responsable", "0"),
    ],
)
def test_invalid_filters_return_422(client, auth_headers, escenario, parametro, valor):
    res = client.get(
        URL,
        query_string={parametro: valor},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    assert parametro in res.get_json()["error"]["fields"]


def test_inverted_date_range_returns_422(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "fecha_limite_desde": (escenario.hoy + timedelta(days=5)).isoformat(),
            "fecha_limite_hasta": escenario.hoy.isoformat(),
        },
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 422
    fields = res.get_json()["error"]["fields"]
    assert fields["fecha_limite_desde"] == [
        "La fecha límite inicial no puede ser posterior a la final"
    ]


# ---------------------------------------------------------------------------
# Regla de los 30 días al filtrar
# ---------------------------------------------------------------------------
def test_completed_filter_still_hides_old_completed_tasks(
    client, auth_headers, escenario
):
    _crear_tarea(
        titulo="Completada hace más de un mes",
        cliente=escenario.cliente_a,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.admin,
        fecha_limite=escenario.hoy - timedelta(days=40),
        estado=ESTADO_COMPLETADO,
        prioridad="MEDIA",
        completada_en=utcnow() - timedelta(days=31),
    )

    res = client.get(
        URL,
        query_string={"prioridad": "MEDIA"},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["total_tareas"] == 2
    assert set(_ids(res, ESTADO_COMPLETADO)) == {escenario.completada_a.id}
