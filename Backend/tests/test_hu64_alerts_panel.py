"""HU_64: Consultar panel de alertas de vencimiento."""
from datetime import date, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.core.semaforo import SEMAFORO_AMARILLO, SEMAFORO_ROJO
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

URL = "/api/v1/tasks/alerts"
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
        descripcion="Tarea del panel de alertas",
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


def _data(res) -> dict:
    return res.get_json()["data"]


def _ids(res) -> list[int]:
    return [tarea["id"] for tarea in _data(res)["tareas"]]


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.alertas@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.alertas@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador = make_user("ana.alertas@despacho.com", "CONTADOR", nombre="Ana Contadora")
    coordinador = make_user(
        "carla.alertas@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente_a = _crear_cliente(contador, "Cliente Alfa", "XAle010101000")
    cliente_b = _crear_cliente(contador, "Cliente Beta", "XBeta010101000")
    cliente_sin = _crear_cliente(contador, "Cliente Sin Alertas", "XSin010101000")
    fiscal = _crear_categoria("Fiscal")
    hoy = today_mx()

    tareas = {
        "rojo_vencida": _crear_tarea(
            titulo="Declaración vencida",
            cliente=cliente_a,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy - timedelta(days=3),
            prioridad="ALTA",
        ),
        "rojo_hoy": _crear_tarea(
            titulo="Declaración de hoy",
            cliente=cliente_a,
            categoria=fiscal,
            asignado=coordinador,
            creador=admin,
            fecha_limite=hoy,
            estado=ESTADO_EN_PROGRESO,
            prioridad="MEDIA",
        ),
        "amarillo_manana": _crear_tarea(
            titulo="Declaración de mañana",
            cliente=cliente_a,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy + timedelta(days=1),
            estado=ESTADO_EN_REVISION,
            prioridad="ALTA",
        ),
        "amarillo_dos": _crear_tarea(
            titulo="Declaración en dos días",
            cliente=cliente_b,
            categoria=fiscal,
            asignado=coordinador,
            creador=coordinador,
            fecha_limite=hoy + timedelta(days=2),
            prioridad="BAJA",
        ),
        "verde": _crear_tarea(
            titulo="Declaración en tres días",
            cliente=cliente_a,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "completada": _crear_tarea(
            titulo="Declaración completada",
            cliente=cliente_a,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy - timedelta(days=1),
            estado=ESTADO_COMPLETADO,
        ),
        "eliminada": _crear_tarea(
            titulo="Declaración eliminada",
            cliente=cliente_b,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy - timedelta(days=2),
        ),
        "sin_alerta": _crear_tarea(
            titulo="Declaración lejana",
            cliente=cliente_sin,
            categoria=fiscal,
            asignado=contador,
            creador=admin,
            fecha_limite=hoy + timedelta(days=5),
        ),
    }
    tareas["eliminada"].deleted_at = utcnow()
    db.session.commit()

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        contador=contador,
        coordinador=coordinador,
        cliente_a=cliente_a,
        cliente_b=cliente_b,
        cliente_sin=cliente_sin,
        fiscal=fiscal,
        tareas=tareas,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401


def test_accountant_cannot_see_the_alerts_panel(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador))

    assert res.status_code == 403
    assert res.get_json()["error"]["message"] == MSG_FORBIDDEN


@pytest.mark.parametrize("rol", ["dueno", "admin", "coordinador"])
def test_owner_admin_and_coordinator_can_see_the_panel(
    client, auth_headers, escenario, rol
):
    res = client.get(URL, headers=auth_headers(getattr(escenario, rol)))

    assert res.status_code == 200


# ---------------------------------------------------------------------------
# Conteos y listado
# ---------------------------------------------------------------------------
def test_counts_and_list_include_only_red_and_yellow(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    data = _data(res)
    assert data["conteos"] == {SEMAFORO_ROJO: 2, SEMAFORO_AMARILLO: 2}
    assert _ids(res) == [
        escenario.tareas["rojo_vencida"].id,
        escenario.tareas["rojo_hoy"].id,
        escenario.tareas["amarillo_manana"].id,
        escenario.tareas["amarillo_dos"].id,
    ]
    assert res.get_json()["meta"] == {"page": 1, "per_page": 20, "total": 4, "pages": 1}


def test_list_is_ordered_red_first_then_yellow_by_deadline(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    fechas = [tarea["fecha_limite"] for tarea in _data(res)["tareas"]]
    assert fechas == sorted(fechas)
    assert [tarea["semaforo"] for tarea in _data(res)["tareas"]] == [
        SEMAFORO_ROJO,
        SEMAFORO_ROJO,
        SEMAFORO_AMARILLO,
        SEMAFORO_AMARILLO,
    ]


def test_rows_include_client_task_assignee_deadline_and_delay(
    client, auth_headers, escenario
):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    fila = _data(res)["tareas"][0]
    assert fila["id"] == escenario.tareas["rojo_vencida"].id
    assert fila["titulo"] == "Declaración vencida"
    assert fila["cliente_id"] == escenario.cliente_a.id
    assert fila["cliente_nombre"] == "Cliente Alfa"
    assert fila["asignado_id"] == escenario.contador.id
    assert fila["asignado_nombre"] == "Ana Contadora"
    assert fila["fecha_limite"] == (escenario.hoy - timedelta(days=3)).isoformat()
    assert fila["hora_limite"] == "15:30"
    assert fila["prioridad"] == "ALTA"
    assert fila["estado"] == ESTADO_POR_HACER
    assert fila["semaforo"] == SEMAFORO_ROJO
    assert fila["dias_restantes"] == -3
    assert fila["dias_atraso"] == 3


def test_tasks_due_today_and_tomorrow_have_no_delay(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    filas = {tarea["id"]: tarea for tarea in _data(res)["tareas"]}
    assert filas[escenario.tareas["rojo_hoy"].id]["dias_restantes"] == 0
    assert filas[escenario.tareas["rojo_hoy"].id]["dias_atraso"] == 0
    assert filas[escenario.tareas["amarillo_manana"].id]["dias_restantes"] == 1
    assert filas[escenario.tareas["amarillo_manana"].id]["dias_atraso"] == 0
    assert filas[escenario.tareas["amarillo_dos"].id]["dias_restantes"] == 2
    assert filas[escenario.tareas["amarillo_dos"].id]["dias_atraso"] == 0


def test_completed_and_deleted_tasks_are_excluded(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    ids = set(_ids(res))
    assert escenario.tareas["completada"].id not in ids
    assert escenario.tareas["eliminada"].id not in ids
    assert escenario.tareas["verde"].id not in ids
    assert escenario.tareas["sin_alerta"].id not in ids


# ---------------------------------------------------------------------------
# Filtros
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("color", "esperados"),
    [
        (SEMAFORO_ROJO, ("rojo_vencida", "rojo_hoy")),
        (SEMAFORO_AMARILLO, ("amarillo_manana", "amarillo_dos")),
    ],
)
def test_filter_by_color_keeps_both_counts(
    client, auth_headers, escenario, color, esperados
):
    res = client.get(
        URL, query_string={"color": color}, headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 200
    assert _data(res)["conteos"] == {SEMAFORO_ROJO: 2, SEMAFORO_AMARILLO: 2}
    assert _ids(res) == [escenario.tareas[clave].id for clave in esperados]
    assert res.get_json()["meta"]["total"] == 2


def test_filter_by_cliente(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_a.id},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["conteos"] == {SEMAFORO_ROJO: 2, SEMAFORO_AMARILLO: 1}
    assert _ids(res) == [
        escenario.tareas["rojo_vencida"].id,
        escenario.tareas["rojo_hoy"].id,
        escenario.tareas["amarillo_manana"].id,
    ]


def test_filter_by_responsable(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"responsable": escenario.contador.id},
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["conteos"] == {SEMAFORO_ROJO: 1, SEMAFORO_AMARILLO: 1}
    assert _ids(res) == [
        escenario.tareas["rojo_vencida"].id,
        escenario.tareas["amarillo_manana"].id,
    ]


def test_filters_can_be_combined(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={
            "cliente": escenario.cliente_b.id,
            "responsable": escenario.coordinador.id,
            "color": SEMAFORO_AMARILLO,
        },
        headers=auth_headers(escenario.admin),
    )

    assert _data(res)["conteos"] == {SEMAFORO_ROJO: 0, SEMAFORO_AMARILLO: 1}
    assert _ids(res) == [escenario.tareas["amarillo_dos"].id]


def test_color_is_trimmed_and_uppercased(client, auth_headers, escenario):
    res = client.get(
        URL, query_string={"color": "  rojo  "}, headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 200
    assert _ids(res) == [
        escenario.tareas["rojo_vencida"].id,
        escenario.tareas["rojo_hoy"].id,
    ]


def test_empty_query_params_are_ignored(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": "", "responsable": "", "color": "", "page": ""},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert res.get_json()["meta"]["total"] == 4


# ---------------------------------------------------------------------------
# Paginación (RG-07)
# ---------------------------------------------------------------------------
def test_panel_is_paginated_in_pages_of_20(client, auth_headers, escenario):
    for numero in range(19):
        _crear_tarea(
            titulo=f"Alerta adicional {numero}",
            cliente=escenario.cliente_a,
            categoria=escenario.fiscal,
            asignado=escenario.contador,
            creador=escenario.admin,
            fecha_limite=escenario.hoy - timedelta(days=1),
        )

    primera = client.get(URL, headers=auth_headers(escenario.admin))
    segunda = client.get(
        URL, query_string={"page": 2}, headers=auth_headers(escenario.admin)
    )

    assert _data(primera)["conteos"] == {SEMAFORO_ROJO: 21, SEMAFORO_AMARILLO: 2}
    assert len(_ids(primera)) == 20
    assert len(_ids(segunda)) == 3
    assert primera.get_json()["meta"] == {
        "page": 1,
        "per_page": 20,
        "total": 23,
        "pages": 2,
    }
    assert segunda.get_json()["meta"] == {
        "page": 2,
        "per_page": 20,
        "total": 23,
        "pages": 2,
    }
    assert set(_ids(primera)).isdisjoint(_ids(segunda))


# ---------------------------------------------------------------------------
# Panel vacío
# ---------------------------------------------------------------------------
def test_panel_without_alerts_returns_zero_counts(client, auth_headers, escenario):
    res = client.get(
        URL,
        query_string={"cliente": escenario.cliente_sin.id},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert _data(res)["conteos"] == {SEMAFORO_ROJO: 0, SEMAFORO_AMARILLO: 0}
    assert _data(res)["tareas"] == []
    assert res.get_json()["meta"]["total"] == 0


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("parametro", "valor", "campo"),
    [
        ("color", "VERDE", "color"),
        ("color", "GRIS", "color"),
        ("color", "AZUL", "color"),
        ("cliente", "0", "cliente"),
        ("cliente", "abc", "cliente"),
        ("responsable", "0", "responsable"),
        ("page", "0", "page"),
        ("page", "abc", "page"),
    ],
)
def test_invalid_filters_return_422(
    client, auth_headers, escenario, parametro, valor, campo
):
    res = client.get(
        URL, query_string={parametro: valor}, headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 422
    assert campo in res.get_json()["error"]["fields"]


# ---------------------------------------------------------------------------
# Integración con el detalle (la fila abre la tarea)
# ---------------------------------------------------------------------------
def test_alert_row_opens_the_task_detail(client, auth_headers, escenario):
    tarea = escenario.tareas["rojo_vencida"]

    res = client.get(f"/api/v1/tasks/{tarea.id}", headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    assert res.get_json()["data"]["semaforo"] == SEMAFORO_ROJO
