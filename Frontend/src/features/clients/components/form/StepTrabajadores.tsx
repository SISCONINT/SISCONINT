import { BriefcaseBusiness, CheckCircle2, UsersRound } from "lucide-react";
import clsx from "clsx";
import type { UseFormReturn } from "react-hook-form";
import { SelectField } from "@/shared/components/SelectField";
import { TIPO_NOMINA_OPTIONS } from "../../constants";
import type { ClientFormValues } from "../../schemas/client.schema";
import { SectionCard } from "./SectionCard";

export function StepTrabajadores({ form }: { form: UseFormReturn<ClientFormValues> }) {
  const {
    register,
    watch,
    setValue,
    formState: { errors },
  } = form;

  const tieneTrabajadores = watch("tiene_trabajadores");

  return (
    <SectionCard
      number="04"
      title="Trabajadores y Esquema Laboral"
      description="Obligaciones de seguridad social, retención de nómina y emisión de CFDI de Nómina 1.2."
      aside={
        <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-app px-3 py-1 text-[10px] font-semibold text-muted">
          <BriefcaseBusiness size={13} className="text-navy-800" />
          Obligaciones laborales
        </span>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-line px-4 py-3.5">
          <p className="text-sm font-semibold text-ink">
            ¿El contribuyente cuenta con trabajadores o empleados contratados?
          </p>
          <p className="mt-0.5 text-[11px] text-muted">
            Determina si se auditará el cumplimiento ante IMSS, INFONAVIT y el ISN.
          </p>

          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() =>
                setValue("tiene_trabajadores", true, { shouldValidate: true, shouldDirty: true })
              }
              aria-pressed={tieneTrabajadores}
              className={clsx(
                "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition",
                tieneTrabajadores
                  ? "bg-navy-900 text-white shadow-[0_4px_12px_rgb(11_20_69/18%)]"
                  : "bg-app text-navy-800 hover:bg-navy-900/10",
              )}
            >
              <UsersRound size={15} />
              Sí, con trabajadores
            </button>
            <button
              type="button"
              onClick={() =>
                setValue("tiene_trabajadores", false, { shouldValidate: true, shouldDirty: true })
              }
              aria-pressed={!tieneTrabajadores}
              className={clsx(
                "inline-flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition",
                !tieneTrabajadores
                  ? "bg-navy-900 text-white shadow-[0_4px_12px_rgb(11_20_69/18%)]"
                  : "bg-app text-navy-800 hover:bg-navy-900/10",
              )}
            >
              <CheckCircle2 size={15} />
              No, sin nómina
            </button>
          </div>
        </div>

        {tieneTrabajadores ? (
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Tipo y frecuencia de dispersión"
              required
              options={TIPO_NOMINA_OPTIONS}
              placeholder="Selecciona la periodicidad"
              registration={register("tipo_nomina")}
              error={errors.tipo_nomina}
            />
            <div className="rounded-xl bg-field/60 px-4 py-3 text-[11px] leading-relaxed text-muted">
              <p className="font-semibold text-ink">Retenciones e IMSS / INFONAVIT</p>
              <p className="mt-0.5">
                Se generarán cédulas mensuales y bimestrales para revisión previa al vencimiento
                del día 17 de cada mes.
              </p>
            </div>
          </div>
        ) : (
          <div className="rounded-xl bg-field/60 px-4 py-3 text-[11px] leading-relaxed text-muted">
            <p className="font-semibold text-ink">Sin nómina registrada</p>
            <p className="mt-0.5">
              No se generarán obligaciones de retención salarial, IMSS, INFONAVIT ni ISN para este
              contribuyente.
            </p>
          </div>
        )}
      </div>
    </SectionCard>
  );
}
