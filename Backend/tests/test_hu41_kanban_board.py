"""HU_41: Visualizar tablero Kanban."""
import re
from datetime import date, datetime, time, timedelta
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.core.semaforo import (
    SEMAFORO_AMARILLO,
    SEMAFORO_GRIS,
    SEMAFORO_ROJO,
    SEMAFORO_VERDE,
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
from app.models.time_entry import RegistroTiempo

URL = "/api/v1/tasks/board"
COLUMNAS = ("POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO")


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


def _columnas(res) -> dict[str, dict]:
    return {columna["estado"]: columna for columna in res.get_json()["data"]["columnas"]}


def _ids(columna: dict) -> list[int]:
    return [tarea["id"] for tarea in columna["tareas"]]


def _tarjeta(columnas: dict[str, dict], tarea: Tarea) -> dict:
    for columna in columnas.values():
        for tarjeta in columna["tareas"]:
            if tarjeta["id"] == tarea.id:
                return tarjeta
    raise AssertionError(f"La tarea {tarea.id} no está en el tablero")


@pytest.fixture()
def escenario(make_user):
    dueno = make_user("dora.tablero@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user("admin.tablero@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.tablero@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.tablero@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.tablero@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )

    cliente = _crear_cliente(contador1, "Cliente Kanban", "XKan010101000")
    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)
    hoy = today_mx()

    por_hacer = _crear_tarea(
        titulo="Declaración anual",
        cliente=cliente,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
        estado=ESTADO_POR_HACER,
        prioridad="ALTA",
        horas_estimadas=4.0,
    )
    en_progreso = _crear_tarea(
        titulo="Conciliación bancaria",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=1),
        estado=ESTADO_EN_PROGRESO,
        prioridad="MEDIA",
        horas_estimadas=None,
    )
    en_revision = _crear_tarea(
        titulo="Revisión de nómina",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy,
        estado=ESTADO_EN_REVISION,
        prioridad="BAJA",
        horas_estimadas=2.0,
    )
    completada = _crear_tarea(
        titulo="Cierre mensual",
        cliente=cliente,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy - timedelta(days=2),
        estado=ESTADO_COMPLETADO,
        prioridad="ALTA",
        horas_estimadas=4.0,
        completada_en=utcnow() - timedelta(days=5),
    )
    completada_vieja = _crear_tarea(
        titulo="Cierre de hace un mes",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy - timedelta(days=40),
        estado=ESTADO_COMPLETADO,
        prioridad="MEDIA",
        horas_estimadas=1.0,
        completada_en=utcnow() - timedelta(days=31),
    )
    ajena = _crear_tarea(
        titulo="Tarea de otro contador",
        cliente=cliente,
        categoria=fiscal,
        asignado=contador2,
        creador=coordinador,
        fecha_limite=hoy + timedelta(days=2),
        estado=ESTADO_POR_HACER,
        prioridad="BAJA",
        horas_estimadas=2.0,
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
        por_hacer=por_hacer,
        en_progreso=en_progreso,
        en_revision=en_revision,
        completada=completada,
        completada_vieja=completada_vieja,
        ajena=ajena,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso (RG-02 / RG-12)
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(URL).status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador", "contador1"])
def test_all_roles_can_open_the_board(client, auth_headers, escenario, actor):
    res = client.get(URL, headers=auth_headers(getattr(escenario, actor)))

    assert res.status_code == 200
    columnas = _columnas(res)
    assert tuple(columnas) == COLUMNAS


def test_management_sees_everyones_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    columnas = _columnas(res)
    assert escenario.ajena.id in _ids(columnas[ESTADO_POR_HACER])
    assert res.get_json()["data"]["total_tareas"] == 5


def test_accountant_only_sees_his_tasks(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador1))

    data = res.get_json()["data"]
    columnas = _columnas(res)
    assert data["total_tareas"] == 4
    assert escenario.ajena.id not in _ids(columnas[ESTADO_POR_HACER])
    assert {columna: len(columnas[columna]["tareas"]) for columna in COLUMNAS} == {
        ESTADO_POR_HACER: 1,
        ESTADO_EN_PROGRESO: 1,
        ESTADO_EN_REVISION: 1,
        ESTADO_COMPLETADO: 1,
    }


def test_accountant_sees_tasks_he_created_for_someone_else(
    client, auth_headers, escenario
):
    creada = _crear_tarea(
        titulo="Tarea creada por la contadora",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador2,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=3),
    )

    res = client.get(URL, headers=auth_headers(escenario.contador1))

    assert creada.id in _ids(_columnas(res)[ESTADO_POR_HACER])


def test_other_accountant_only_sees_his_task(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.contador2))

    data = res.get_json()["data"]
    columnas = _columnas(res)
    assert data["total_tareas"] == 1
    assert _ids(columnas[ESTADO_POR_HACER]) == [escenario.ajena.id]
    assert _ids(columnas[ESTADO_EN_PROGRESO]) == []
    assert _ids(columnas[ESTADO_EN_REVISION]) == []
    assert _ids(columnas[ESTADO_COMPLETADO]) == []


# ---------------------------------------------------------------------------
# Columnas fijas y contadores
# ---------------------------------------------------------------------------
def test_four_fixed_columns_with_titles_and_counts(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    columnas = res.get_json()["data"]["columnas"]
    assert [(columna["titulo"], columna["total"]) for columna in columnas] == [
        ("Por hacer", 2),
        ("En progreso", 1),
        ("En revisión", 1),
        ("Completado", 1),
    ]
    assert res.get_json()["data"]["total_tareas"] == 5


def test_each_task_appears_in_exactly_one_column(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    columnas = _columnas(res)
    ids = [tarea["id"] for columna in columnas.values() for tarea in columna["tareas"]]
    assert len(ids) == len(set(ids))
    assert sum(columna["total"] for columna in columnas.values()) == len(ids)


def test_deleted_tasks_are_not_shown(client, auth_headers, escenario):
    escenario.por_hacer.deleted_at = utcnow()
    db.session.commit()

    res = client.get(URL, headers=auth_headers(escenario.admin))

    data = res.get_json()["data"]
    columnas = _columnas(res)
    assert escenario.por_hacer.id not in _ids(columnas[ESTADO_POR_HACER])
    assert data["total_tareas"] == 4


def test_empty_board_keeps_the_four_columns(client, auth_headers, make_user):
    admin = make_user("admin.vacio@despacho.com", "ADMINISTRADOR", nombre="Admin Vacío")

    res = client.get(URL, headers=auth_headers(admin))

    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["total_tareas"] == 0
    assert [(columna["estado"], columna["total"]) for columna in data["columnas"]] == [
        (estado, 0) for estado in COLUMNAS
    ]
    assert all(columna["tareas"] == [] for columna in data["columnas"])


# ---------------------------------------------------------------------------
# Contenido de la tarjeta
# ---------------------------------------------------------------------------
def test_card_shows_the_fields_required_by_hu_41(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    tarjeta = _tarjeta(_columnas(res), escenario.por_hacer)
    assert tarjeta["id"] == escenario.por_hacer.id
    assert tarjeta["titulo"] == "Declaración anual"
    assert tarjeta["cliente_id"] == escenario.cliente.id
    assert tarjeta["cliente_nombre"] == "Cliente Kanban"
    assert tarjeta["asignado_id"] == escenario.contador1.id
    assert tarjeta["asignado_nombre"] == "Ana Contadora"
    assert tarjeta["prioridad"] == "ALTA"
    assert tarjeta["estado"] == ESTADO_POR_HACER
    assert tarjeta["hora_limite"] == "15:30"
    assert tarjeta["semaforo"] == SEMAFORO_VERDE


def test_card_dates_travel_in_iso_8601(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    tarjeta = _tarjeta(_columnas(res), escenario.completada)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", tarjeta["fecha_limite"])
    assert datetime.fromisoformat(tarjeta["completada_en"]) is not None


@pytest.mark.parametrize(
    ("tarea", "semaforo"),
    [
        ("por_hacer", SEMAFORO_VERDE),
        ("en_progreso", SEMAFORO_AMARILLO),
        ("en_revision", SEMAFORO_ROJO),
        ("completada", SEMAFORO_GRIS),
    ],
)
def test_semaforo_is_calculated_on_the_server(
    client, auth_headers, escenario, tarea, semaforo
):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert _tarjeta(_columnas(res), getattr(escenario, tarea))["semaforo"] == semaforo


def test_card_shows_registered_and_estimated_hours(client, auth_headers, escenario):
    _crear_tiempo(escenario.por_hacer, escenario.contador1, 90)
    _crear_tiempo(escenario.por_hacer, escenario.contador1, 30)

    res = client.get(URL, headers=auth_headers(escenario.admin))

    tarjeta = _tarjeta(_columnas(res), escenario.por_hacer)
    assert tarjeta["minutos_registrados"] == 120
    assert tarjeta["horas_registradas"] == 2.0
    assert tarjeta["horas_estimadas"] == 4.0
    assert tarjeta["porcentaje_registrado"] == 50.0


def test_card_without_time_or_estimate(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    tarjeta = _tarjeta(_columnas(res), escenario.en_progreso)
    assert tarjeta["minutos_registrados"] == 0
    assert tarjeta["horas_registradas"] == 0.0
    assert tarjeta["horas_estimadas"] is None
    assert tarjeta["porcentaje_registrado"] is None


def test_deleted_time_entries_are_not_counted(client, auth_headers, escenario):
    registro = _crear_tiempo(escenario.por_hacer, escenario.contador1, 120)
    registro.deleted_at = utcnow()
    db.session.commit()

    res = client.get(URL, headers=auth_headers(escenario.admin))

    tarjeta = _tarjeta(_columnas(res), escenario.por_hacer)
    assert tarjeta["minutos_registrados"] == 0
    assert tarjeta["porcentaje_registrado"] == 0.0


# ---------------------------------------------------------------------------
# Columna Completado (últimos 30 días) y orden
# ---------------------------------------------------------------------------
def test_completed_column_only_shows_the_last_30_days(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    completadas = _ids(_columnas(res)[ESTADO_COMPLETADO])
    assert completadas == [escenario.completada.id]
    assert escenario.completada_vieja.id not in completadas


def test_completed_cards_are_ordered_most_recent_first(client, auth_headers, escenario):
    reciente = _crear_tarea(
        titulo="Cierre más reciente",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.admin,
        fecha_limite=escenario.hoy,
        estado=ESTADO_COMPLETADO,
        completada_en=utcnow() - timedelta(days=2),
    )

    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert _ids(_columnas(res)[ESTADO_COMPLETADO]) == [reciente.id, escenario.completada.id]


def test_completed_task_without_closing_date_is_not_shown(
    client, auth_headers, escenario
):
    sin_fecha = _crear_tarea(
        titulo="Completada sin fecha de cierre",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.admin,
        fecha_limite=escenario.hoy,
        estado=ESTADO_COMPLETADO,
        completada_en=None,
    )

    res = client.get(URL, headers=auth_headers(escenario.admin))

    assert sin_fecha.id not in _ids(_columnas(res)[ESTADO_COMPLETADO])


def test_open_cards_are_ordered_by_deadline(client, auth_headers, escenario):
    res = client.get(URL, headers=auth_headers(escenario.admin))

    # "ajena" vence en 2 días y "por_hacer" en 5: primero lo más urgente.
    assert _ids(_columnas(res)[ESTADO_POR_HACER]) == [
        escenario.ajena.id,
        escenario.por_hacer.id,
    ]
