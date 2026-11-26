import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { minutesApi } from "./minutesApi";
import type { MinutaFilters } from "../types";

export function useMinutes(filters: MinutaFilters) {
  return useQuery({
    queryKey: ["minutes", filters],
    queryFn: () => minutesApi.list(filters),
  });
}

export function useCreateMinute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: minutesApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["minutes"] }),
  });
}

export function useDeleteMinute() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => minutesApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["minutes"] }),
  });
}
