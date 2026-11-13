import { useMemo, useState, type FormEvent } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Banknote, CircleDollarSign, Pencil, Wallet } from "lucide-react";
import { api } from "@/shared/api/client";
import {
  BTN_PRIMARY,
  BTN_SECONDARY,
  INPUT_CLASS,
  NIVEL_TARIFA_LABELS,
} from "@/shared/constants/constants";
import {
  Badge,
  ErrorState,
  FormField,
  LoadingState,
  Modal,
  Notice,
  PageHeader,
  StatCard,
} from "@/shared/components/components";
import { formatDate, formatDateTime, formatMoney, getErrorMessage, todayISO } from "@/shared/utils/utils";

interface RateRow {
  id: number | null;
  nivel: string;
  monto_hora_mxn: number | null;
  vigencia_inicio: string | null;
  vigencia_fin: string | null;
  vigente: boolean;
  updated_at: string | null;
}

interface FormState {
  monto_hora_mxn: string;
  vigencia_inicio: string;
  vigencia_fin: string;
}

const EMPTY_FORM: FormState = {
  monto_hora_mxn: "",
  vigencia_inicio: todayISO(),
  vigencia_fin: "",
};

export function RatesPage() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState<RateRow | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const query = useQuery({
    queryKey: ["rates"],
    queryFn: async () => {
      const res = await api.get<{ data: RateRow[] }>("/rates");
      return res.data.data ?? [];
    },
    staleTime: 30_000,
  });

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!editing) return;
      await api.put(`/rates/${editing.nivel}`, {
        monto_hora_mxn: Number(form.monto_hora_mxn),
        vigencia_inicio: form.vigencia_inicio || null,
        vigencia_fin: form.vigencia_fin || null,
      });
    },
    onSuccess: () => {
      setNotice("Tarifa guardada.");
      setError("");
      setEditing(null);
      queryClient.invalidateQueries({ queryKey: ["rates"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => setError(getErrorMessage(err)),
  });

  const rows = useMemo(() => query.data ?? [], [query.data]);

  const summary = useMemo(() => {
    const conTarifa = rows.filter((row) => row.monto_hora_mxn !== null);
    const promedio =
      conTarifa.length > 0
        ? conTarifa.reduce((acc, row) => acc + (row.monto_hora_mxn ?? 0), 0) / conTarifa.length
        : null;
    return { total: rows.length, conTarifa: conTarifa.length, promedio };
  }, [rows]);

  const openEdit = (row: RateRow) => {
    setEditing(row);
    setForm({
      monto_hora_mxn: row.monto_hora_mxn !== null ? String(row.monto_hora_mxn) : "",
      // Una nueva vigencia desde hoy conserva el monto histórico anterior.
      vigencia_inicio: todayISO(),
      vigencia_fin: "",
    });
    setError("");
  };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    saveMutation.mutate();
  };

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 13 · Tarifas por nivel"
        title="Catálogo de Tarifas"
        description="Define el costo por hora de cada nivel de escalafón. Se usa para calcular el costo estimado del dashboard."
      />

      {notice && <Notice tone="success">{notice}</Notice>}
      {error && <Notice tone="danger">{error}</Notice>}

      <section className="grid gap-3 sm:grid-cols-3">
        <StatCard
          label="Niveles de escalafón"
          value={summary.total}
          icon={<Wallet size={18} />}
        />
        <StatCard
          label="Con tarifa vigente"
          value={summary.conTarifa}
          hint={`${summary.total - summary.conTarifa} sin tarifa`}
          icon={<CircleDollarSign size={18} />}
          tone="success"
        />
        <StatCard
          label="Tarifa promedio"
          value={summary.promedio !== null ? formatMoney(summary.promedio) : "—"}
          hint="Solo niveles con tarifa"
          icon={<Banknote size={18} />}
        />
      </section>

      {query.isLoading && <LoadingState label="Cargando tarifas…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {rows.length > 0 && (
        <section className="card overflow-x-auto">
          <table className="w-full text-left">
            <thead className="border-b border-line bg-app/60">
              <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                <th className="px-5 py-3">Nivel</th>
                <th className="px-4 py-3">Tarifa por hora</th>
                <th className="px-4 py-3">Vigencia</th>
                <th className="px-4 py-3">Estatus</th>
                <th className="px-4 py-3">Actualizada</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {rows.map((row) => (
                <tr key={row.nivel} className="hover:bg-app/50">
                  <td className="px-5 py-3 text-sm font-semibold text-ink">
                    {NIVEL_TARIFA_LABELS[row.nivel] ?? row.nivel}
                  </td>
                  <td className="px-4 py-3 text-xs font-semibold text-ink">
                    {row.monto_hora_mxn !== null ? (
                      formatMoney(row.monto_hora_mxn)
                    ) : (
                      <span className="font-normal text-amber-700">Sin tarifa</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {row.vigencia_inicio ? formatDate(row.vigencia_inicio) : "—"}
                    {row.vigencia_fin ? ` a ${formatDate(row.vigencia_fin)}` : " en adelante"}
                  </td>
                  <td className="px-4 py-3">
                    <Badge
                      className={
                        row.vigente
                          ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                          : "bg-slate-100 text-slate-600 ring-slate-200"
                      }
                    >
                      {row.vigente ? "Vigente" : "Sin tarifa"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">
                    {row.updated_at ? formatDateTime(row.updated_at) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button type="button" className={BTN_SECONDARY} onClick={() => openEdit(row)}>
                      <Pencil size={14} /> {row.vigente ? "Editar" : "Asignar"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <Modal
        open={editing !== null}
        onClose={() => setEditing(null)}
        title={editing?.vigente ? "Editar tarifa" : "Asignar tarifa"}
        description={
          editing
            ? `Nivel ${NIVEL_TARIFA_LABELS[editing.nivel] ?? editing.nivel}. Las vigencias anteriores conservan su monto histórico.`
            : undefined
        }
      >
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={submit}>
          <FormField
            label="Monto por hora (MXN)"
            required
            className="sm:col-span-2"
            hint="Mayor a 0 y hasta 999,999.99"
          >
            <input
              type="number"
              min={0.01}
              max={999999.99}
              step={0.01}
              value={form.monto_hora_mxn}
              onChange={(event) => setForm({ ...form, monto_hora_mxn: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Vigencia desde" required>
            <input
              type="date"
              value={form.vigencia_inicio}
              onChange={(event) => setForm({ ...form, vigencia_inicio: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <FormField label="Vigencia hasta" hint="Déjalo vacío si no tiene fecha de fin">
            <input
              type="date"
              value={form.vigencia_fin}
              onChange={(event) => setForm({ ...form, vigencia_fin: event.target.value })}
              className={INPUT_CLASS}
            />
          </FormField>
          <div className="flex justify-end gap-2 sm:col-span-2">
            <button
              type="button"
              className={BTN_SECONDARY}
              onClick={() => setEditing(null)}
              disabled={saveMutation.isPending}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className={BTN_PRIMARY}
              disabled={
                saveMutation.isPending ||
                !form.monto_hora_mxn ||
                Number(form.monto_hora_mxn) <= 0 ||
                !form.vigencia_inicio ||
                (form.vigencia_fin !== "" && form.vigencia_fin < form.vigencia_inicio)
              }
            >
              {saveMutation.isPending ? "Guardando…" : "Guardar tarifa"}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
