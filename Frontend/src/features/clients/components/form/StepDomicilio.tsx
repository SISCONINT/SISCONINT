import type { UseFormReturn } from "react-hook-form";
import { TextField } from "@/shared/components/TextField";
import type { ClientFormValues } from "../../schemas/client.schema";
import { SectionCard } from "./SectionCard";

export function StepDomicilio({ form }: { form: UseFormReturn<ClientFormValues> }) {
  const {
    register,
    formState: { errors },
  } = form;

  return (
    <SectionCard
      number="02"
      title="Domicilio Fiscal Registrado"
      description="Ubicación ante la Administración Desconcentrada del SAT y domicilio para notificaciones oficiales."
      aside={
        <span className="w-fit rounded-full bg-app px-3 py-1 text-[10px] font-semibold text-muted">
          Obligatorio (*)
        </span>
      }
    >
      <div className="grid gap-4 sm:grid-cols-6">
        <div className="sm:col-span-4">
          <TextField
            label="Calle"
            required
            maxLength={150}
            autoComplete="off"
            registration={register("calle")}
            error={errors.calle}
          />
        </div>
        <div className="sm:col-span-2">
          <TextField
            label="Código Postal"
            required
            inputMode="numeric"
            maxLength={5}
            hint="5 dígitos"
            registration={register("codigo_postal")}
            error={errors.codigo_postal}
          />
        </div>
        <div className="sm:col-span-3">
          <TextField
            label="Número exterior"
            required
            maxLength={20}
            autoComplete="off"
            registration={register("no_exterior")}
            error={errors.no_exterior}
          />
        </div>
        <div className="sm:col-span-3">
          <TextField
            label="Número interior"
            maxLength={20}
            autoComplete="off"
            hint="Opcional"
            registration={register("no_interior")}
            error={errors.no_interior}
          />
        </div>
        <div className="sm:col-span-3">
          <TextField
            label="Colonia / asentamiento"
            required
            maxLength={100}
            autoComplete="off"
            registration={register("colonia")}
            error={errors.colonia}
          />
        </div>
        <div className="sm:col-span-3">
          <TextField
            label="Municipio o alcaldía"
            required
            maxLength={100}
            autoComplete="off"
            registration={register("ciudad")}
            error={errors.ciudad}
          />
        </div>
        <div className="sm:col-span-3">
          <TextField
            label="Entidad federativa"
            required
            maxLength={100}
            autoComplete="off"
            registration={register("estado")}
            error={errors.estado}
          />
        </div>
      </div>

      <p className="mt-4 rounded-lg bg-app px-3.5 py-2.5 text-[11px] leading-relaxed text-muted">
        El domicilio debe coincidir con la Constancia de Situación Fiscal vigente. Los datos de
        ubicación se conservan como referencia para diligencias y notificaciones.
      </p>
    </SectionCard>
  );
}
