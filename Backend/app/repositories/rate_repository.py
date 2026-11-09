"""HU_57-62. Acceso a datos de tarifas por colaborador."""
from sqlalchemy import select

from app.extensions import db
from app.models.rate import Tarifa
from app.models.user import ESTATUS_ACTIVO, Colaborador


def list_with_colaboradores() -> list[dict]:
    """Un renglón por colaborador Activo, con su tarifa si ya tiene una asignada."""
    stmt = (
        select(Colaborador, Tarifa)
        .outerjoin(
            Tarifa, (Tarifa.colaborador_id == Colaborador.id) & (Tarifa.deleted_at.is_(None))
        )
        .where(Colaborador.estatus == ESTATUS_ACTIVO, Colaborador.deleted_at.is_(None))
        .order_by(Colaborador.nombre_completo)
    )
    rows = db.session.execute(stmt).all()
    return [
        {
            "id": tarifa.id if tarifa else None,
            "colaborador_id": colaborador.id,
            "colaborador_nombre": colaborador.nombre_completo,
            "rol": colaborador.rol,
            "monto_hora": float(tarifa.monto_hora) if tarifa else None,
            "moneda": tarifa.moneda if tarifa else None,
            "updated_at": tarifa.updated_at if tarifa else None,
        }
        for colaborador, tarifa in rows
    ]


def get_by_colaborador(colaborador_id: int) -> Tarifa | None:
    stmt = select(Tarifa).where(Tarifa.colaborador_id == colaborador_id, Tarifa.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def tarifas_por_colaborador(colaborador_ids: list[int]) -> dict[int, float]:
    """Mapa {colaborador_id: monto_hora} para el costo estimado del dashboard."""
    if not colaborador_ids:
        return {}
    stmt = select(Tarifa.colaborador_id, Tarifa.monto_hora).where(
        Tarifa.colaborador_id.in_(colaborador_ids), Tarifa.deleted_at.is_(None)
    )
    return {cid: float(monto) for cid, monto in db.session.execute(stmt).all()}
