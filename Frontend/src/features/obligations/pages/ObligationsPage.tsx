import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { Plus, Repeat, ShieldOff, X } from "lucide-react";
import { DataTable, type Column } from "@/shared/components/DataTable";
import { Pagination } from "@/shared/components/Pagination";
import { ClientPicker } from "@/shared/components/ClientPicker";
import { TextField } from "@/shared/components/TextField";
import { SelectField } from "@/shared/components/SelectField";
import { BTN_PRIMARY, BTN_SECONDARY } from "@/shared/components/buttons";
import { ApiError } from "@/shared/api/types";
import { useCreateObligation, useDeactivateObligation, useObligations } from "../api/useObligations";
import { PERIODICIDAD_LABELS, PERIODICIDADES, type Obligacion, type ObligacionFormValues } from "../types";

const EMPTY: ObligacionFormValues = {
  cliente_id: "",
  categoria_id: "",
  nombre: "",
  periodicidad: "MENSUAL",
  dia_limite: "17",
  notas: "",
};

function NewObligationForm({ onClose }: { onClose: () => void }) {
  const mutation = useCreateObligation();
  const { register, handleSubmit, control, formState: { errors } } = useForm<ObligacionFormValues>({ defaultValues: EMPTY });

  const onSubmit = (values: ObligacionFormValues) => {
    if (values.cliente_id === "") return;
    mutation.mutate(
      {
        cliente_id: values.cliente_id,
        nombre: values.nombre.trim(),
        periodicidad: values.periodicidad,
        dia_limite: Number(values.dia_limite),
        notas: values.notas.trim() || undefined,
      },
      { onSuccess: onClose },
    );
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ink">Nueva obligación periódica</h2>
        <button type="button" onClick={onClose} className="text-muted hover:text-ink" aria-label="Cerrar">
          <X size={18} />
        </button>
      </div>

      {mutation.error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-danger">
          {mutation.error instanceof ApiError ? mutation.error.message : "Ocurrió un error inesperado."}
        </p>
      )}

      <Controller
        control={control}
        name="cliente_id"
        rules={{ required: true }}
        render={({ field }) => (
          <ClientPicker value={field.value} onChange={field.onChange} required error={field.value === "" ? "Selecciona un cliente" : undefined} />
        )}
      />

      <TextField label="Nombre de la obligación" required maxLength={150} placeholder="Ej. Declaración mensual de IVA" registration={register("nombre", { required: true, minLength: 1 })} error={errors.nombre as never} />

      <div className="grid grid-cols-2 gap-4">
        <SelectField
          label="Periodicidad"
          required
          registration={register("periodicidad")}
          options={PERIODICIDADES.map((p) => ({ value: p, label: PERIODICIDAD_LABELS[p] }))}
        />
        <TextField label="Día límite" required type="number" min={1} max={31} registration={register("dia_limite", { required: true })} error={errors.dia_limite as never} />
      </div>

      <TextField label="Notas" maxLength={300} registration={register("notas")} />

      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className={BTN_SECONDARY}>Cancelar</button>
        <button type="submit" disabled={mutation.isPending} className={BTN_PRIMARY}>
          {mutation.isPending ? "Guardando…" : "Registrar"}
        </button>
      </div>
    </form>
  );
}

export function ObligationsPage() {
  const [page, setPage] = useState(1);
  const [soloActivas, setSoloActivas] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const { data, isLoading } = useObligations({ solo_activas: soloActivas, page });
  const deactivateMutation = useDeactivateObligation();

  const columns: Column<Obligacion>[] = [
    { header: "Cliente", cell: (o) => o.cliente_nombre ?? "—" },
    { header: "Obligación", cell: (o) => <span className="font-medium text-ink">{o.nombre}</span> },
    { header: "Periodicidad", cell: (o) => PERIODICIDAD_LABELS[o.periodicidad] },
    { header: "Día límite", cell: (o) => `Día ${o.dia_limite}` },
    {
      header: "Estatus",
      cell: (o) => (
        <span className={o.activa ? "text-emerald-700" : "text-muted"}>{o.activa ? "Activa" : "Inactiva"}</span>
      ),
    },
    {
      header: "",
      cell: (o) =>
        o.activa && (
          <button
            type="button"
            onClick={() => deactivateMutation.mutate(o.id)}
            disabled={deactivateMutation.isPending}
            className="inline-flex items-center gap-1 text-[13px] font-medium text-danger hover:underline"
          >
            <ShieldOff size={13} /> Desactivar
          </button>
        ),
    },
  ];

  return (
    <div className="mx-auto flex w-full max-w-5xl flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
            <span>Gestión</span>
            <span aria-hidden="true">/</span>
            <span className="font-semibold text-navy-800">Obligaciones periódicas</span>
          </nav>
          <div className="flex items-center gap-2">
            <Repeat size={20} className="text-gold-700" />
            <h1 className="font-display text-2xl font-bold text-ink">Obligaciones periódicas</h1>
          </div>
          <p className="mt-1.5 text-sm text-muted">Declaraciones recurrentes de cada cliente, con su día límite de cada periodo.</p>
        </div>
        <button type="button" onClick={() => setShowForm((s) => !s)} className={BTN_PRIMARY}>
          <Plus size={16} /> Nueva obligación
        </button>
      </header>

      {showForm && <NewObligationForm onClose={() => setShowForm(false)} />}

      <label className="flex w-fit items-center gap-2 text-sm text-ink">
        <input type="checkbox" checked={soloActivas} onChange={(e) => { setSoloActivas(e.target.checked); setPage(1); }} className="size-4 rounded border-line accent-navy-900" />
        Solo activas
      </label>

      <div className="card">
        <DataTable columns={columns} rows={data?.items ?? []} getRowKey={(o) => o.id} isLoading={isLoading} emptyMessage="Sin obligaciones registradas." />
        {data?.meta && <Pagination page={page} perPage={data.meta.per_page} total={data.meta.total} onChange={setPage} />}
      </div>
    </div>
  );
}
