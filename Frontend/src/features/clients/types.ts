export const TIPOS_PERSONA = ["FISICA", "MORAL"] as const;
export type TipoPersona = (typeof TIPOS_PERSONA)[number];

export const FORMAS_PAGO = ["EFECTIVO", "TRANSFERENCIA"] as const;
export type FormaPago = (typeof FORMAS_PAGO)[number];

export const TIPOS_NOMINA = ["SEMANAL", "QUINCENAL", "MENSUAL"] as const;
export type TipoNomina = (typeof TIPOS_NOMINA)[number];

export type ClienteEstatus = "ACTIVO" | "PAUSADO" | "BAJA";

export interface Contacto {
  nombre_completo: string;
  telefono: string;
  correo: string;
  cargo: string;
}

export interface ContactoConId extends Contacto {
  id: number;
  tipo: "PRINCIPAL" | "PAGOS";
}

export interface ClienteListItem {
  id: number;
  nombre_completo: string;
  razon_social?: string | null;
  rfc: string;
  tipo_persona: TipoPersona;
  contacto_principal_correo?: string | null;
  tareas_activas: number;
  horas_registradas: number;
  estatus: ClienteEstatus;
}

export interface Cliente {
  id: number;
  nombre_completo: string;
  rfc: string;
  tipo_persona: TipoPersona;
  razon_social?: string | null;
  forma_pago: FormaPago;
  contador_asignado_id: number;
  giro: string;
  telefono: string;
  correo: string;
  codigo_postal: string;
  calle: string;
  no_exterior: string;
  no_interior?: string | null;
  colonia: string;
  ciudad: string;
  estado: string;
  tiene_trabajadores: boolean;
  tipo_nomina?: TipoNomina | null;
  estatus: ClienteEstatus;
  motivo_baja?: string | null;
  regimenes: string[];
  contactos: ContactoConId[];
}

export interface ClienteFilters {
  q?: string;
  estatus?: ClienteEstatus;
  contador?: number;
  tipo_persona?: TipoPersona;
  page?: number;
}

export interface ClienteFormValues {
  nombre_completo: string;
  rfc: string;
  tipo_persona: TipoPersona;
  razon_social?: string;
  forma_pago: FormaPago;
  contador_asignado_id: number | null;
  giro: string;
  telefono: string;
  correo: string;
  codigo_postal: string;
  calle: string;
  no_exterior: string;
  no_interior?: string;
  colonia: string;
  ciudad: string;
  estado: string;
  regimenes: string[];
  tiene_trabajadores: boolean;
  tipo_nomina?: TipoNomina | "";
  contacto_principal: Contacto;
  tiene_contacto_pagos: boolean;
  contacto_pagos?: Partial<Contacto>;
}
