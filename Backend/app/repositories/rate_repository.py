"""HU_57-62. Acceso a datos de tarifas por nivel de escalafón."""
from datetime import date

from sqlalchemy import select

from app.extensions import db
from app.models.rate import TarifaNivel
from app.models.user import Colaborador


def get_effective(nivel: str, fecha: date) -> TarifaNivel | None:
    stmt = (
        select(TarifaNivel)
        .where(
            TarifaNivel.nivel == nivel,
            TarifaNivel.deleted_at.is_(None),
            TarifaNivel.vigencia_inicio <= fecha,
            (TarifaNivel.vigencia_fin.is_(None)) | (TarifaNivel.vigencia_fin >= fecha),
        )
        .order_by(TarifaNivel.vigencia_inicio.desc(), TarifaNivel.id.desc())
        .limit(1)
    )
    return db.session.execute(stmt).scalar_one_or_none()


def get_by_nivel_inicio(nivel: str, inicio: date) -> TarifaNivel | None:
    stmt = select(TarifaNivel).where(
        TarifaNivel.nivel == nivel,
        TarifaNivel.deleted_at.is_(None),
        TarifaNivel.vigencia_inicio == inicio,
    )
    return db.session.execute(stmt).scalar_one_or_none()


def find_overlap(
    nivel: str,
    inicio: date,
    fin: date | None,
    exclude_id: int | None = None,
) -> TarifaNivel | None:
    """Busca una tarifa del mismo nivel que se traslape con [inicio, fin]."""
    stmt = select(TarifaNivel).where(
        TarifaNivel.nivel == nivel,
        TarifaNivel.deleted_at.is_(None),
        TarifaNivel.vigencia_inicio <= (fin or date.max),
        (TarifaNivel.vigencia_fin.is_(None)) | (TarifaNivel.vigencia_fin >= inicio),
    )
    if exclude_id is not None:
        stmt = stmt.where(TarifaNivel.id != exclude_id)
    return db.session.execute(stmt.limit(1)).scalar_one_or_none()


def rates_by_level(fecha: date) -> dict[str, float]:
    stmt = (
        select(TarifaNivel.nivel, TarifaNivel.monto_hora_mxn)
        .where(
            TarifaNivel.deleted_at.is_(None),
            TarifaNivel.vigencia_inicio <= fecha,
            (TarifaNivel.vigencia_fin.is_(None)) | (TarifaNivel.vigencia_fin >= fecha),
        )
        .order_by(TarifaNivel.nivel, TarifaNivel.vigencia_inicio.desc(), TarifaNivel.id.desc())
    )
    result: dict[str, float] = {}
    for nivel, monto in db.session.execute(stmt).all():
        result.setdefault(nivel, float(monto))
    return result


def tarifas_por_colaborador(colaborador_ids: list[int], fecha: date) -> dict[int, float]:
    """Mapa {colaborador_id: monto_hora_mxn vigente en la fecha} para el costo estimado."""
    if not colaborador_ids:
        return {}
    rates = rates_by_level(fecha)
    stmt = select(Colaborador.id, Colaborador.grado_escalafon).where(
        Colaborador.id.in_(colaborador_ids),
        Colaborador.deleted_at.is_(None),
    )
    return {
        colaborador_id: rates[nivel]
        for colaborador_id, nivel in db.session.execute(stmt).all()
        if nivel in rates
    }
