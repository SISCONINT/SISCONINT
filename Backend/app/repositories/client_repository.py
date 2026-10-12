"""HU_11-12. Acceso a datos de clientes."""
from sqlalchemy import func, select

from app.extensions import db
from app.models.client import Cliente, RegimenFiscal
from app.models.user import Colaborador, ESTATUS_ACTIVO, ROL_CONTADOR


def find_by_rfc(rfc: str) -> Cliente | None:
    """Busca un cliente NO eliminado por RFC (comparación exacta, ya viene en mayúsculas)."""
    stmt = select(Cliente).where(Cliente.rfc == rfc, Cliente.deleted_at.is_(None))
    return db.session.execute(stmt).scalar_one_or_none()


def get_contador_activo(contador_id: int) -> Colaborador | None:
    """Colaborador Activo con rol CONTADOR, no eliminado."""
    stmt = select(Colaborador).where(
        Colaborador.id == contador_id,
        Colaborador.rol == ROL_CONTADOR,
        Colaborador.estatus == ESTATUS_ACTIVO,
        Colaborador.deleted_at.is_(None),
    )
    return db.session.execute(stmt).scalar_one_or_none()


def regimenes_existen(claves: list[str]) -> set[str]:
    """Devuelve el subconjunto de claves que SÍ existen y están activas en regimen_fiscal."""
    if not claves:
        return set()
    stmt = select(RegimenFiscal.clave).where(
        RegimenFiscal.clave.in_(claves), RegimenFiscal.activo.is_(True)
    )
    return {row[0] for row in db.session.execute(stmt).all()}


def add(cliente: Cliente) -> Cliente:
    db.session.add(cliente)
    db.session.flush()
    return cliente