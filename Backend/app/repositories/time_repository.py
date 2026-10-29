"""HU_49-53. Acceso a datos del registro de tiempos."""
from datetime import date

from sqlalchemy import func, select

from app.extensions import db
from app.models.client import Cliente
from app.models.task import Tarea
from app.models.time_entry import RegistroTiempo, TemporizadorActivo
from app.models.user import Colaborador


# ---------------------------------------------------------------------------
# Temporizador activo (HU_49-50)
# ---------------------------------------------------------------------------
def get_active_for_user(
    colaborador_id: int, *, for_update: bool = False
) -> TemporizadorActivo | None:
    stmt = select(TemporizadorActivo).where(
        TemporizadorActivo.colaborador_id == colaborador_id,
    )
    if for_update:
        # Evita que dos peticiones detengan el mismo temporizador a la vez.
        stmt = stmt.with_for_update()
    return db.session.execute(stmt).scalar_one_or_none()


def add_timer(temporizador: TemporizadorActivo) -> TemporizadorActivo:
    db.session.add(temporizador)
    db.session.flush()
    return temporizador


def delete_timer(temporizador: TemporizadorActivo) -> None:
    db.session.delete(temporizador)


def get_timer_detail(temporizador_id: int) -> dict | None:
    """Temporizador con el nombre de la tarea y del cliente (para la pantalla del timer)."""
    stmt = (
        select(
            TemporizadorActivo.id,
            TemporizadorActivo.tarea_id,
            TemporizadorActivo.iniciado_en,
            Tarea.titulo,
            Cliente.id,
            Cliente.nombre_completo,
        )
        .join(Tarea, Tarea.id == TemporizadorActivo.tarea_id)
        .join(Cliente, Cliente.id == Tarea.cliente_id)
        .where(TemporizadorActivo.id == temporizador_id)
    )
    row = db.session.execute(stmt).first()
    if row is None:
        return None

    return {
        "id": row[0],
        "tarea_id": row[1],
        "iniciado_en": row[2],
        "tarea_titulo": row[3],
        "cliente_id": row[4],
        "cliente_nombre": row[5],
    }


# ---------------------------------------------------------------------------
# Registros de tiempo (HU_50-53)
# ---------------------------------------------------------------------------
def add_registro(registro: RegistroTiempo) -> RegistroTiempo:
    db.session.add(registro)
    db.session.flush()
    return registro


def get_by_id(registro_id: int) -> RegistroTiempo | None:
    """Registro no eliminado (el servicio aplica el alcance de HU_53)."""
    stmt = select(RegistroTiempo).where(
        RegistroTiempo.id == registro_id,
        RegistroTiempo.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def sum_minutes_for_day(
    colaborador_id: int,
    fecha: date,
    exclude_id: int | None = None,
) -> int:
    """Minutos ya registrados por el colaborador en un día (HU_51: límite de 24 h)."""
    stmt = select(func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0)).where(
        RegistroTiempo.colaborador_id == colaborador_id,
        RegistroTiempo.fecha == fecha,
        RegistroTiempo.deleted_at.is_(None),
    )
    if exclude_id is not None:
        stmt = stmt.where(RegistroTiempo.id != exclude_id)
    return int(db.session.execute(stmt).scalar_one())


def _detail_stmt():
    """Registro con empleado, cliente y tarea resueltos."""
    return (
        select(
            RegistroTiempo,
            Colaborador.nombre_completo.label("empleado_nombre"),
            Cliente.id.label("cliente_id"),
            Cliente.nombre_completo.label("cliente_nombre"),
            Tarea.titulo.label("tarea_titulo"),
        )
        .join(Colaborador, Colaborador.id == RegistroTiempo.colaborador_id)
        .join(Tarea, Tarea.id == RegistroTiempo.tarea_id)
        .join(Cliente, Cliente.id == Tarea.cliente_id)
    )


def _conditions(
    *,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    colaborador_id: int | None,
    cliente_id: int | None,
    scope_usuario_id: int | None,
) -> list:
    """Filtros de HU_52 compartidos por el listado paginado y el total de horas."""
    conds = [RegistroTiempo.deleted_at.is_(None)]

    if fecha_desde is not None:
        conds.append(RegistroTiempo.fecha >= fecha_desde)
    if fecha_hasta is not None:
        conds.append(RegistroTiempo.fecha <= fecha_hasta)
    if colaborador_id is not None:
        conds.append(RegistroTiempo.colaborador_id == colaborador_id)
    if cliente_id is not None:
        tareas = select(Tarea.id).where(Tarea.cliente_id == cliente_id)
        conds.append(RegistroTiempo.tarea_id.in_(tareas))

    # RG-12: el Contador solo consulta sus propios registros.
    if scope_usuario_id is not None:
        conds.append(RegistroTiempo.colaborador_id == scope_usuario_id)

    return conds


def _detail_row(row) -> dict:
    registro, empleado_nombre, cliente_id, cliente_nombre, tarea_titulo = row
    return {
        "id": registro.id,
        "fecha": registro.fecha,
        "empleado_id": registro.colaborador_id,
        "empleado_nombre": empleado_nombre,
        "cliente_id": cliente_id,
        "cliente_nombre": cliente_nombre,
        "tarea_id": registro.tarea_id,
        "tarea_titulo": tarea_titulo,
        "tipo": registro.tipo,
        "duracion_minutos": registro.duracion_minutos,
        "horas": round(registro.duracion_minutos / 60, 2),
        "descripcion": registro.descripcion,
        "nivel_escalafon": registro.nivel_escalafon,
        "cierre_automatico": registro.cierre_automatico,
        "permiso_fuera_plazo_id": registro.permiso_fuera_plazo_id,
        "created_at": registro.created_at,
        "updated_at": registro.updated_at,
    }


def get_detail(registro_id: int) -> dict | None:
    stmt = _detail_stmt().where(
        RegistroTiempo.id == registro_id,
        RegistroTiempo.deleted_at.is_(None),
    )
    row = db.session.execute(stmt).first()
    return _detail_row(row) if row is not None else None


def details_for(registro_ids: list[int]) -> dict[int, dict]:
    """Nombres resueltos de varios registros (evita N+1 en el listado de HU_52)."""
    if not registro_ids:
        return {}

    stmt = _detail_stmt().where(RegistroTiempo.id.in_(registro_ids))
    return {row[0].id: _detail_row(row) for row in db.session.execute(stmt).all()}


def search(
    *,
    fecha_desde: date | None,
    fecha_hasta: date | None,
    colaborador_id: int | None,
    cliente_id: int | None,
    scope_usuario_id: int | None,
    page: int,
    per_page: int,
):
    """HU_52. Página de registros con total de horas del mismo filtro."""
    conds = _conditions(
        fecha_desde=fecha_desde,
        fecha_hasta=fecha_hasta,
        colaborador_id=colaborador_id,
        cliente_id=cliente_id,
        scope_usuario_id=scope_usuario_id,
    )

    stmt = (
        select(RegistroTiempo)
        .where(*conds)
        .order_by(
            RegistroTiempo.fecha.desc(),
            RegistroTiempo.created_at.desc(),
            RegistroTiempo.id.desc(),
        )
    )
    page_obj = db.paginate(
        stmt,
        page=page,
        per_page=per_page,
        max_per_page=per_page,
        error_out=False,
    )

    total_stmt = (
        select(func.coalesce(func.sum(RegistroTiempo.duracion_minutos), 0))
        .select_from(RegistroTiempo)
        .where(*conds)
    )
    total_minutos = int(db.session.execute(total_stmt).scalar_one())

    detalles = details_for([registro.id for registro in page_obj.items])
    items = [detalles[registro.id] for registro in page_obj.items]
    return items, page_obj, total_minutos
