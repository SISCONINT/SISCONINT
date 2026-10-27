import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormField, inputClass } from "@/shared/components/FormField";
import { SearchableSelect } from "@/shared/components/SearchableSelect";
import { ApiError } from "@/shared/api/types";
import { useClienteOptions } from "@/features/clients/api/useClients";
import { useColaboradorOptions } from "@/features/users/api/useUsers";
import { useCatalog } from "@/features/catalog/api/useCatalog";
import { taskSchema } from "../schemas/task.schema";
import type { TareaFormValues } from "../types";

interface Props {
  defaultValues?: Partial<TareaFormValues>;
  submitLabel: string;
  pending?: boolean;
  serverError?: unknown;
  onSubmit: (values: TareaFormValues) => void;
  onCancel?: () => void;
}

function errorMessage(e: unknown): string | null {
  if (!e) return null;
  if (e instanceof ApiError) return e.message;
  return "Ocurrió un error inesperado.";
}

export function TaskForm({ defaultValues, submitLabel, pending, serverError, onSubmit, onCancel }: Props) {
  const [clienteQuery, setClienteQuery] = useState("");
  const [responsableQuery, setResponsableQuery] = useState("");
  const { options: clienteOptions, isLoading: loadingClientes } = useClienteOptions(clienteQuery);
  const { options: responsableOptions, isLoading: loadingResponsables } = useColaboradorOptions(responsableQuery);
  const { data: categorias } = useCatalog({ solo_activas: true });

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = useForm<TareaFormValues>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      titulo: "",
      descripcion: "",
      cliente_id: null,
      categoria_id: null,
      asignado_id: null,
      fecha_limite: "",
      hora_limite: "23:59",
      prioridad: "MEDIA",
      horas_estimadas: "",
      notificar_cliente: true,
      ...defaultValues,
    },
  });

  const message = errorMessage(serverError);

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      {message && (
        <div role="alert" className="rounded-lg bg-red-50 px-3 py-2.5 text-sm font-medium text-danger">
          {message}
        </div>
      )}

      <FormField label="Título de la tarea" htmlFor="titulo" required error={errors.titulo?.message}>
        <input id="titulo" className={inputClass + " pl-4"} {...register("titulo")} />
      </FormField>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Cliente asociado" htmlFor="cliente_id" required error={errors.cliente_id?.message}>
          <Controller
            control={control}
            name="cliente_id"
            render={({ field }) => (
              <SearchableSelect
                value={field.value}
                onChange={field.onChange}
                options={clienteOptions}
                loading={loadingClientes}
                query={clienteQuery}
                onQueryChange={setClienteQuery}
                placeholder="Buscar cliente…"
                invalid={!!errors.cliente_id}
              />
            )}
          />
        </FormField>

        <FormField label="Contador / responsable" htmlFor="asignado_id" required error={errors.asignado_id?.message}>
          <Controller
            control={control}
            name="asignado_id"
            render={({ field }) => (
              <SearchableSelect
                value={field.value}
                onChange={field.onChange}
                options={responsableOptions}
                loading={loadingResponsables}
                query={responsableQuery}
                onQueryChange={setResponsableQuery}
                placeholder="Buscar colaborador…"
                invalid={!!errors.asignado_id}
              />
            )}
          />
        </FormField>

        <FormField label="Categoría / subcategoría" htmlFor="categoria_id" required error={errors.categoria_id?.message}>
          <Controller
            control={control}
            name="categoria_id"
            render={({ field }) => (
              <select
                id="categoria_id"
                className={inputClass + " pl-4"}
                aria-invalid={!!errors.categoria_id}
                value={field.value ?? ""}
                onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
              >
                <option value="">Selecciona…</option>
                {(categorias ?? []).map((cat) => (
                  <optgroup key={cat.id} label={cat.nombre}>
                    {cat.subcategorias.map((sub) => (
                      <option key={sub.id} value={sub.id}>
                        {sub.nombre}
                      </option>
                    ))}
                  </optgroup>
                ))}
              </select>
            )}
          />
        </FormField>

        <FormField label="Prioridad" htmlFor="prioridad" required error={errors.prioridad?.message}>
          <select id="prioridad" className={inputClass + " pl-4"} {...register("prioridad")}>
            <option value="BAJA">Baja</option>
            <option value="MEDIA">Media</option>
            <option value="ALTA">Alta</option>
          </select>
        </FormField>

        <FormField label="Fecha límite" htmlFor="fecha_limite" required error={errors.fecha_limite?.message}>
          <input id="fecha_limite" type="date" className={inputClass + " pl-4"} {...register("fecha_limite")} />
        </FormField>

        <FormField label="Hora de corte" htmlFor="hora_limite" required error={errors.hora_limite?.message}>
          <input id="hora_limite" type="time" className={inputClass + " pl-4"} {...register("hora_limite")} />
        </FormField>

        <FormField
          label="Horas estimadas"
          htmlFor="horas_estimadas"
          error={errors.horas_estimadas?.message}
          hint="Múltiplos de 0.5, opcional"
        >
          <input id="horas_estimadas" type="number" step="0.5" min="0.5" max="200" className={inputClass + " pl-4"} {...register("horas_estimadas")} />
        </FormField>
      </div>

      <FormField label="Descripción" htmlFor="descripcion" error={errors.descripcion?.message}>
        <textarea id="descripcion" rows={4} className={inputClass + " pl-4 pt-3"} {...register("descripcion")} />
      </FormField>

      <label className="flex items-center gap-2 text-sm text-ink">
        <input type="checkbox" className="size-4 rounded border-line accent-navy-900" {...register("notificar_cliente")} />
        Notificar al cliente cuando se complete
      </label>

      <div className="flex justify-end gap-2 border-t border-line pt-4">
        {onCancel && (
          <button type="button" onClick={onCancel} className="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink hover:bg-field">
            Cancelar
          </button>
        )}
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-gold-300 px-5 py-2.5 text-sm font-semibold text-ink hover:brightness-95 disabled:opacity-60"
        >
          {pending ? "Guardando…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
