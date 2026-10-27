import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { SelectOption } from "@/shared/components/SearchableSelect";
import { usersApi } from "./usersApi";
import type { ColaboradorFilters, ColaboradorFormValues } from "../types";
import { ROLE_LABELS } from "@/shared/constants/roles";

export function useUsers(filters: ColaboradorFilters) {
  return useQuery({
    queryKey: ["users", filters],
    queryFn: () => usersApi.list(filters),
    placeholderData: (prev) => prev,
  });
}

export function useUser(id: number | undefined) {
  return useQuery({
    queryKey: ["users", id],
    queryFn: () => usersApi.get(id as number),
    enabled: id !== undefined,
  });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ColaboradorFormValues) => usersApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });
}

export function useUpdateUser(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ColaboradorFormValues) => usersApi.update(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      qc.invalidateQueries({ queryKey: ["users", id] });
    },
  });
}

export function useDeactivationImpact(id: number | undefined) {
  return useQuery({
    queryKey: ["users", id, "deactivation-impact"],
    queryFn: () => usersApi.deactivationImpact(id as number),
    enabled: id !== undefined,
  });
}

/** Opciones para selects buscables (contador asignado, responsable de tarea, etc.). */
export function useColaboradorOptions(q: string, filters?: Pick<ColaboradorFilters, "rol">) {
  const query = useQuery({
    queryKey: ["users", "options", q, filters],
    queryFn: () => usersApi.list({ q: q || undefined, estatus: "ACTIVO", ...filters }),
  });

  const options: SelectOption[] = (query.data?.data ?? []).map((u) => ({
    value: u.id,
    label: u.nombre_completo,
    sublabel: `${ROLE_LABELS[u.rol]} · ${u.correo_institucional}`,
  }));

  return { options, isLoading: query.isLoading };
}

export function useDeactivateUser(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (reasignarA?: number | null) => usersApi.deactivate(id, reasignarA),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      qc.invalidateQueries({ queryKey: ["users", id] });
    },
  });
}
