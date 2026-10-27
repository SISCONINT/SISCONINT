import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { SelectOption } from "@/shared/components/SearchableSelect";
import { clientsApi } from "./clientsApi";
import type { ClienteFilters, ClienteFormValues } from "../types";

export function useClients(filters: ClienteFilters) {
  return useQuery({
    queryKey: ["clients", filters],
    queryFn: () => clientsApi.list(filters),
    placeholderData: (prev) => prev,
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: ClienteFormValues) => clientsApi.create(values),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["clients"] }),
  });
}

/** Opciones para selects buscables (cliente asociado a una tarea, por ejemplo). */
export function useClienteOptions(q: string) {
  const query = useQuery({
    queryKey: ["clients", "options", q],
    queryFn: () => clientsApi.list({ q: q || undefined, estatus: "ACTIVO" }),
  });

  const options: SelectOption[] = (query.data?.data ?? []).map((c) => ({
    value: c.id,
    label: c.razon_social || c.nombre_completo,
    sublabel: `RFC ${c.rfc}`,
  }));

  return { options, isLoading: query.isLoading };
}
