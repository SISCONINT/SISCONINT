export interface Minuta {
  id: number;
  cliente_id: number | null;
  cliente_nombre: string | null;
  tarea_id: number | null;
  tarea_titulo: string | null;
  titulo: string;
  fecha: string;
  participantes: string | null;
  acuerdos: string;
  creador_id: number;
  creador_nombre: string | null;
  created_at: string;
}

export interface MinutaFormValues {
  cliente_id: number | "";
  titulo: string;
  fecha: string;
  participantes: string;
  acuerdos: string;
}

export interface MinutaFilters {
  cliente?: number;
  page: number;
}
