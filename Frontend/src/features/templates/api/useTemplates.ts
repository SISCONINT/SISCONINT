import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { templatesApi } from "./templatesApi";
import type { PlantillaFormValues } from "../types";

export function useTemplates() {
  return useQuery({ queryKey: ["templates"], queryFn: templatesApi.list });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: PlantillaFormValues) => templatesApi.create(values),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useUpdateTemplate(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: Omit<PlantillaFormValues, "clave">) => templatesApi.update(id, values),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}
