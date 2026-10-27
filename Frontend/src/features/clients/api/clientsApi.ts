import { api } from "@/shared/api/client";
import type { ApiResponse } from "@/shared/api/types";
import { toQueryParams } from "@/shared/utils/format";
import type { Cliente, ClienteFilters, ClienteFormValues, ClienteListItem } from "../types";

function toPayload(v: ClienteFormValues) {
  return {
    nombre_completo: v.nombre_completo,
    rfc: v.rfc,
    tipo_persona: v.tipo_persona,
    razon_social: v.razon_social || null,
    forma_pago: v.forma_pago,
    contador_asignado_id: v.contador_asignado_id,
    giro: v.giro,
    telefono: v.telefono,
    correo: v.correo,
    codigo_postal: v.codigo_postal,
    calle: v.calle,
    no_exterior: v.no_exterior,
    no_interior: v.no_interior || null,
    colonia: v.colonia,
    ciudad: v.ciudad,
    estado: v.estado,
    regimenes: v.regimenes,
    tiene_trabajadores: v.tiene_trabajadores,
    tipo_nomina: v.tiene_trabajadores ? v.tipo_nomina || null : null,
    contacto_principal: v.contacto_principal,
    contacto_pagos: v.tiene_contacto_pagos ? v.contacto_pagos : null,
  };
}

export const clientsApi = {
  list: async (filters: ClienteFilters) => {
    const res = await api.get<ApiResponse<ClienteListItem[]>>("/clients", {
      params: toQueryParams(filters),
    });
    return res.data;
  },

  create: async (values: ClienteFormValues) => {
    const res = await api.post<ApiResponse<Cliente>>("/clients", toPayload(values));
    return res.data.data;
  },
};
