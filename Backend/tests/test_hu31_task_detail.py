"""HU_31: Consultar detalle de tarea."""
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

import pytest

from app.core.datetime_utils import today_mx, utcnow
from app.core.semaforo import SEMAFORO_AMARILLO, SEMAFORO_GRIS
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import (
    Comentario,
    HistorialEstadoTarea,
    Subtarea,
    Tarea,
)
from app.models.time_entry import RegistroTiempo

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
    creador,
    fecha_limite: date,
    estado: str = "EN_PROGRESO",
    prioridad: str = "ALTA",
    horas_estimadas: float | None = 4.0,
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Descripción completa de la tarea",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        obligacion_id=123,
        periodo="2026-10",
        fecha_limite=fecha_limite,
        hora_limite=time(15, 30),
        prioridad=prioridad,
        estado=estado,
        horas_estimadas=horas_estimadas,
        notificar_cliente=True,
        cliente_notificado=False,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def _crear_subtarea(
    tarea: Tarea,
    titulo: str,
    *,
    completada: bool = False,
    completada_por=None,
    completada_en: datetime | None = None,
    created_at: datetime | None = None,
) -> Subtarea:
    subtarea = Subtarea(
        tarea_id=tarea.id,
        titulo=titulo,
        completada=completada,
        completada_por=completada_por.id if completada_por else None,
        completada_en=completada_en,
        created_at=created_at or utcnow(),
    )
    db.session.add(subtarea)
    db.session.commit()
    return subtarea


def _crear_comentario(
    tarea: Tarea,
    autor,
    texto: str,
    *,
    editado: bool = False,
    created_at: datetime | None = None,
) -> Comentario:
    comentario = Comentario(
        tarea_id=tarea.id,
        autor_id=autor.id,
        texto=texto,
        editado=editado,
        created_at=created_at or utcnow(),
        created_by=autor.id,
    )
    db.session.add(comentario)
    db.session.commit()
    return comentario


def _crear_historial(
    tarea: Tarea,
    *,
    estado_anterior: str | None,
    estado_nuevo: str,
    usuario,
    created_at: datetime,
) -> HistorialEstadoTarea:
    historial = HistorialEstadoTarea(
        tarea_id=tarea.id,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario_id=usuario.id,
        created_at=created_at,
    )
    db.session.add(historial)
    db.session.commit()
    return historial


def _crear_tiempo(
    tarea: Tarea,
    colaborador,
    minutos: int,
    *,
    fecha: date | None = None,
) -> RegistroTiempo:
    registro = RegistroTiempo(
        tarea_id=tarea.id,
        colaborador_id=colaborador.id,
        fecha=fecha or today_mx(),
        duracion_minutos=minutos,
        tipo="MANUAL",
        descripcion="Registro de apoyo",
        nivel_escalafon=colaborador.grado_escalafon,
        created_by=colaborador.id,
    )
    db.session.add(registro)
    db.session.commit()
    return registro


@pytest.fixture()
def escenario(make_user):
    admin = make_user("admin.detalle@despacho.com", "ADMINISTRADOR", nombre="Admin Tareas")
    contador1 = make_user("ana.detalle@despacho.com", "CONTADOR", nombre="Ana Contadora")
    contador2 = make_user("beto.detalle@despacho.com", "CONTADOR", nombre="Beto Contador")
    coordinador = make_user(
        "carla.detalle@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    dueno = make_user("dora.detalle@despacho.com", "DUENO", nombre="Dora Dueña")

    cliente = _crear_cliente(contador1, "Cliente Detalle", "XDet010101000")
    fiscal = _crear_categoria("Fiscal")
    declaraciones = _crear_categoria("Declaraciones", padre=fiscal)

    hoy = today_mx()
    tarea = _crear_tarea(
        titulo="Declaración anual del cliente",
        cliente=cliente,
        categoria=declaraciones,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=2),
    )

    base = datetime(2026, 10, 20, 8, 0, tzinfo=timezone.utc)
    _crear_subtarea(
        tarea,
        "Recopilar documentos",
        completada=True,
        completada_por=contador1,
        completada_en=base + timedelta(hours=2),
        created_at=base,
    )
    _crear_subtarea(tarea, "Calcular impuestos", created_at=base + timedelta(minutes=1))
    sub_eliminada = _crear_subtarea(
        tarea, "Paso cancelado", created_at=base + timedelta(minutes=2)
    )
    sub_eliminada.deleted_at = utcnow()

    _crear_comentario(
        tarea,
        admin,
        "Revisar el cálculo antes de enviar",
        created_at=base + timedelta(hours=3),
    )
    _crear_comentario(
        tarea,
        contador1,
        "Cálculo revisado y listo",
        editado=True,
        created_at=base + timedelta(hours=4),
    )
    comentario_eliminado = _crear_comentario(
        tarea,
        contador2,
        "Comentario retirado",
        created_at=base + timedelta(hours=5),
    )
    comentario_eliminado.deleted_at = utcnow()

    _crear_historial(
        tarea,
        estado_anterior=None,
        estado_nuevo="POR_HACER",
        usuario=admin,
        created_at=base,
    )
    _crear_historial(
        tarea,
        estado_anterior="POR_HACER",
        estado_nuevo="EN_PROGRESO",
        usuario=contador1,
        created_at=base + timedelta(hours=1),
    )

    _crear_tiempo(tarea, contador1, 60)
    _crear_tiempo(tarea, contador2, 30)
    tiempo_eliminado = _crear_tiempo(tarea, contador1, 120)
    tiempo_eliminado.deleted_at = utcnow()

    db.session.commit()

    return SimpleNamespace(
        admin=admin,
        contador1=contador1,
        contador2=contador2,
        coordinador=coordinador,
        dueno=dueno,
        cliente=cliente,
        fiscal=fiscal,
        declaraciones=declaraciones,
        tarea=tarea,
        hoy=hoy,
    )


# ---------------------------------------------------------------------------
# Acceso y alcance (RG-02 / RG-12)
# ---------------------------------------------------------------------------
def test_requires_authentication(client, escenario):
    assert client.get(f"{URL}/{escenario.tarea.id}").status_code == 401


@pytest.mark.parametrize("actor", ["dueno", "admin", "coordinador", "contador1"])
def test_all_roles_with_access_can_view_detail(client, auth_headers, escenario, actor):
    res = client.get(
        f"{URL}/{escenario.tarea.id}",
        headers=auth_headers(getattr(escenario, actor)),
    )
    assert res.status_code == 200


def test_accountant_can_view_task_created_by_him(client, auth_headers, escenario):
    tarea = _crear_tarea(
        titulo="Tarea creada por contador",
        cliente=escenario.cliente,
        categoria=escenario.declaraciones,
        asignado=escenario.contador2,
        creador=escenario.contador1,
        fecha_limite=escenario.hoy + timedelta(days=3),
    )

    res = client.get(f"{URL}/{tarea.id}", headers=auth_headers(escenario.contador1))
    assert res.status_code == 200
    assert res.get_json()["data"]["id"] == tarea.id


def test_accountant_cannot_view_other_task(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}",
        headers=auth_headers(escenario.contador2),
    )
    assert res.status_code == 403
    body = res.get_json()
    assert body["error"]["code"] == "FORBIDDEN"
    assert body["error"]["message"] == "No tienes permiso para esta acción"
    assert "data" not in body


def test_nonexistent_task_returns_404(client, auth_headers, escenario):
    res = client.get(f"{URL}/999999", headers=auth_headers(escenario.admin))
    assert res.status_code == 404
    assert res.get_json()["error"]["message"] == "Tarea no encontrada"


def test_deleted_task_returns_404(client, auth_headers, escenario):
    escenario.tarea.deleted_at = utcnow()
    db.session.commit()

    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    assert res.status_code == 404


# ---------------------------------------------------------------------------
# Contenido del detalle
# ---------------------------------------------------------------------------
def test_detail_returns_all_task_fields(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    assert res.status_code == 200
    data = res.get_json()["data"]

    assert set(data) == {
        "id", "titulo", "descripcion", "cliente_id", "cliente_nombre",
        "categoria_id", "categoria_nombre", "categoria_padre_nombre",
        "asignado_id", "asignado_nombre", "creador_id", "creador_nombre",
        "obligacion_id", "periodo", "fecha_limite", "hora_limite",
        "prioridad", "estado", "horas_estimadas", "notificar_cliente",
        "cliente_notificado", "completada_en", "completada_por",
        "completada_por_nombre", "created_by", "updated_by", "created_at",
        "updated_at", "semaforo", "dias_restantes", "subtareas",
        "comentarios", "historial_estados", "tiempo",
    }
    assert data["titulo"] == "Declaración anual del cliente"
    assert data["descripcion"] == "Descripción completa de la tarea"
    assert data["cliente_nombre"] == "Cliente Detalle"
    assert data["categoria_nombre"] == "Declaraciones"
    assert data["categoria_padre_nombre"] == "Fiscal"
    assert data["asignado_nombre"] == "Ana Contadora"
    assert data["creador_id"] == escenario.admin.id
    assert data["creador_nombre"] == "Admin Tareas"
    assert data["obligacion_id"] == 123
    assert data["periodo"] == "2026-10"
    assert data["hora_limite"] == "15:30"
    assert data["horas_estimadas"] == 4.0
    assert data["notificar_cliente"] is True
    assert data["cliente_notificado"] is False
    assert data["semaforo"] == SEMAFORO_AMARILLO
    assert data["dias_restantes"] == 2
    assert data["created_at"] is not None
    assert data["updated_at"] is not None


def test_completed_task_has_gray_semaforo_and_completer(client, auth_headers, escenario):
    escenario.tarea.estado = "COMPLETADO"
    escenario.tarea.completada_por = escenario.contador1.id
    escenario.tarea.completada_en = utcnow()
    db.session.commit()

    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    data = res.get_json()["data"]

    assert res.status_code == 200
    assert data["semaforo"] == SEMAFORO_GRIS
    assert data["completada_por"] == escenario.contador1.id
    assert data["completada_por_nombre"] == "Ana Contadora"
    assert data["completada_en"] is not None


def test_subtasks_include_progress_and_exclude_deleted(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    subtareas = res.get_json()["data"]["subtareas"]

    assert [s["titulo"] for s in subtareas["items"]] == [
        "Recopilar documentos",
        "Calcular impuestos",
    ]
    assert subtareas["total"] == 2
    assert subtareas["completadas"] == 1
    assert subtareas["avance"] == "1/2"
    assert subtareas["porcentaje"] == 50.0
    assert subtareas["items"][0]["completada_por_nombre"] == "Ana Contadora"
    assert subtareas["items"][0]["completada_en"] is not None


def test_comments_include_author_and_exclude_deleted(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    comentarios = res.get_json()["data"]["comentarios"]

    assert [c["texto"] for c in comentarios] == [
        "Revisar el cálculo antes de enviar",
        "Cálculo revisado y listo",
    ]
    assert comentarios[0]["autor_nombre"] == "Admin Tareas"
    assert comentarios[1]["autor_nombre"] == "Ana Contadora"
    assert comentarios[1]["editado"] is True
    assert comentarios[0]["created_at"] is not None


def test_status_history_includes_who_and_when(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    historial = res.get_json()["data"]["historial_estados"]

    assert len(historial) == 2
    assert historial[0]["estado_anterior"] is None
    assert historial[0]["estado_nuevo"] == "POR_HACER"
    assert historial[0]["usuario_nombre"] == "Admin Tareas"
    assert historial[1]["estado_anterior"] == "POR_HACER"
    assert historial[1]["estado_nuevo"] == "EN_PROGRESO"
    assert historial[1]["usuario_nombre"] == "Ana Contadora"
    assert historial[1]["created_at"] is not None


def test_time_summary_compares_registered_vs_estimated(client, auth_headers, escenario):
    res = client.get(
        f"{URL}/{escenario.tarea.id}", headers=auth_headers(escenario.admin)
    )
    tiempo = res.get_json()["data"]["tiempo"]

    assert tiempo["total_minutos"] == 90  # 120 minutos eliminados no cuentan
    assert tiempo["total_horas"] == 1.5
    assert tiempo["horas_estimadas"] == 4.0
    assert tiempo["porcentaje_registrado"] == 37.5
    assert [
        (t["colaborador_nombre"], t["minutos"], t["horas"])
        for t in tiempo["por_colaborador"]
    ] == [
        ("Ana Contadora", 60, 1.0),
        ("Beto Contador", 30, 0.5),
    ]


def test_detail_without_subtasks_comments_time_or_estimate(
    client, auth_headers, escenario
):
    tarea = _crear_tarea(
        titulo="Tarea recién creada",
        cliente=escenario.cliente,
        categoria=escenario.fiscal,
        asignado=escenario.contador1,
        creador=escenario.admin,
        fecha_limite=escenario.hoy,
        estado="POR_HACER",
        horas_estimadas=None,
    )

    res = client.get(f"{URL}/{tarea.id}", headers=auth_headers(escenario.admin))
    data = res.get_json()["data"]

    assert res.status_code == 200
    assert data["subtareas"] == {
        "items": [],
        "total": 0,
        "completadas": 0,
        "avance": "0/0",
        "porcentaje": 0.0,
    }
    assert data["comentarios"] == []
    assert data["historial_estados"] == []
    assert data["tiempo"] == {
        "total_minutos": 0,
        "total_horas": 0.0,
        "horas_estimadas": None,
        "porcentaje_registrado": None,
        "por_colaborador": [],
    }
