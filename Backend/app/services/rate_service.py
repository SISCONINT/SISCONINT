"""HU_57-62. Lógica de negocio del catálogo de tarifas por nivel."""
from datetime import timedelta

from app.core import audit
from app.core.datetime_utils import today_mx
from app.core.errors import ConflictError, ValidationAppError
from app.extensions import db
from app.models.rate import TarifaNivel
from app.models.user import GRADOS
from app.repositories import rate_repository

MSG_TRASLAPE = "Ya existe una tarifa vigente para ese nivel en el rango indicado"


def list_rates() -> list[dict]:
    """Una fila por nivel con la tarifa vigente hoy (o sin tarifa)."""
    hoy = today_mx()
    filas = []
    for nivel in GRADOS:
        tarifa = rate_repository.get_effective(nivel, hoy)
        filas.append(
            {
                "id": tarifa.id if tarifa else None,
                "nivel": nivel,
                "monto_hora_mxn": float(tarifa.monto_hora_mxn) if tarifa else None,
                "vigencia_inicio": tarifa.vigencia_inicio if tarifa else None,
                "vigencia_fin": tarifa.vigencia_fin if tarifa else None,
                "vigente": tarifa is not None,
                "updated_at": tarifa.updated_at if tarifa else None,
            }
        )
    return filas


def upsert_rate(actor, nivel: str, data: dict) -> TarifaNivel:
    if nivel not in GRADOS:
        raise ValidationAppError(
            "Nivel no válido", fields={"nivel": ["Debe ser JUNIOR, SENIOR o ADMIN"]}
        )

    inicio = data.get("vigencia_inicio") or today_mx()
    fin = data.get("vigencia_fin")
    if fin is not None and fin < inicio:
        raise ValidationAppError(
            "La fecha final no puede ser anterior a la inicial",
            fields={"vigencia_fin": ["Debe ser igual o posterior a la fecha inicial"]},
        )

    # Si ya hay una tarifa que empieza exactamente en esa fecha, se actualiza.
    tarifa = rate_repository.get_by_nivel_inicio(nivel, inicio)
    accion = audit.MODIFICAR if tarifa else audit.CREAR

    if tarifa is None:
        # Cerrar la tarifa vigente anterior el día antes de la nueva vigencia.
        anterior = rate_repository.get_effective(nivel, inicio)
        if anterior is not None:
            if anterior.vigencia_inicio == inicio:
                tarifa = anterior
                accion = audit.MODIFICAR
            else:
                anterior.vigencia_fin = inicio - timedelta(days=1)
                anterior.updated_by = actor.id

    if tarifa is None:
        tarifa = TarifaNivel(
            nivel=nivel,
            monto_hora_mxn=data["monto_hora_mxn"],
            vigencia_inicio=inicio,
            vigencia_fin=fin,
            created_by=actor.id,
            updated_by=actor.id,
        )
        db.session.add(tarifa)
    else:
        tarifa.monto_hora_mxn = data["monto_hora_mxn"]
        tarifa.vigencia_fin = fin
        tarifa.updated_by = actor.id

    db.session.flush()

    traslape = rate_repository.find_overlap(nivel, inicio, fin, exclude_id=tarifa.id)
    if traslape is not None:
        db.session.rollback()
        raise ConflictError(MSG_TRASLAPE, fields={"vigencia_inicio": [MSG_TRASLAPE]})

    audit.log(
        actor.id,
        "tarifa_nivel",
        tarifa.id,
        accion,
        {
            "nivel": nivel,
            "monto_hora_mxn": float(tarifa.monto_hora_mxn),
            "vigencia_inicio": inicio.isoformat(),
        },
    )
    db.session.commit()
    return tarifa
