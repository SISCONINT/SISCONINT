"""HU_63: Visualizar semáforo de vencimiento (RG-11)."""
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
from app.models.task import (
    ESTADO_COMPLETADO,
    ESTADO_EN_PROGRESO,
    ESTADO_EN_REVISION,
    ESTADO_POR_HACER,
    Tarea,
)
from app.services import task_service

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
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Tarea para el semáforo",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad="ALTA",
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


def _colores(res) -> dict[int, str]:
    return {item["id"]: item["semaforo"] for item in res.get_json()["data"]}


def _tarjeta(columnas: dict, tarea_id: int) -> dict:
    for columna in columnas.values():
        for tarjeta in columna["tareas"]:
            if tarjeta["id"] == tarea_id:
                return tarjeta
    raise AssertionError(f"La tarea {tarea_id} no está en el tablero")


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.semaforo@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.semaforo@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.semaforo@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.semaforo@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.semaforo@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente1 = _crear_cliente(contador1, "Cliente Uno", "XSem010101000")
    cliente2 = _crear_cliente(contador2, "Cliente Dos", "XSem010101001")
    fiscal = _crear_categoria("Fiscal")
    hoy = today_mx()

    tareas = {
        "vencida": _crear_tarea(
            titulo="Vencida hace dos días",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy - timedelta(days=2),
        ),
        "hoy": _crear_tarea(
            titulo="Vence hoy",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy,
        ),
        "manana": _crear_tarea(
            titulo="Vence mañana",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy + timedelta(days=1),
            estado=ESTADO_EN_PROGRESO,
        ),
        "dos_dias": _crear_tarea(
            titulo="Vence en dos días",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador2,
            creador=coordinador,
            fecha_limite=hoy + timedelta(days=2),
            estado=ESTADO_EN_REVISION,
        ),
        "tres_dias": _crear_tarea(
            titulo="Vence en tres días",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador2,
            creador=coordinador,
            fecha_limite=hoy + timedelta(days=3),
        ),
        "verde_lejos": _crear_tarea(
            titulo="Vence en diez días",
            cliente=cliente2,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy + timedelta(days=10),
        ),
        "completada": _crear_tarea(
            titulo="Ya completada",
            cliente=cliente1,
            categoria=fiscal,
            asignado=contador1,
            creador=admin,
            fecha_limite=hoy - timedelta(days=1),
            estado=ESTADO_COMPLETADO,
        ),
        "ajena": _crear_tarea(
            titulo="Tarea de otro contador",
            cliente=cliente2,
            categoria=fiscal,
            asignado=contador2,
            creador=coordinador,
            fecha_limite=hoy + timedelta(days=1),
        ),
    }

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        coordinador=coordinador,
        cliente1=cliente1,
        cliente2=cliente2,
        fiscal=fiscal,
        tareas=tareas,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# RG-11: cálculo del color
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("dias", "estado", "esperado"),
    [
        (30, ESTADO_POR_HACER, SEMAFORO_VERDE),
        (4, ESTADO_POR_HACER, SEMAFORO_VERDE),
        (3, ESTADO_EN_PROGRESO, SEMAFORO_VERDE),
        (2, ESTADO_POR_HACER, SEMAFORO_AMARILLO),
        (1, ESTADO_EN_REVISION, SEMAFORO_AMARILLO),
        (0, ESTADO_POR_HACER, SEMAFORO_ROJO),
        (-1, ESTADO_EN_PROGRESO, SEMAFORO_ROJO),
        (-30, ESTADO_POR_HACER, SEMAFORO_ROJO),
        (-1, ESTADO_COMPLETADO, SEMAFORO_GRIS),
        (30, ESTADO_COMPLETADO, SEMAFORO_GRIS),
    ],
)
def test_rg11_uses_natural_days(dias, estado, esperado):
    hoy = date(2026, 11, 2)

    assert calcular_semaforo(estado, hoy + timedelta(days=dias), hoy) == esperado


# ---------------------------------------------------------------------------
# Listado de tareas
# ---------------------------------------------------------------------------
def test_list_shows_the_color_of_each_task(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    colores = _colores(res)
    assert colores[escenario.tareas["vencida"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["hoy"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["manana"].id] == SEMAFORO_AMARILLO
    assert colores[escenario.tareas["dos_dias"].id] == SEMAFORO_AMARILLO
    assert colores[escenario.tareas["tres_dias"].id] == SEMAFORO_VERDE
    assert colores[escenario.tareas["verde_lejos"].id] == SEMAFORO_VERDE
    assert colores[escenario.tareas["completada"].id] == SEMAFORO_GRIS


def test_list_includes_remaining_days(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    dias = {item["id"]: item["dias_restantes"] for item in res.get_json()["data"]}
    assert dias[escenario.tareas["vencida"].id] == -2
    assert dias[escenario.tareas["hoy"].id] == 0
    assert dias[escenario.tareas["manana"].id] == 1
    assert dias[escenario.tareas["dos_dias"].id] == 2


# ---------------------------------------------------------------------------
# Detalle de tarea
# ---------------------------------------------------------------------------
def test_detail_shows_the_color_and_remaining_days(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tareas['manana'].id}", headers=auth_headers(escenario.admin)
    )

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["semaforo"] == SEMAFORO_AMARILLO
    assert data["dias_restantes"] == 1


def test_completed_task_is_gray_in_the_detail(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tareas['completada'].id}",
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["semaforo"] == SEMAFORO_GRIS


# ---------------------------------------------------------------------------
# Tablero Kanban
# ---------------------------------------------------------------------------
def test_board_shows_the_color_on_each_card(client, auth_headers, escenario):
    res = client.get(f"{URL}/board", headers=auth_headers(escenario.admin))

    assert res.status_code == 200
    columnas = {columna["estado"]: columna for columna in res.get_json()["data"]["columnas"]}
    assert _tarjeta(columnas, escenario.tareas["vencida"].id)["semaforo"] == SEMAFORO_ROJO
    assert _tarjeta(columnas, escenario.tareas["manana"].id)["semaforo"] == SEMAFORO_AMARILLO
    assert _tarjeta(columnas, escenario.tareas["tres_dias"].id)["semaforo"] == SEMAFORO_VERDE
    assert _tarjeta(columnas, escenario.tareas["completada"].id)["semaforo"] == SEMAFORO_GRIS


# ---------------------------------------------------------------------------
# Alcance del Contador (RG-12)
# ---------------------------------------------------------------------------
def test_accountant_only_sees_the_color_of_his_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert res.status_code == 200
    colores = _colores(res)
    assert set(colores) == {
        escenario.tareas["vencida"].id,
        escenario.tareas["hoy"].id,
        escenario.tareas["manana"].id,
        escenario.tareas["verde_lejos"].id,
        escenario.tareas["completada"].id,
    }
    assert colores[escenario.tareas["vencida"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["completada"].id] == SEMAFORO_GRIS


# ---------------------------------------------------------------------------
# Actualización al editar la fecha límite o cambiar el día
# ---------------------------------------------------------------------------
def test_color_changes_when_the_deadline_is_edited(client, auth_headers, escenario):
    tarea = escenario.tareas["vencida"]

    res = client.put(
        f"{URL}/{tarea.id}",
        json={"fecha_limite": (escenario.hoy + timedelta(days=5)).isoformat()},
        headers=auth_headers(escenario.admin),
    )

    assert res.status_code == 200
    assert res.get_json()["data"]["semaforo"] == SEMAFORO_VERDE
    assert _colores(client.get(URL, headers=auth_headers(escenario.admin)))[tarea.id] == (
        SEMAFORO_VERDE
    )


def test_color_changes_when_the_day_changes(
    client, auth_headers, escenario, monkeypatch
):
    """Al pasar la medianoche, el mismo registro cambia de color (RG-11)."""
    manana = escenario.hoy + timedelta(days=1)
    monkeypatch.setattr(task_service, "today_mx", lambda: manana)

    res = client.get(URL, headers=auth_headers(escenario.admin))

    colores = _colores(res)
    assert colores[escenario.tareas["manana"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["hoy"].id] == SEMAFORO_ROJO
    assert colores[escenario.tareas["dos_dias"].id] == SEMAFORO_AMARILLO

    detalle = client.get(
        f"{URL}/{escenario.tareas['manana'].id}", headers=auth_headers(escenario.admin)
    )
    assert detalle.get_json()["data"]["semaforo"] == SEMAFORO_ROJO
    assert detalle.get_json()["data"]["dias_restantes"] == 0
