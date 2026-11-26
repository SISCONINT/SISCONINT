import { useState } from "react";
import { Banknote, Check, Pencil, X } from "lucide-react";
import { DataTable, type Column } from "@/shared/components/DataTable";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { useRates, useUpsertRate } from "../api/useRates";
import type { TarifaRow } from "../types";

function EditableRate({ row }: { row: TarifaRow }) {
  const [editing, setEditing] = useState(false);
  const [value, setValue] = useState(row.monto_hora?.toString() ?? "");
  const mutation = useUpsertRate();

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => {
          setValue(row.monto_hora?.toString() ?? "");
          setEditing(true);
        }}
        className="flex items-center gap-1.5 text-sm font-medium text-ink hover:text-navy-800"
      >
        {row.monto_hora !== null ? (
          <>${row.monto_hora.toFixed(2)} {row.moneda}/hr</>
        ) : (
          <span className="text-muted italic">Sin tarifa</span>
        )}
        <Pencil size={13} className="text-muted" />
      </button>
    );
  }

  const save = () => {
    const monto = Number(value);
    if (!Number.isFinite(monto) || monto <= 0) return;
    mutation.mutate(
      { colaboradorId: row.colaborador_id, montoHora: monto },
      { onSuccess: () => setEditing(false) },
    );
  };

  return (
    <div className="flex items-center gap-1.5">
      <input
        autoFocus
        type="number"
        step="0.01"
        min="0.01"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && save()}
        className="w-28 rounded-md border border-line bg-field px-2 py-1 text-sm text-ink outline-none focus:ring-2 focus:ring-gold-500"
      />
      <button type="button" onClick={save} disabled={mutation.isPending} className="text-emerald-600 hover:brightness-90" aria-label="Guardar">
        <Check size={16} />
      </button>
      <button type="button" onClick={() => setEditing(false)} className="text-muted hover:text-ink" aria-label="Cancelar">
        <X size={16} />
      </button>
    </div>
  );
}

export function RatesPage() {
  const { data, isLoading } = useRates();

  const columns: Column<TarifaRow>[] = [
    { header: "Colaborador", cell: (r) => <span className="font-medium text-ink">{r.colaborador_nombre}</span> },
    { header: "Rol", cell: (r) => ROLE_LABELS[r.rol] },
    { header: "Tarifa por hora", cell: (r) => <EditableRate row={r} /> },
  ];

  return (
    <div className="mx-auto flex w-full max-w-4xl flex-col gap-4">
      <header>
        <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
          <span>Administración</span>
          <span aria-hidden="true">/</span>
          <span className="font-semibold text-navy-800">Tarifas</span>
        </nav>
        <div className="flex items-center gap-2">
          <Banknote size={20} className="text-gold-700" />
          <h1 className="font-display text-2xl font-bold text-ink">Tarifas por colaborador</h1>
        </div>
        <p className="mt-1.5 text-sm text-muted">
          HU_57-62: la tarifa por hora de cada colaborador se usa para calcular el costo estimado del Dashboard.
        </p>
      </header>

      <div className="card">
        <DataTable columns={columns} rows={data ?? []} getRowKey={(r) => r.colaborador_id} isLoading={isLoading} emptyMessage="Sin colaboradores activos." />
      </div>
    </div>
  );
}
