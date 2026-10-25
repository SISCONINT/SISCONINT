"""RG-11: semáforo de vencimiento. Se calcula siempre en el servidor.

Días naturales entre hoy (America/Mexico_City) y la fecha límite:

    VERDE     faltan 3 días o más
    AMARILLO  faltan 1 o 2 días
    ROJO      vence hoy o ya venció
    GRIS      tarea Completada (sin semáforo)
"""
from datetime import date, timedelta

from app.core.datetime_utils import today_mx
from app.models.task import ESTADO_COMPLETADO

SEMAFORO_VERDE = "VERDE"
SEMAFORO_AMARILLO = "AMARILLO"
SEMAFORO_ROJO = "ROJO"
SEMAFORO_GRIS = "GRIS"
SEMAFOROS = (SEMAFORO_VERDE, SEMAFORO_AMARILLO, SEMAFORO_ROJO, SEMAFORO_GRIS)

# Umbrales en días naturales (RG-11). El repositorio los reutiliza para filtrar en SQL.
DIAS_VERDE = 3
DIAS_AMARILLO_DESDE = 1
DIAS_AMARILLO_HASTA = 2


def dias_restantes(fecha_limite: date, hoy: date | None = None) -> int:
    """Días naturales de hoy a la fecha límite. Negativo si ya venció."""
    return (fecha_limite - (hoy or today_mx())).days


def calcular_semaforo(estado: str, fecha_limite: date, hoy: date | None = None) -> str:
    """Devuelve el color del semáforo de una tarea (RG-11)."""
    if estado == ESTADO_COMPLETADO:
        return SEMAFORO_GRIS

    dias = dias_restantes(fecha_limite, hoy)
    if dias >= DIAS_VERDE:
        return SEMAFORO_VERDE
    if dias >= DIAS_AMARILLO_DESDE:
        return SEMAFORO_AMARILLO
    return SEMAFORO_ROJO


def primer_dia_verde(hoy: date | None = None) -> date:
    """Primera fecha límite que pinta verde."""
    return (hoy or today_mx()) + timedelta(days=DIAS_VERDE)


def rango_amarillo(hoy: date | None = None) -> tuple[date, date]:
    """Rango inclusivo de fechas límite que pintan amarillo."""
    base = hoy or today_mx()
    return (
        base + timedelta(days=DIAS_AMARILLO_DESDE),
        base + timedelta(days=DIAS_AMARILLO_HASTA),
    )
