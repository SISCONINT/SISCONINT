"""HU_79-85. Lógica de negocio del dashboard.

El periodo se resuelve en el servidor (RG-04) y el periodo anterior es la misma
cantidad de días inmediatamente antes del inicio del periodo actual. Las tarjetas
de tareas son una foto del estado actual y no dependen del periodo.
"""
from datetime import date, timedelta

from app.core.datetime_utils import today_mx
from app.models.task import ESTADO_COMPLETADO
from app.models.user import ROL_ADMINISTRADOR, ROL_DUENO
from app.repositories import dashboard_repository, rate_repository

MSG_SIN_INFO = "Sin información para los filtros seleccionados"
MSG_SIN_TARIFAS = "Sin tarifas configuradas"

ETIQUETAS = {
    "HOY": "Hoy",
    "SEMANA": "Esta semana",
    "MES_ACTUAL": "Mes actual",
    "MES_ANTERIOR": "Mes anterior",
    "PERSONALIZADO": "Rango personalizado",
}


# ---------------------------------------------------------------------------
# Periodos
# ---------------------------------------------------------------------------
def _resolver_periodo(filtros: dict) -> dict:
    """Traduce el periodo elegido a un rango de fechas inclusivo.

    - Hoy: el día actual.
    - Esta semana: del lunes a hoy (semana en curso).
    - Mes actual: del día 1 a hoy (mes en curso).
    - Mes anterior: el mes calendario completo anterior.
    - Personalizado: las fechas recibidas (el schema valida el máximo de 12 meses).
    """
    tipo = filtros.get("periodo") or "MES_ACTUAL"
    hoy = today_mx()

    if tipo == "HOY":
        desde = hasta = hoy
    elif tipo == "SEMANA":
        desde = hoy - timedelta(days=hoy.weekday())
        hasta = hoy
    elif tipo == "MES_ACTUAL":
        desde = hoy.replace(day=1)
        hasta = hoy
    elif tipo == "MES_ANTERIOR":
        hasta = hoy.replace(day=1) - timedelta(days=1)
        desde = hasta.replace(day=1)
    else:
        desde = filtros["fecha_desde"]
        hasta = filtros["fecha_hasta"]

    return {
        "tipo": tipo,
        "etiqueta": ETIQUETAS.get(tipo, tipo),
        "desde": desde,
        "hasta": hasta,
    }


def _periodo_anterior(desde: date, hasta: date) -> dict:
    """Mismo número de días inmediatamente antes del inicio del periodo actual."""
    dias = (hasta - desde).days + 1
    anterior_hasta = desde - timedelta(days=1)
    anterior_desde = anterior_hasta - timedelta(days=dias - 1)
    return {"desde": anterior_desde, "hasta": anterior_hasta}


# ---------------------------------------------------------------------------
# Dashboard general (HU_79-84)
# ---------------------------------------------------------------------------
def get_dashboard(actor, filtros: dict) -> dict:
    """Dashboard del despacho para Dueño, Administrador y Coordinador.

    Los filtros de cliente y colaborador se aplican a todas las tarjetas y
    gráficas. El costo estimado solo se incluye para Dueño y Administrador; el
    Coordinador no recibe la clave.
    """
    periodo = _resolver_periodo(filtros)
    anterior = _periodo_anterior(periodo["desde"], periodo["hasta"])
    cliente_id = filtros.get("cliente")
    colaborador_id = filtros.get("colaborador")

    total = _total(periodo, cliente_id, colaborador_id)
    total_anterior = _total(anterior, cliente_id, colaborador_id)

    empleados = dashboard_repository.tiempo_por_empleado(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    clientes = dashboard_repository.tiempo_por_cliente(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    categorias = dashboard_repository.tiempo_por_categoria(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )
    tareas = dashboard_repository.conteo_tareas(
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
        hoy=today_mx(),
    )

    tarjetas = {
        "horas_totales": _horas_card(total, total_anterior),
        "tareas_activas": tareas["total"] - tareas[ESTADO_COMPLETADO],
        "tareas_vencidas": tareas["vencidas"],
    }
    costo = _costo_estimado(actor, empleados)
    if costo is not None:
        tarjetas["costo_estimado"] = costo

    sin_informacion = total == 0 and tareas["total"] == 0

    return {
        "periodo": periodo,
        "periodo_anterior": anterior,
        "filtros": {
            "cliente_id": cliente_id,
            "cliente_nombre": dashboard_repository.get_cliente_nombre(cliente_id),
            "colaborador_id": colaborador_id,
            "colaborador_nombre": dashboard_repository.get_colaborador_nombre(
                colaborador_id
            ),
        },
        "tarjetas": tarjetas,
        "tiempo_por_empleado": _filas_empleado(empleados),
        "tiempo_por_cliente": _filas_cliente(clientes),
        "distribucion_por_categoria": _filas_categoria(categorias),
        "estado_tareas": tareas,
        "sin_informacion": sin_informacion,
        "mensaje": MSG_SIN_INFO if sin_informacion else None,
    }


# ---------------------------------------------------------------------------
# Dashboard personal (HU_85)
# ---------------------------------------------------------------------------
def get_personal_dashboard(actor, filtros: dict) -> dict:
    """Dashboard propio del Contador: solo sus horas, clientes, categorías y tareas.

    No incluye costos ni información de otros colaboradores. Cualquier filtro de
    colaborador recibido se ignora: el alcance siempre es el usuario autenticado.
    """
    periodo = _resolver_periodo(filtros)
    anterior = _periodo_anterior(periodo["desde"], periodo["hasta"])
    colaborador_id = actor.id

    total = _total(periodo, None, colaborador_id)
    total_anterior = _total(anterior, None, colaborador_id)

    clientes = dashboard_repository.tiempo_por_cliente(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=None,
        colaborador_id=colaborador_id,
    )
    categorias = dashboard_repository.tiempo_por_categoria(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=None,
        colaborador_id=colaborador_id,
    )
    tareas = dashboard_repository.conteo_tareas(
        cliente_id=None,
        colaborador_id=colaborador_id,
        hoy=today_mx(),
    )

    tarjetas = {
        "horas_totales": _horas_card(total, total_anterior),
        "tareas_activas": tareas["total"] - tareas[ESTADO_COMPLETADO],
        "tareas_vencidas": tareas["vencidas"],
    }
    sin_informacion = total == 0 and tareas["total"] == 0

    return {
        "periodo": periodo,
        "periodo_anterior": anterior,
        "tarjetas": tarjetas,
        "tiempo_por_cliente": _filas_cliente(clientes),
        "distribucion_por_categoria": _filas_categoria(categorias),
        "estado_tareas": tareas,
        "sin_informacion": sin_informacion,
        "mensaje": MSG_SIN_INFO if sin_informacion else None,
    }


# ---------------------------------------------------------------------------
# Utilidades de presentación
# ---------------------------------------------------------------------------
def _total(periodo: dict, cliente_id: int | None, colaborador_id: int | None) -> int:
    return dashboard_repository.total_minutos(
        fecha_desde=periodo["desde"],
        fecha_hasta=periodo["hasta"],
        cliente_id=cliente_id,
        colaborador_id=colaborador_id,
    )


def _horas(minutos: int) -> float:
    return round(minutos / 60, 1)


def _horas_card(minutos: int, minutos_anteriores: int) -> dict:
    return {
        "horas": _horas(minutos),
        "minutos": minutos,
        "variacion_porcentaje": _variacion(minutos, minutos_anteriores),
        "horas_periodo_anterior": _horas(minutos_anteriores),
    }


def _variacion(actual: int, anterior: int) -> float | None:
    """Variación porcentual; sin horas previas no hay comparación posible."""
    if anterior == 0:
        return None if actual > 0 else 0.0
    return round((actual - anterior) * 100 / anterior, 1)


def _costo_estimado(actor, empleados: list[dict]) -> dict | None:
    """Costo estimado solo para Dueño y Administrador (HU_79).

    Usa el catálogo de tarifas (HU_57-62): suma horas × tarifa por cada colaborador que
    ya tiene una tarifa capturada, y reporta aparte las horas que quedaron sin tarifa.
    """
    if actor.rol not in (ROL_DUENO, ROL_ADMINISTRADOR):
        return None

    colaborador_ids = [e["colaborador_id"] for e in empleados]
    tarifas = rate_repository.tarifas_por_colaborador(colaborador_ids, today_mx())

    if not tarifas:
        return {
            "disponible": False,
            "monto": None,
            "horas_sin_tarifa": _horas(sum(e["minutos"] for e in empleados)),
            "mensaje": MSG_SIN_TARIFAS,
        }

    monto = 0.0
    minutos_sin_tarifa = 0
    for e in empleados:
        tarifa = tarifas.get(e["colaborador_id"])
        if tarifa is None:
            minutos_sin_tarifa += e["minutos"]
        else:
            monto += (e["minutos"] / 60.0) * tarifa

    horas_sin_tarifa = _horas(minutos_sin_tarifa)
    return {
        "disponible": True,
        "monto": round(monto, 2),
        "horas_sin_tarifa": horas_sin_tarifa,
        "mensaje": "" if minutos_sin_tarifa == 0 else f"{horas_sin_tarifa} hrs sin tarifa configurada",
    }


def _filas_empleado(rows: list[dict]) -> list[dict]:
    return [
        {
            "colaborador_id": row["colaborador_id"],
            "nombre": row["nombre"],
            "minutos": row["minutos"],
            "horas": _horas(row["minutos"]),
        }
        for row in rows
    ]


def _filas_cliente(rows: list[dict]) -> list[dict]:
    return [
        {
            "cliente_id": row["cliente_id"],
            "nombre": row["nombre"],
            "minutos": row["minutos"],
            "horas": _horas(row["minutos"]),
        }
        for row in rows
    ]


def _filas_categoria(rows: list[dict]) -> list[dict]:
    """Agrega el porcentaje; el total siempre suma 100.0 (HU_82)."""
    total = sum(row["minutos"] for row in rows)
    if total == 0:
        return []

    porcentajes = [round(row["minutos"] * 100 / total, 1) for row in rows]
    diferencia = round(100.0 - sum(porcentajes), 1)
    if diferencia:
        # El ajuste de redondeo se aplica a la categoría con más horas.
        mayor = max(range(len(rows)), key=lambda indice: rows[indice]["minutos"])
        porcentajes[mayor] = round(porcentajes[mayor] + diferencia, 1)

    return [
        {
            "categoria_id": row["categoria_id"],
            "nombre": row["nombre"],
            "minutos": row["minutos"],
            "horas": _horas(row["minutos"]),
            "porcentaje": porcentajes[indice],
        }
        for indice, row in enumerate(rows)
    ]
