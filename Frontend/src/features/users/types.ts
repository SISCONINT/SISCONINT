import type { Role } from "@/shared/constants/roles";
import type { Grado } from "@/shared/constants/grados";

export interface Colaborador{
    id: number;
    nombre_completo: string;
    correo_institucional: string;
    rol: Role;
    grado_escalafon: Grado;
    estatus: "ACTIVO"|"INACTIVO";
    telefono_despacho: string;
    telefono_personal: string;
    emergencia_nombre: string;
    emergencia_telefono: string;
    //Opcionales
    licenciatura: string | null;
    cedula: string | null;
    calle: string | null;
    no_ext_int: string | null;
    colonia: string | null;
    municipio: string | null;
    estado: string | null;
    fecha_alta: string;
}

export interface ColaboradorCreado extends Colaborador{
    correo_activacion_enviado: boolean
}

export type EstatusColaborador = "ACTIVO" | "INACTIVO";

export interface UsersFilters {
  search: string;
  rol: Role | "";
  estatus: EstatusColaborador | "";
  page: number;
}