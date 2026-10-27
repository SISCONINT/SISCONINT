import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { tasksApi } from "./tasksApi";
import type { TareaBoardFilters, TareaFormValues, TareaListFilters } from "../types";

export function useTasks(filters: TareaListFilters) {
  return useQuery({
    queryKey: ["tasks", filters],
    queryFn: () => tasksApi.list(filters),
    placeholderData: (prev) => prev,
  });
}

export function useTaskBoard(filters: TareaBoardFilters) {
  return useQuery({
    queryKey: ["tasks", "board", filters],
    queryFn: () => tasksApi.board(filters),
    placeholderData: (prev) => prev,
  });
}

export function useTask(id: number | undefined) {
  return useQuery({
    queryKey: ["tasks", id],
    queryFn: () => tasksApi.get(id as number),
    enabled: id !== undefined,
  });
}

function invalidateAll(qc: ReturnType<typeof useQueryClient>, id?: number) {
  qc.invalidateQueries({ queryKey: ["tasks"] });
  if (id !== undefined) qc.invalidateQueries({ queryKey: ["tasks", id] });
}

export function useCreateTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: TareaFormValues) => tasksApi.create(values),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useUpdateTask(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (values: TareaFormValues) => tasksApi.update(id, values),
    onSuccess: () => invalidateAll(qc, id),
  });
}

export function useMoveTask(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ estado, confirmar }: { estado: string; confirmar?: boolean }) =>
      tasksApi.move(id, estado, confirmar),
    onSuccess: () => invalidateAll(qc, id),
  });
}

export function useDeleteTask() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => tasksApi.remove(id),
    onSuccess: () => invalidateAll(qc),
  });
}
