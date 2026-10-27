export const ESTADOS = ["POR_HACER", "EN_PROGRESO", "EN_REVISION", "COMPLETADO"] as const;
export type Estado = (typeof ESTADOS)[number];

export const PRIORIDADES = ["BAJA", "MEDIA", "ALTA"] as const;
export type Prioridad = (typeof PRIORIDADES)[number];

export type Semaforo = "VERDE" | "AMARILLO" | "ROJO" | "GRIS";

export interface TareaListItem {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre?: string | null;
  categoria_id: number;
  categoria_nombre?: string | null;
  categoria_padre_nombre?: string | null;
  asignado_id: number;
  asignado_nombre?: string | null;
  prioridad: Prioridad;
  estado: Estado;
  fecha_limite: string;
  hora_limite?: string | null;
  semaforo: Semaforo;
  dias_restantes: number;
}

export interface TareaListFilters {
  cliente?: number;
  responsable?: number;
  estado?: Estado;
  prioridad?: Prioridad;
  categoria?: number;
  fecha_limite_desde?: string;
  fecha_limite_hasta?: string;
  semaforo?: Semaforo;
  page?: number;
}

export interface TareaBoardFilters {
  cliente?: number;
  responsable?: number;
  prioridad?: Prioridad;
  fecha_limite_desde?: string;
  fecha_limite_hasta?: string;
}

export interface TareaBoardCard {
  id: number;
  titulo: string;
  cliente_id: number;
  cliente_nombre?: string | null;
  asignado_id: number;
  asignado_nombre?: string | null;
  prioridad: Prioridad;
  estado: Estado;
  fecha_limite: string;
  hora_limite?: string | null;
  semaforo: Semaforo;
  minutos_registrados: number;
  horas_registradas: number;
  horas_estimadas?: number | null;
  porcentaje_registrado?: number | null;
  completada_en?: string | null;
}

export interface TareaBoardColumn {
  estado: Estado;
  titulo: string;
  total: number;
  tareas: TareaBoardCard[];
}

export interface TareaBoard {
  columnas: TareaBoardColumn[];
  total_tareas: number;
  mensaje?: string | null;
}

export interface Subtarea {
  id: number;
  titulo: string;
  completada: boolean;
  completada_por?: number | null;
  completada_por_nombre?: string | null;
  completada_en?: string | null;
  created_at: string;
}

export interface Comentario {
  id: number;
  autor_id: number;
  autor_nombre?: string | null;
  texto: string;
  editado: boolean;
  created_at: string;
  updated_at: string;
}

export interface HistorialEstado {
  id: number;
  estado_anterior?: Estado | null;
  estado_nuevo: Estado;
  usuario_id?: number | null;
  usuario_nombre?: string | null;
  created_at: string;
}

export interface TiempoColaborador {
  colaborador_id: number;
  colaborador_nombre?: string | null;
  minutos: number;
  horas: number;
}

export interface TareaDetalle {
  id: number;
  titulo: string;
  descripcion?: string | null;
  cliente_id: number;
  cliente_nombre?: string | null;
  categoria_id: number;
  categoria_nombre?: string | null;
  categoria_padre_nombre?: string | null;
  asignado_id: number;
  asignado_nombre?: string | null;
  creador_id?: number | null;
  creador_nombre?: string | null;
  obligacion_id?: number | null;
  periodo?: string | null;
  fecha_limite: string;
  hora_limite?: string | null;
  prioridad: Prioridad;
  estado: Estado;
  horas_estimadas?: number | null;
  notificar_cliente: boolean;
  cliente_notificado: boolean;
  completada_en?: string | null;
  completada_por?: number | null;
  completada_por_nombre?: string | null;
  created_by?: number | null;
  updated_by?: number | null;
  created_at: string;
  updated_at: string;
  semaforo: Semaforo;
  dias_restantes: number;
  subtareas: {
    items: Subtarea[];
    total: number;
    completadas: number;
    avance: string;
    porcentaje: number;
  };
  comentarios: Comentario[];
  historial_estados: HistorialEstado[];
  tiempo: {
    total_minutos: number;
    total_horas: number;
    horas_estimadas?: number | null;
    porcentaje_registrado?: number | null;
    por_colaborador: TiempoColaborador[];
  };
}

export interface TareaFormValues {
  titulo: string;
  descripcion?: string;
  cliente_id: number | null;
  categoria_id: number | null;
  asignado_id: number | null;
  fecha_limite: string;
  hora_limite: string;
  prioridad: Prioridad;
  horas_estimadas?: string;
  notificar_cliente: boolean;
}
