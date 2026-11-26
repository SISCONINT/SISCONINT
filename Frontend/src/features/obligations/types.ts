export const PERIODICIDADES = ["MENSUAL", "BIMESTRAL", "ANUAL"] as const;
export type Periodicidad = (typeof PERIODICIDADES)[number];

export const PERIODICIDAD_LABELS: Record<Periodicidad, string> = {
  MENSUAL: "Mensual",
  BIMESTRAL: "Bimestral",
  ANUAL: "Anual",
};

export interface Obligacion {
  id: number;
  cliente_id: number;
  cliente_nombre: string | null;
  categoria_id: number | null;
  categoria_nombre: string | null;
  nombre: string;
  periodicidad: Periodicidad;
  dia_limite: number;
  activa: boolean;
  notas: string | null;
}

export interface ObligacionFormValues {
  cliente_id: number | "";
  categoria_id: number | "";
  nombre: string;
  periodicidad: Periodicidad;
  dia_limite: string;
  notas: string;
}

export interface ObligacionFilters {
  cliente?: number;
  solo_activas?: boolean;
  page: number;
}
