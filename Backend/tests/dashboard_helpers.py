"""Datos de apoyo para las pruebas del dashboard (módulo 12)."""
from datetime import timedelta
from types import SimpleNamespace

from app.core.datetime_utils import today_mx
from tests.time_helpers import (
    crear_categoria,
    crear_cliente,
    crear_registro,
    crear_tarea,
)


def crear_escenario(make_user) -> SimpleNamespace:
    """Despacho con dos clientes, tres categorías, cinco tareas y tres registros.

    Los registros de hoy suman 180 minutos: 120 del contador1 y 60 del contador2.
    """
    dueno = make_user("dora.dashboard@despacho.com", "DUENO", nombre="Dora Dueña")
    admin = make_user(
        "admin.dashboard@despacho.com", "ADMINISTRADOR", nombre="Admin Dashboard"
    )
    coordinador = make_user(
        "carla.dashboard@despacho.com", "COORDINADOR", nombre="Carla Coordinadora"
    )
    contador1 = make_user(
        "ana.dashboard@despacho.com", "CONTADOR", nombre="Ana Contadora"
    )
    contador2 = make_user(
        "beto.dashboard@despacho.com", "CONTADOR", nombre="Beto Contador"
    )
    contador3 = make_user(
        "cora.dashboard@despacho.com", "CONTADOR", nombre="Cora Sin Datos"
    )

    cliente1 = crear_cliente(contador1, "Cliente Uno", "XDB010101000")
    cliente2 = crear_cliente(contador2, "Cliente Dos", "XDB010101001")
    cliente3 = crear_cliente(contador3, "Cliente Sin Datos", "XDB010101002")

    fiscal = crear_categoria("Fiscal")
    fiscal_sub = crear_categoria("Declaraciones", padre=fiscal)
    laboral = crear_categoria("Laboral")
    crear_categoria("Sin horas")

    hoy = today_mx()
    ayer = hoy - timedelta(days=1)

    tarea1 = crear_tarea(
        titulo="Declaración mensual",
        cliente=cliente1,
        categoria=fiscal_sub,
        asignado=contador1,
        creador=admin,
        fecha_limite=hoy + timedelta(days=5),
        estado="EN_PROGRESO",
    )
    tarea2 = crear_tarea(
        titulo="Pago vencido",
        cliente=cliente1,
        categoria=fiscal,
        asignado=contador1,
        creador=admin,
        fecha_limite=ayer,
        estado="POR_HACER",
    )
    tarea3 = crear_tarea(
        titulo="Nómina",
        cliente=cliente2,
        categoria=laboral,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy + timedelta(days=2),
        estado="EN_REVISION",
    )
    tarea4 = crear_tarea(
        titulo="Terminada vencida",
        cliente=cliente2,
        categoria=laboral,
        asignado=contador2,
        creador=admin,
        fecha_limite=ayer,
        estado="COMPLETADO",
    )
    tarea5 = crear_tarea(
        titulo="Terminada hoy",
        cliente=cliente1,
        categoria=fiscal,
        asignado=contador2,
        creador=admin,
        fecha_limite=hoy,
        estado="COMPLETADO",
    )

    registro1 = crear_registro(
        tarea1, contador1, fecha=hoy, minutos=90, descripcion="Declaración"
    )
    registro2 = crear_registro(
        tarea2, contador1, fecha=hoy, minutos=30, descripcion="Pago"
    )
    registro3 = crear_registro(
        tarea3, contador2, fecha=hoy, minutos=60, descripcion="Nómina"
    )

    return SimpleNamespace(
        dueno=dueno,
        admin=admin,
        coordinador=coordinador,
        contador1=contador1,
        contador2=contador2,
        contador3=contador3,
        cliente1=cliente1,
        cliente2=cliente2,
        cliente3=cliente3,
        fiscal=fiscal,
        fiscal_sub=fiscal_sub,
        laboral=laboral,
        tarea1=tarea1,
        tarea2=tarea2,
        tarea3=tarea3,
        tarea4=tarea4,
        tarea5=tarea5,
        registro1=registro1,
        registro2=registro2,
        registro3=registro3,
        hoy=hoy,
        ayer=ayer,
    )
