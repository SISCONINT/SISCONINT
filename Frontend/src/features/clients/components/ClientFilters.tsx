import { Loader2, Search, SlidersHorizontal, X } from "lucide-react";
import clsx from "clsx";
import { plainInputClass } from "@/shared/components/FormField";
import {
  ESTATUS_FILTER_LABELS,
  TIPO_PERSONA_LABELS,
} from "../constants";
import type {
  AccountantOption,
  EstatusCliente,
  TipoPersona,
} from "../types";

interface Props {
  q: string;
  estatus: EstatusCliente;
  tipoPersona: TipoPersona | null;
  contador?: number;
  canFilterByAccountant: boolean;
  accountants: AccountantOption[];
  accountantsLoading: boolean;
  accountantsError: boolean;
  total: number;
  isFetching: boolean;
  onSearchChange: (value: string) => void;
  onEstatusChange: (value: EstatusCliente) => void;
  onTipoPersonaChange: (value: TipoPersona | null) => void;
  onContadorChange: (value: number | undefined) => void;
  onClear: () => void;
}

export function ClientFilters({
  q,
  estatus,
  tipoPersona,
  contador,
  canFilterByAccountant,
  accountants,
  accountantsLoading,
  accountantsError,
  total,
  isFetching,
  onSearchChange,
  onEstatusChange,
  onTipoPersonaChange,
  onContadorChange,
  onClear,
}: Props) {
  const hasFilters = q !== "" || tipoPersona !== null || contador !== undefined || estatus !== "ACTIVO";

  const quickViews: { label: string; active: boolean; apply: () => void }[] = [
    {
      label: "Activos",
      active: estatus === "ACTIVO" && !tipoPersona && contador === undefined,
      apply: () => {
        onEstatusChange("ACTIVO");
        onTipoPersonaChange(null);
        onContadorChange(undefined);
      },
    },
    {
      label: "Personas morales",
      active: estatus === "ACTIVO" && tipoPersona === "MORAL",
      apply: () => {
        onEstatusChange("ACTIVO");
        onTipoPersonaChange("MORAL");
      },
    },
    {
      label: "Personas físicas",
      active: estatus === "ACTIVO" && tipoPersona === "FISICA",
      apply: () => {
        onEstatusChange("ACTIVO");
        onTipoPersonaChange("FISICA");
      },
    },
    {
      label: "Pausados",
      active: estatus === "PAUSADO" && !tipoPersona,
      apply: () => {
        onEstatusChange("PAUSADO");
        onTipoPersonaChange(null);
      },
    },
    {
      label: "Bajas",
      active: estatus === "BAJA" && !tipoPersona,
      apply: () => {
        onEstatusChange("BAJA");
        onTipoPersonaChange(null);
      },
    },
  ];

  return (
    <section className="card p-4" aria-label="Filtros de la cartera">
      <div className="grid gap-2.5 lg:grid-cols-12">
        <div className="relative lg:col-span-4">
          <Search
            size={16}
            aria-hidden="true"
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
          />
          <label htmlFor="client-search" className="sr-only">
            Buscar contribuyente
          </label>
          <input
            id="client-search"
            type="search"
            value={q}
            onChange={(event) => onSearchChange(event.target.value)}
            placeholder="Buscar por nombre, razón social o RFC…"
            className={clsx(plainInputClass, "py-2.5 pl-9 pr-9 text-[13px]")}
          />
          {q !== "" && (
            <button
              type="button"
              onClick={() => onSearchChange("")}
              aria-label="Limpiar búsqueda"
              className="absolute right-2.5 top-1/2 grid size-6 -translate-y-1/2 place-items-center rounded text-muted transition hover:bg-line hover:text-ink"
            >
              <X size={14} />
            </button>
          )}
        </div>

        <div className={clsx(canFilterByAccountant ? "lg:col-span-2" : "lg:col-span-3")}>
          <label htmlFor="client-estatus" className="sr-only">
            Estatus
          </label>
          <select
            id="client-estatus"
            value={estatus}
            onChange={(event) => onEstatusChange(event.target.value as EstatusCliente)}
            className={clsx(plainInputClass, "py-2.5 text-[13px]")}
          >
            {(["ACTIVO", "PAUSADO", "BAJA"] as const).map((value) => (
              <option key={value} value={value}>
                {ESTATUS_FILTER_LABELS[value]}
              </option>
            ))}
          </select>
        </div>

        <div className={clsx(canFilterByAccountant ? "lg:col-span-2" : "lg:col-span-3")}>
          <label htmlFor="client-tipo" className="sr-only">
            Tipo de persona
          </label>
          <select
            id="client-tipo"
            value={tipoPersona ?? ""}
            onChange={(event) =>
              onTipoPersonaChange(event.target.value === "" ? null : (event.target.value as TipoPersona))
            }
            className={clsx(plainInputClass, "py-2.5 text-[13px]")}
          >
            <option value="">Todos los tipos</option>
            {(["MORAL", "FISICA"] as const).map((value) => (
              <option key={value} value={value}>
                {TIPO_PERSONA_LABELS[value]}
              </option>
            ))}
          </select>
        </div>

        {canFilterByAccountant && (
          <div className="lg:col-span-2">
            <label htmlFor="client-contador" className="sr-only">
              Contador asignado
            </label>
            <select
              id="client-contador"
              value={contador ?? ""}
              onChange={(event) =>
                onContadorChange(event.target.value === "" ? undefined : Number(event.target.value))
              }
              disabled={accountantsLoading || accountantsError}
              title={accountantsError ? "No se pudo cargar la lista de contadores" : undefined}
              className={clsx(plainInputClass, "py-2.5 text-[13px]")}
            >
              <option value="">
                {accountantsLoading ? "Cargando contadores…" : "Todos los contadores"}
              </option>
              {accountants.map((accountant) => (
                <option key={accountant.id} value={accountant.id}>
                  {accountant.nombre_completo}
                </option>
              ))}
            </select>
          </div>
        )}

        <div className="flex items-center lg:col-span-2">
          <button
            type="button"
            onClick={onClear}
            disabled={!hasFilters}
            className={clsx(
              "inline-flex w-full items-center justify-center gap-1.5 rounded-lg border border-line px-3 py-2.5 text-[12px] font-semibold transition",
              hasFilters
                ? "text-navy-800 hover:bg-app"
                : "cursor-not-allowed text-muted/60",
            )}
          >
            <SlidersHorizontal size={14} />
            Limpiar filtros
          </button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-line pt-3">
        <span className="mr-1 text-[10px] font-semibold uppercase tracking-wider text-muted">
          Vistas rápidas
        </span>
        {quickViews.map((view) => (
          <button
            key={view.label}
            type="button"
            onClick={view.apply}
            className={clsx(
              "rounded-full px-3 py-1.5 text-[11px] font-semibold transition",
              view.active
                ? "bg-navy-900 text-white"
                : "bg-app text-navy-800 hover:bg-navy-900/10",
            )}
          >
            {view.label}
          </button>
        ))}

        <span className="ml-auto inline-flex items-center gap-1.5 text-[11px] text-muted">
          {isFetching && <Loader2 size={12} className="animate-spin" aria-hidden="true" />}
          <b className="text-ink">{total}</b> contribuyente{total === 1 ? "" : "s"}
        </span>
      </div>
    </section>
  );
}
