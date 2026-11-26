import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { obligationsApi } from "./obligationsApi";
import type { ObligacionFilters } from "../types";

export function useObligations(filters: ObligacionFilters) {
  return useQuery({
    queryKey: ["obligations", filters],
    queryFn: () => obligationsApi.list(filters),
  });
}

export function useCreateObligation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: obligationsApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["obligations"] }),
  });
}

export function useDeactivateObligation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => obligationsApi.deactivate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["obligations"] }),
  });
}
