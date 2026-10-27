import { useEffect, useMemo, useState } from "react";
import { BadgeCheck, Check, Search } from "lucide-react";
import clsx from "clsx";
import type { UseFormReturn } from "react-hook-form";
import { plainInputClass } from "@/shared/components/FormField";
import { REGIMENES_SAT } from "../../constants";
import type { ClientFormValues } from "../../schemas/client.schema";
import { SectionCard } from "./SectionCard";

export function StepRegimenes({ form }: { form: UseFormReturn<ClientFormValues> }) {
  const {
    watch,
    setValue,
    getValues,
    formState: { errors },
  } = form;

  const tipo = watch("tipo_persona");
  const seleccionados = watch("regimenes");
  const [query, setQuery] = useState("");

  const disponibles = useMemo(
    () =>
      REGIMENES_SAT.filter(
        (regimen) =>
          regimen.aplica.includes(tipo) &&
          `${regimen.clave} ${regimen.nombre}`
            .toLowerCase()
            .includes(query.trim().toLowerCase()),
      ),
    [tipo, query],
  );

  // Al cambiar el tipo de persona no deben quedar regímenes de otro tipo.
  useEffect(() => {
    const validas = new Set(REGIMENES_SAT.filter((r) => r.aplica.includes(tipo)).map((r) => r.clave));
    const actuales = getValues("regimenes");
    const filtrados = actuales.filter((clave) => validas.has(clave));
    if (filtrados.length !== actuales.length) {
      setValue("regimenes", filtrados, { shouldValidate: true });
    }
  }, [tipo, getValues, setValue]);

  const toggle = (clave: string) => {
    const next = seleccionados.includes(clave)
      ? seleccionados.filter((item) => item !== clave)
      : [...seleccionados, clave];

    setValue("regimenes", next, { shouldValidate: true, shouldDirty: true });
  };

  return (
    <SectionCard
      number="03"
      title="Regímenes Fiscales y Obligaciones SAT"
      description="Selecciona los regímenes vigentes según la Constancia de Situación Fiscal (CSF) del contribuyente."
      aside={
        <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-app px-3 py-1 text-[10px] font-semibold text-muted">
          <BadgeCheck size={13} className="text-gold-700" />
          Catálogo Anexo 20 SAT
        </span>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div className="relative w-full sm:max-w-xs">
            <Search
              size={15}
              aria-hidden="true"
              className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <label htmlFor="regimen-search" className="sr-only">
              Buscar régimen fiscal
            </label>
            <input
              id="regimen-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Buscar clave o régimen…"
              className={clsx(plainInputClass, "py-2.5 pl-9 text-[13px]")}
            />
          </div>

          <p className="text-[11px] text-muted">
            <b className="text-ink">{seleccionados.length}</b> régimen
            {seleccionados.length === 1 ? "" : "es"} seleccionado
            {seleccionados.length === 1 ? "" : "s"}
          </p>
        </div>

        <div className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-3">
          {disponibles.map((regimen) => {
            const selected = seleccionados.includes(regimen.clave);
            return (
              <button
                key={regimen.clave}
                type="button"
                onClick={() => toggle(regimen.clave)}
                aria-pressed={selected}
                className={clsx(
                  "flex h-full flex-col items-start gap-2 rounded-xl border p-3.5 text-left transition",
                  selected
                    ? "border-navy-900 bg-navy-900 text-white shadow-[0_6px_16px_rgb(11_20_69/18%)]"
                    : "border-line bg-field/40 text-ink hover:border-navy-700/30 hover:bg-field/70",
                )}
              >
                <span className="flex w-full items-start justify-between gap-2">
                  <span
                    className={clsx(
                      "rounded px-1.5 py-0.5 text-[10px] font-bold tracking-wider",
                      selected ? "bg-white/10 text-gold-300" : "bg-surface text-navy-800 ring-1 ring-line",
                    )}
                  >
                    CLAVE {regimen.clave}
                  </span>
                  <span
                    className={clsx(
                      "grid size-5 shrink-0 place-items-center rounded",
                      selected
                        ? "bg-gold-300 text-navy-900"
                        : "border border-line bg-surface text-transparent",
                    )}
                  >
                    <Check size={13} strokeWidth={3} />
                  </span>
                </span>

                <span className="text-[13px] font-semibold leading-snug">{regimen.nombre}</span>
                <span
                  className={clsx(
                    "text-[11px] leading-snug",
                    selected ? "text-on-dark" : "text-muted",
                  )}
                >
                  {regimen.descripcion}
                </span>
              </button>
            );
          })}
        </div>

        {disponibles.length === 0 && (
          <p className="rounded-lg bg-app px-3.5 py-3 text-xs text-muted">
            No hay regímenes que coincidan con la búsqueda para este tipo de persona.
          </p>
        )}

        {errors.regimenes && (
          <p role="alert" className="text-xs font-medium text-danger">
            {errors.regimenes.message}
          </p>
        )}
      </div>
    </SectionCard>
  );
}
