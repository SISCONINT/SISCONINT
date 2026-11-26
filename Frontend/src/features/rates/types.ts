import type { Role } from "@/shared/constants/roles";

export interface TarifaRow {
  id: number | null;
  colaborador_id: number;
  colaborador_nombre: string;
  rol: Role;
  monto_hora: number | null;
  moneda: string | null;
  updated_at: string | null;
}
