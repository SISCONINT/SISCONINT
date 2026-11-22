export interface ReportPeriodo {
  tipo: string;
  etiqueta: string;
  desde: string;
  hasta: string;
}

export interface ReportHoras {
  horas: number;
  minutos: number;
  variacion_porcentaje: number | null;
  horas_periodo_anterior: number;
}

export interface ReportCosto {
  disponible: boolean;
  monto: number | null;
  horas_sin_tarifa: number;
  mensaje: string;
}

export interface ReportTarjetas {
  horas_totales: ReportHoras;
  tareas_activas: number;
  tareas_vencidas: number;
  costo_estimado?: ReportCosto | null;
}

export interface ReportEstadoTareas {
  POR_HACER?: number;
  EN_PROGRESO?: number;
  EN_REVISION?: number;
  COMPLETADO?: number;
  vencidas?: number;
  total?: number;
}

export interface ReportHorasRow {
  minutos: number;
  horas: number;
}

export interface ReportEmpleadoRow extends ReportHorasRow {
  colaborador_id: number;
  nombre: string;
}

export interface ReportClienteRow extends ReportHorasRow {
  cliente_id: number;
  nombre: string;
}

export interface ReportCategoriaRow extends ReportHorasRow {
  categoria_id: number;
  nombre: string;
  porcentaje: number;
}

export interface ReportData {
  periodo: ReportPeriodo;
  periodo_anterior?: { desde: string; hasta: string };
  filtros?: {
    cliente_id: number | null;
    cliente_nombre: string | null;
    colaborador_id: number | null;
    colaborador_nombre: string | null;
  };
  tarjetas: ReportTarjetas;
  tiempo_por_empleado?: ReportEmpleadoRow[];
  tiempo_por_cliente?: ReportClienteRow[];
  distribucion_por_categoria?: ReportCategoriaRow[];
  estado_tareas: ReportEstadoTareas;
  tareas_completadas: number;
  generado_en: string;
  sin_informacion: boolean;
  mensaje: string | null;
}

export interface ReportFilters {
  periodo: string;
  fecha_desde?: string;
  fecha_hasta?: string;
  cliente?: number;
  colaborador?: number;
}

export interface ReportOption {
  id: number;
  nombre_completo: string;
}
