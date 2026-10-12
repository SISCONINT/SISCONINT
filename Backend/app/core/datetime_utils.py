"""RG-04: se guarda y compara en UTC; America/Mexico_City es solo de presentación."""
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

TZ_MX = ZoneInfo("America/Mexico_City")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def today_mx() -> date:
    """Fecha 'hoy' en America/Mexico_City. Para comparar vigencias por día (permisos, obligaciones)."""
    return datetime.now(TZ_MX).date()


def now_mx() -> datetime:
    """Momento actual en America/Mexico_City, con tzinfo. Para presentación o para formatear."""
    return datetime.now(TZ_MX)


def as_utc(dt: datetime) -> datetime:
    """Normaliza a UTC. Si viene sin tzinfo, asume que ya está en UTC (convención del sistema)."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)