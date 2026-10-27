import { Building2, UserRound } from "lucide-react";
import clsx from "clsx";
import type { UseFormReturn } from "react-hook-form";
import { SelectField } from "@/shared/components/SelectField";
import { TextField } from "@/shared/components/TextField";
import { FORMA_PAGO_OPTIONS } from "../../constants";
import type { AccountantOption } from "../../types";
import type { ClientFormValues } from "../../schemas/client.schema";
import { SectionCard } from "./SectionCard";

interface Props {
  form: UseFormReturn<ClientFormValues>;
  accountants: AccountantOption[];
  accountantsLoading: boolean;
  accountantsError: boolean;
}

const TIPOS = [
  {
    value: "FISICA" as const,
    label: "Persona Física",
    hint: "Actividades empresariales, profesionales u honorarios.",
    icon: UserRound,
  },
  {
    value: "MORAL" as const,
    label: "Persona Moral",
    hint: "Sociedad mercantil, civil, SAPI o asociación.",
    icon: Building2,
  },
];

export function StepDatosGenerales({
  form,
  accountants,
  accountantsLoading,
  accountantsError,
}: Props) {
  const {
    register,
    watch,
    formState: { errors },
  } = form;

  const tipo = watch("tipo_persona");
  const accountantOptions = accountants.map((accountant) => ({
    value: String(accountant.id),
    label: accountant.nombre_completo,
  }));

  return (
    <SectionCard
      number="01"
      title="Datos Generales del Contribuyente"
      description="Identificación legal, régimen contractual y asignación del contador responsable del expediente."
      aside={
        <span className="w-fit rounded-full bg-app px-3 py-1 text-[10px] font-semibold text-muted">
          Obligatorio (*)
        </span>
      }
    >
      <div className="flex flex-col gap-5">
        <fieldset>
          <legend className="mb-2 text-sm font-semibold text-ink">
            Tipo de Persona Fiscal <span className="text-danger">*</span>
          </legend>
          <div className="grid gap-2.5 sm:grid-cols-2">
            {TIPOS.map(({ value, label, hint, icon: Icon }) => {
              const selected = tipo === value;
              return (
                <label
                  key={value}
                  className={clsx(
                    "flex cursor-pointer items-start gap-3 rounded-xl border p-4 transition",
                    selected
                      ? "border-navy-900 bg-navy-900 text-white shadow-[0_6px_16px_rgb(11_20_69/18%)]"
                      : "border-line bg-field/50 text-ink hover:border-navy-700/30",
                  )}
                >
                  <input
                    type="radio"
                    value={value}
                    {...register("tipo_persona")}
                    className="mt-1 size-4 shrink-0 accent-gold-500"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-semibold">{label}</span>
                    <span
                      className={clsx(
                        "mt-0.5 block text-[11px] leading-snug",
                        selected ? "text-on-dark" : "text-muted",
                      )}
                    >
                      {hint}
                    </span>
                  </span>
                  <Icon
                    size={18}
                    aria-hidden="true"
                    className={clsx("mt-0.5 shrink-0", selected ? "text-gold-500" : "text-muted")}
                  />
                </label>
              );
            })}
          </div>
          {errors.tipo_persona && (
            <p role="alert" className="mt-1 text-xs font-medium text-danger">
              {errors.tipo_persona.message}
            </p>
          )}
        </fieldset>

        <div className="grid gap-4 sm:grid-cols-2">
          <TextField
            label="RFC del contribuyente"
            required
            maxLength={13}
            autoComplete="off"
            hint="12 caracteres para persona moral, 13 para persona física."
            registration={register("rfc")}
            error={errors.rfc}
          />
          <TextField
            label="Nombre comercial"
            required
            maxLength={200}
            autoComplete="off"
            registration={register("nombre_completo")}
            error={errors.nombre_completo}
          />

          {tipo === "MORAL" && (
            <TextField
              label="Razón o denominación social"
              required
              maxLength={250}
              autoComplete="off"
              registration={register("razon_social")}
              error={errors.razon_social}
            />
          )}

          <TextField
            label="Giro / actividad preponderante"
            required
            maxLength={150}
            autoComplete="off"
            registration={register("giro")}
            error={errors.giro}
          />

          <SelectField
            label="Forma de pago convenida"
            required
            options={FORMA_PAGO_OPTIONS}
            placeholder="Selecciona la forma de pago"
            registration={register("forma_pago")}
            error={errors.forma_pago}
          />

          <div>
            <SelectField
              label="Contador responsable"
              required
              options={accountantOptions}
              placeholder={
                accountantsLoading ? "Cargando contadores…" : "Selecciona un contador activo"
              }
              disabled={accountantsLoading || accountantsError}
              registration={register("contador_asignado_id")}
              error={errors.contador_asignado_id}
            />
            {accountantsError && (
              <p className="mt-1 text-[11px] font-medium text-danger">
                No se pudo cargar la lista de contadores. Recarga la página e inténtalo de nuevo.
              </p>
            )}
            {!accountantsError && !accountantsLoading && accountants.length === 0 && (
              <p className="mt-1 text-[11px] font-medium text-amber-700">
                No hay contadores activos. Registra uno en Colaboradores antes de dar de alta al
                cliente.
              </p>
            )}
          </div>

          <TextField
            label="Teléfono del contribuyente"
            required
            inputMode="numeric"
            maxLength={10}
            hint="10 dígitos"
            registration={register("telefono")}
            error={errors.telefono}
          />
          <TextField
            label="Correo institucional"
            type="email"
            required
            autoComplete="off"
            registration={register("correo")}
            error={errors.correo}
          />
        </div>
      </div>
    </SectionCard>
  );
}
