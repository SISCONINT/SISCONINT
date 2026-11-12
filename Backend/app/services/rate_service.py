"""HU_57-62. Lógica de negocio del catálogo de tarifas."""
from app.core import audit
from app.core.errors import NotFoundError
from app.extensions import db
from app.models.rate import Tarifa
from app.models.user import Colaborador
from app.repositories import rate_repository


def list_rates() -> list[dict]:
    """HU_58. Un renglón por colaborador Activo (con o sin tarifa capturada)."""
    return rate_repository.list_with_colaboradores()


def upsert_rate(actor, colaborador_id: int, data: dict) -> Tarifa:
    """HU_59-60. Crea o actualiza la tarifa vigente de un colaborador."""
    colaborador = db.session.get(Colaborador, colaborador_id)
    if colaborador is None or colaborador.deleted_at is not None:
        raise NotFoundError("Colaborador no encontrado")

    tarifa = rate_repository.get_by_colaborador(colaborador_id)
    accion = audit.MODIFICAR if tarifa else audit.CREAR
    before = float(tarifa.monto_hora) if tarifa else None

    if tarifa is None:
        tarifa = Tarifa(colaborador_id=colaborador_id, created_by=actor.id)
        db.session.add(tarifa)

    tarifa.monto_hora = data["monto_hora"]
    tarifa.moneda = data.get("moneda") or "MXN"
    tarifa.updated_by = actor.id

    audit.log(
        actor.id, "tarifa", colaborador_id, accion,
        {"monto_hora": {"antes": before, "despues": float(tarifa.monto_hora)}},
    )
    db.session.commit()
    return tarifa
