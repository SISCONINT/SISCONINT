"""Datos de apoyo para las pruebas de HU_49-53 (módulo 8)."""
from datetime import date, datetime

from app.core.datetime_utils import today_mx
from app.extensions import db
from app.models.catalog import CategoriaProyecto
from app.models.client import Cliente
from app.models.task import Tarea
from app.models.time_entry import TIPO_MANUAL, RegistroTiempo, TemporizadorActivo


def crear_cliente(
    contador,
    nombre: str = "Cliente Tiempos",
    rfc: str = "XTIM010101000",
) -> Cliente:
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


def crear_categoria(nombre: str, padre: CategoriaProyecto | None = None) -> CategoriaProyecto:
    categoria = CategoriaProyecto(
        nombre=nombre,
        padre_id=padre.id if padre else None,
        activa=True,
        orden=0,
    )
    db.session.add(categoria)
    db.session.commit()
    return categoria


def crear_tarea(
    *,
    titulo: str,
    cliente: Cliente,
    categoria: CategoriaProyecto,
    asignado,
    creador,
    fecha_limite: date,
    estado: str = "EN_PROGRESO",
) -> Tarea:
    tarea = Tarea(
        titulo=titulo,
        descripcion="Tarea de apoyo para las pruebas de tiempo",
        cliente_id=cliente.id,
        categoria_id=categoria.id,
        asignado_id=asignado.id,
        creador_id=creador.id,
        fecha_limite=fecha_limite,
        hora_limite=datetime.strptime("23:59", "%H:%M").time(),
        prioridad="ALTA",
        estado=estado,
        horas_estimadas=4.0,
        notificar_cliente=True,
        cliente_notificado=False,
        created_by=creador.id,
        updated_by=creador.id,
    )
    db.session.add(tarea)
    db.session.commit()
    return tarea


def crear_registro(
    tarea: Tarea,
    colaborador,
    *,
    fecha: date | None = None,
    minutos: int = 60,
    descripcion: str = "Trabajo registrado",
    tipo: str = TIPO_MANUAL,
    cierre_automatico: bool = False,
) -> RegistroTiempo:
    registro = RegistroTiempo(
        tarea_id=tarea.id,
        colaborador_id=colaborador.id,
        fecha=fecha or today_mx(),
        duracion_minutos=minutos,
        tipo=tipo,
        descripcion=descripcion,
        nivel_escalafon=colaborador.grado_escalafon,
        cierre_automatico=cierre_automatico,
        created_by=colaborador.id,
    )
    db.session.add(registro)
    db.session.commit()
    return registro


def crear_temporizador(
    colaborador,
    tarea: Tarea,
    iniciado_en: datetime,
) -> TemporizadorActivo:
    temporizador = TemporizadorActivo(
        colaborador_id=colaborador.id,
        tarea_id=tarea.id,
        iniciado_en=iniciado_en,
    )
    db.session.add(temporizador)
    db.session.commit()
    return temporizador
