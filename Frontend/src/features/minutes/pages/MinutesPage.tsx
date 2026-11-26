import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { FileText, Plus, Trash2, X } from "lucide-react";
import { ClientPicker } from "@/shared/components/ClientPicker";
import { TextField } from "@/shared/components/TextField";
import { Pagination } from "@/shared/components/Pagination";
import { BTN_PRIMARY, BTN_SECONDARY } from "@/shared/components/buttons";
import { plainInputClass, FormField } from "@/shared/components/FormField";
import { ApiError } from "@/shared/api/types";
import { useCreateMinute, useDeleteMinute, useMinutes } from "../api/useMinutes";
import type { MinutaFormValues } from "../types";

const today = () => new Date().toISOString().slice(0, 10);

const EMPTY: MinutaFormValues = { cliente_id: "", titulo: "", fecha: today(), participantes: "", acuerdos: "" };

function NewMinuteForm({ onClose }: { onClose: () => void }) {
  const mutation = useCreateMinute();
  const { register, handleSubmit, control, formState: { errors } } = useForm<MinutaFormValues>({ defaultValues: EMPTY });

  const onSubmit = (values: MinutaFormValues) => {
    mutation.mutate(
      {
        cliente_id: values.cliente_id === "" ? undefined : values.cliente_id,
        titulo: values.titulo.trim(),
        fecha: values.fecha,
        participantes: values.participantes.trim() || undefined,
        acuerdos: values.acuerdos.trim(),
      },
      { onSuccess: onClose },
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ink">Nueva minuta</h2>
        <button type="button" onClick={onClose} className="text-muted hover:text-ink" aria-label="Cerrar">
          <X size={18} />
        </button>
      </div>

      {mutation.error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-danger">
          {mutation.error instanceof ApiError ? mutation.error.message : "Ocurrió un error inesperado."}
        </p>
      )}

      <TextField label="Título" required maxLength={150} registration={register("titulo", { required: true })} error={errors.titulo as never} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Controller control={control} name="cliente_id" render={({ field }) => (
          <ClientPicker value={field.value} onChange={field.onChange} allowEmpty label="Cliente (opcional)" />
        )} />
        <TextField label="Fecha" required type="date" registration={register("fecha", { required: true })} error={errors.fecha as never} />
      </div>

      <TextField label="Participantes" maxLength={300} placeholder="Nombres separados por coma" registration={register("participantes")} />

      <FormField label="Acuerdos" htmlFor="acuerdos" required error={errors.acuerdos?.message}>
        <textarea id="acuerdos" rows={4} className={plainInputClass} {...register("acuerdos", { required: "Campo obligatorio" })} />
      </FormField>

      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className={BTN_SECONDARY}>Cancelar</button>
        <button type="submit" disabled={mutation.isPending} className={BTN_PRIMARY}>
          {mutation.isPending ? "Guardando…" : "Guardar minuta"}
        </button>
      </div>
    </form>
  );
}

export function MinutesPage() {
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading } = useMinutes({ page });
  const deleteMutation = useDeleteMinute();

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
            <span>Gestión</span>
            <span aria-hidden="true">/</span>
            <span className="font-semibold text-navy-800">Minutas</span>
          </nav>
          <div className="flex items-center gap-2">
            <FileText size={20} className="text-gold-700" />
            <h1 className="font-display text-2xl font-bold text-ink">Minutas y acuerdos</h1>
          </div>
          <p className="mt-1.5 text-sm text-muted">Bitácora de reuniones, decisiones y acuerdos con clientes.</p>
        </div>
        <button type="button" onClick={() => setShowForm((s) => !s)} className={BTN_PRIMARY}>
          <Plus size={16} /> Nueva minuta
        </button>
      </header>

      {showForm && <NewMinuteForm onClose={() => setShowForm(false)} />}

      {isLoading ? (
        <p className="text-sm text-muted">Cargando minutas…</p>
      ) : (data?.items.length ?? 0) === 0 ? (
        <div className="card p-10 text-center text-sm text-muted">Sin minutas registradas.</div>
      ) : (
        <div className="flex flex-col gap-3">
          {data!.items.map((m) => (
            <article key={m.id} className="card p-4">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-ink">{m.titulo}</p>
                  <p className="text-[12px] text-muted">
                    {new Date(m.fecha + "T00:00:00").toLocaleDateString("es-MX")} · {m.cliente_nombre ?? "Interna"} · {m.creador_nombre}
                  </p>
                </div>
                <button type="button" onClick={() => deleteMutation.mutate(m.id)} className="text-muted hover:text-danger" aria-label="Eliminar minuta">
                  <Trash2 size={16} />
                </button>
              </div>
              {m.participantes && <p className="mt-2 text-[12px] text-muted">Participantes: {m.participantes}</p>}
              <p className="mt-2 whitespace-pre-wrap text-sm text-ink/90">{m.acuerdos}</p>
            </article>
          ))}
        </div>
      )}

      {data?.meta && <Pagination page={page} perPage={data.meta.per_page} total={data.meta.total} onChange={setPage} />}
    </div>
  );
}
