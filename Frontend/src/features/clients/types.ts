export type TipoPersona = "FISICA" | "MORAL";
export type EstatusCliente = "ACTIVO" | "PAUSADO" | "BAJA";
export type FormaPago = "EFECTIVO" | "TRANSFERENCIA";
export type TipoNomina = "SEMANAL" | "QUINCENAL" | "MENSUAL";
export type TipoContacto = "PRINCIPAL" | "PAGOS";

/** Datos mínimos que devuelve el listado (HU_12) y que también sirven de encabezado del expediente. */
export interface ClienteResumen {
  id: number;
  nombre_completo: string;
  razon_social: string | null;
  rfc: string;
  tipo_persona: TipoPersona;
  estatus: EstatusCliente;
  contacto_principal_correo?: string | null;
  tareas_activas?: number;
  horas_registradas?: number;
}

export interface ClienteListItem extends ClienteResumen {
  contacto_principal_correo: string | null;
  tareas_activas: number;
  horas_registradas: number;
}

export interface ContactoCliente {
  nombre_completo: string;
  telefono: string;
  correo: string;
  cargo: string;
}

export interface ContactoClienteDetalle extends ContactoCliente {
  id: number;
  tipo: TipoContacto;
}

/** Expediente fiscal (respuesta de POST /clients y de la futura consulta de detalle). */
export interface ClienteDetalle extends ClienteResumen {
  giro: string;
  forma_pago: FormaPago;
  contador_asignado_id: number;
  telefono: string;
  correo: string;
  codigo_postal: string;
  calle: string;
  no_exterior: string;
  no_interior: string | null;
  colonia: string;
  ciudad: string;
  estado: string;
  tiene_trabajadores: boolean;
  tipo_nomina: TipoNomina | null;
  motivo_baja: string | null;
  regimenes: string[];
  contactos: ContactoClienteDetalle[];
}

/** Cabecera + datos completos cuando el backend ya expone el detalle. */
export type ClienteExpediente = ClienteResumen & Partial<ClienteDetalle>;

export interface ClienteCreatePayload {
  nombre_completo: string;
  rfc: string;
  tipo_persona: TipoPersona;
  razon_social?: string;
  forma_pago: FormaPago;
  contador_asignado_id: number;
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
  tipo_nomina?: TipoNomina;
  contacto_principal: ContactoCliente;
  contacto_pagos?: ContactoCliente;
}

export interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  pages?: number;
}

export interface ClientesPage {
  items: ClienteListItem[];
  meta: PaginationMeta;
}

export interface ClientesQuery {
  q: string;
  estatus: EstatusCliente;
  tipo_persona: TipoPersona | null;
  contador?: number;
  page: number;
}

export interface AccountantOption {
  id: number;
  nombre_completo: string;
  correo_institucional: string;
  grado_escalafon: string;
}

export type ClientFileLocationState = {
  cliente?: ClienteResumen;
  recienCreado?: boolean;
};
