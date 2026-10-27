import {
  keepPreviousData,
  useMutation,
  useQueries,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { clientsApi } from "./clientsApi";
import { ESTATUS_CLIENTE } from "../constants";
import type {
  ClientesPage,
  ClientesQuery,
} from "../types";

export function useClients(filters: ClientesQuery) {
  return useQuery({
    queryKey: ["clients", "list", filters],
    queryFn: () => clientsApi.list(filters),
    placeholderData: keepPreviousData,
    staleTime: 15_000,
  });
}

/** Totales por estatus para las tarjetas de la cartera (3 consultas cacheadas). */
export function useClientsSummary() {
  return useQueries({
    queries: ESTATUS_CLIENTE.map((estatus) => ({
      queryKey: ["clients", "summary", estatus],
      queryFn: () =>
        clientsApi.list({ q: "", estatus, tipo_persona: null, page: 1 }),
      select: (page: ClientesPage) => page.meta.total,
      staleTime: 60_000,
    })),
  });
}

export function useClientDetail(id: number, enabled = true) {
  return useQuery({
    queryKey: ["clients", "detail", id],
    queryFn: () => clientsApi.get(id),
    enabled: enabled && Number.isInteger(id) && id > 0,
    retry: false,
    staleTime: 5 * 60_000,
  });
}

export function useCreateClient() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: clientsApi.create,
    onSuccess: (cliente) => {
      queryClient.setQueryData(["clients", "detail", cliente.id], cliente);
      queryClient.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

/** Contadores activos para asignar o filtrar. Solo Dueño/Administrador tienen `user:list`. */
export function useAccountants(enabled: boolean) {
  return useQuery({
    queryKey: ["users", "accountants"],
    queryFn: clientsApi.listAccountants,
    enabled,
    staleTime: 5 * 60_000,
  });
}
