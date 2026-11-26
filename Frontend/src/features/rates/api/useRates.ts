import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ratesApi } from "./ratesApi";

export function useRates() {
  return useQuery({
    queryKey: ["rates"],
    queryFn: ratesApi.list,
  });
}

export function useUpsertRate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ colaboradorId, montoHora }: { colaboradorId: number; montoHora: number }) =>
      ratesApi.upsert(colaboradorId, montoHora),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["rates"] }),
  });
}
