export const PERIODOS = ["HOY", "SEMANA", "MES_ACTUAL", "MES_ANTERIOR", "PERSONALIZADO"] as const;
export type Periodo = (typeof PERIODOS)[number];

export const PERIODO_LABELS: Record<Periodo, string> = {
  HOY: "Hoy",
  SEMANA: "Esta semana",
  MES_ACTUAL: "Mes actual",
  MES_ANTERIOR: "Mes anterior",
  PERSONALIZADO: "Rango personalizado",
};

export interface DashboardFilters {
  periodo: Periodo;
  fecha_desde?: string;
  fecha_hasta?: string;
  cliente?: number;
  colaborador?: number;
}

export interface PeriodoInfo {
  tipo: Periodo;
  etiqueta: string;
  desde: string;
  hasta: string;
}

export interface HorasCard {
  horas: number;
  minutos: number;
  variacion_porcentaje: number | null;
  horas_periodo_anterior: number;
}

export interface CostoEstimado {
  disponible: boolean;
  monto: number | null;
  horas_sin_tarifa: number;
  mensaje: string;
}

export interface EstadoTareas {
  POR_HACER: number;
  EN_PROGRESO: number;
  EN_REVISION: number;
  COMPLETADO: number;
  vencidas: number;
  total: number;
}

export interface EmpleadoHoras {
  colaborador_id: number;
  nombre: string;
  minutos: number;
  horas: number;
}

export interface ClienteHoras {
  cliente_id: number;
  nombre: string;
  minutos: number;
  horas: number;
}

export interface CategoriaHoras {
  categoria_id: number;
  nombre: string;
  minutos: number;
  horas: number;
  porcentaje: number;
}

export interface DashboardGerencial {
  periodo: PeriodoInfo;
  periodo_anterior: { desde: string; hasta: string };
  filtros: {
    cliente_id: number | null;
    cliente_nombre: string | null;
    colaborador_id: number | null;
    colaborador_nombre: string | null;
  };
  tarjetas: {
    horas_totales: HorasCard;
    tareas_activas: number;
    tareas_vencidas: number;
    costo_estimado: CostoEstimado | null;
  };
  tiempo_por_empleado: EmpleadoHoras[];
  tiempo_por_cliente: ClienteHoras[];
  distribucion_por_categoria: CategoriaHoras[];
  estado_tareas: EstadoTareas;
  sin_informacion: boolean;
  mensaje: string | null;
}

export interface DashboardPersonal {
  periodo: PeriodoInfo;
  periodo_anterior: { desde: string; hasta: string };
  tarjetas: {
    horas_totales: HorasCard;
    tareas_activas: number;
    tareas_vencidas: number;
  };
  tiempo_por_cliente: ClienteHoras[];
  distribucion_por_categoria: CategoriaHoras[];
  estado_tareas: EstadoTareas;
  sin_informacion: boolean;
  mensaje: string | null;
}
