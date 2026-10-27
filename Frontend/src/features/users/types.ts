import type { Role } from "@/shared/constants/roles";

export const GRADOS = ["JUNIOR", "SENIOR", "ADMIN"] as const;
export type Grado = (typeof GRADOS)[number];

export const GRADO_LABELS: Record<Grado, string> = {
  JUNIOR: "Junior",
  SENIOR: "Senior",
  ADMIN: "Administrativo",
};

export type Estatus = "ACTIVO" | "INACTIVO";

export interface ColaboradorListItem {
  id: number;
  nombre_completo: string;
  correo_institucional: string;
  rol: Role;
  grado_escalafon: Grado;
  estatus: Estatus;
}

export interface Colaborador extends ColaboradorListItem {
  telefono_despacho: string;
  telefono_personal: string;
  licenciatura?: string | null;
  cedula?: string | null;
  calle?: string | null;
  no_ext_int?: string | null;
  colonia?: string | null;
  municipio?: string | null;
  estado?: string | null;
  emergencia_nombre: string;
  emergencia_telefono: string;
  fecha_alta: string;
}

export interface ColaboradorFilters {
  q?: string;
  rol?: Role;
  estatus?: Estatus;
  page?: number;
}

export interface ColaboradorFormValues {
  nombre_completo: string;
  telefono_despacho: string;
  correo_institucional: string;
  rol: Role;
  grado_escalafon: Grado;
  telefono_personal: string;
  emergencia_nombre: string;
  emergencia_telefono: string;
  licenciatura?: string;
  cedula?: string;
  calle?: string;
  no_ext_int?: string;
  colonia?: string;
  municipio?: string;
  estado?: string;
}

export interface ReasignadoA {
  id: number;
  nombre_completo: string;
  rol: Role;
}

export interface DeactivationImpact {
  colaborador_id: number;
  clientes_asignados: number;
  tareas_abiertas: number;
  requiere_reasignacion: boolean;
  destinos: ReasignadoA[];
}

export function colaboradorToFormValues(c: Colaborador): ColaboradorFormValues {
  return {
    nombre_completo: c.nombre_completo,
    telefono_despacho: c.telefono_despacho,
    correo_institucional: c.correo_institucional,
    rol: c.rol,
    grado_escalafon: c.grado_escalafon,
    telefono_personal: c.telefono_personal,
    emergencia_nombre: c.emergencia_nombre,
    emergencia_telefono: c.emergencia_telefono,
    licenciatura: c.licenciatura ?? "",
    cedula: c.cedula ?? "",
    calle: c.calle ?? "",
    no_ext_int: c.no_ext_int ?? "",
    colonia: c.colonia ?? "",
    municipio: c.municipio ?? "",
    estado: c.estado ?? "",
  };
}
