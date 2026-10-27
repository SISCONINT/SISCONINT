import { useState } from "react";
import { Plus, UserRound, Wallet, X } from "lucide-react";
import type { UseFormReturn } from "react-hook-form";
import { TextField } from "@/shared/components/TextField";
import { BTN_SECONDARY, BTN_GHOST } from "../../constants";
import type { ClientFormValues } from "../../schemas/client.schema";
import { SectionCard } from "./SectionCard";

export function StepContactos({ form }: { form: UseFormReturn<ClientFormValues> }) {
  const {
    register,
    getValues,
    setValue,
    formState: { errors },
  } = form;

  const [showPagos, setShowPagos] = useState(() =>
    Object.values(getValues("contacto_pagos")).some((value) => value.trim() !== ""),
  );

  const principalErrors = errors.contacto_principal;
  const pagosErrors = errors.contacto_pagos;

  const quitarPagos = () => {
    setValue("contacto_pagos", {
      nombre_completo: "",
      telefono: "",
      correo: "",
      cargo: "",
    });
    setShowPagos(false);
  };

  return (
    <SectionCard
      number="05"
      title="Directorio de Contactos y Representación Legal"
      description="Personas facultadas para firma de dictámenes, entrega de sellos e informes ejecutivos."
      aside={
        <span className="w-fit rounded-full bg-app px-3 py-1 text-[10px] font-semibold text-muted">
          Obligatorio (*)
        </span>
      }
    >
      <div className="flex flex-col gap-4">
        <div className="rounded-xl border border-line bg-field/40 p-4">
          <div className="mb-3 flex items-center justify-between gap-2">
            <h3 className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
              <UserRound size={16} className="text-gold-700" />
              Contacto principal / representante legal
            </h3>
            <span className="rounded-full bg-navy-900 px-2.5 py-0.5 text-[10px] font-semibold text-white">
              Obligatorio
            </span>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Nombre completo"
              required
              maxLength={150}
              autoComplete="off"
              registration={register("contacto_principal.nombre_completo")}
              error={principalErrors?.nombre_completo}
            />
            <TextField
              label="Puesto / cargo"
              required
              maxLength={100}
              autoComplete="off"
              registration={register("contacto_principal.cargo")}
              error={principalErrors?.cargo}
            />
            <TextField
              label="Teléfono directo"
              required
              inputMode="numeric"
              maxLength={10}
              hint="10 dígitos"
              registration={register("contacto_principal.telefono")}
              error={principalErrors?.telefono}
            />
            <TextField
              label="Correo institucional"
              type="email"
              required
              autoComplete="off"
              registration={register("contacto_principal.correo")}
              error={principalErrors?.correo}
            />
          </div>
        </div>

        {showPagos ? (
          <div className="rounded-xl border border-line p-4">
            <div className="mb-3 flex items-start justify-between gap-2">
              <div>
                <h3 className="inline-flex items-center gap-2 text-sm font-semibold text-ink">
                  <Wallet size={16} className="text-gold-700" />
                  Contacto de pagos y tesorería
                </h3>
                <p className="mt-0.5 text-[11px] text-muted">
                  Si capturas este contacto, sus cuatro campos son obligatorios.
                </p>
              </div>
              <button
                type="button"
                onClick={quitarPagos}
                className={BTN_GHOST}
                aria-label="Quitar contacto de pagos"
              >
                <X size={15} />
                Quitar
              </button>
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <TextField
                label="Nombre del encargado"
                maxLength={150}
                autoComplete="off"
                registration={register("contacto_pagos.nombre_completo")}
                error={pagosErrors?.nombre_completo}
              />
              <TextField
                label="Puesto / cargo"
                maxLength={100}
                autoComplete="off"
                registration={register("contacto_pagos.cargo")}
                error={pagosErrors?.cargo}
              />
              <TextField
                label="Teléfono de cobranza"
                inputMode="numeric"
                maxLength={10}
                hint="10 dígitos"
                registration={register("contacto_pagos.telefono")}
                error={pagosErrors?.telefono}
              />
              <TextField
                label="Correo de pagos / facturación"
                type="email"
                autoComplete="off"
                registration={register("contacto_pagos.correo")}
                error={pagosErrors?.correo}
              />
            </div>
          </div>
        ) : (
          <button
            type="button"
            onClick={() => setShowPagos(true)}
            className={`${BTN_SECONDARY} w-full`}
          >
            <Plus size={15} />
            Agregar contacto de pagos (opcional)
          </button>
        )}
      </div>
    </SectionCard>
  );
}
