import { useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormField, inputClass } from "@/shared/components/FormField";
import { SearchableSelect } from "@/shared/components/SearchableSelect";
import { ApiError } from "@/shared/api/types";
import { useColaboradorOptions } from "@/features/users/api/useUsers";
import { clientSchema } from "../schemas/client.schema";
import type { ClienteFormValues } from "../types";
import { regimenesPara } from "../satRegimenes";

interface Props {
  submitLabel: string;
  pending?: boolean;
  serverError?: unknown;
  onSubmit: (values: ClienteFormValues) => void;
  onCancel?: () => void;
}

function errorMessage(e: unknown): string | null {
  if (!e) return null;
  if (e instanceof ApiError) return e.message;
  return "Ocurrió un error inesperado.";
}

export function ClientForm({ submitLabel, pending, serverError, onSubmit, onCancel }: Props) {
  const [contadorQuery, setContadorQuery] = useState("");
  const { options: contadorOptions, isLoading: loadingContadores } = useColaboradorOptions(contadorQuery);

  const {
    register,
    handleSubmit,
    watch,
    control,
    formState: { errors },
  } = useForm<ClienteFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      nombre_completo: "",
      rfc: "",
      tipo_persona: "MORAL",
      razon_social: "",
      forma_pago: "TRANSFERENCIA",
      contador_asignado_id: null,
      giro: "",
      telefono: "",
      correo: "",
      codigo_postal: "",
      calle: "",
      no_exterior: "",
      no_interior: "",
      colonia: "",
      ciudad: "",
      estado: "",
      regimenes: [],
      tiene_trabajadores: false,
      tipo_nomina: "",
      contacto_principal: { nombre_completo: "", telefono: "", correo: "", cargo: "" },
      tiene_contacto_pagos: false,
      contacto_pagos: { nombre_completo: "", telefono: "", correo: "", cargo: "" },
    },
  });

  const tipoPersona = watch("tipo_persona");
  const tieneTrabajadores = watch("tiene_trabajadores");
  const tieneContactoPagos = watch("tiene_contacto_pagos");
  const regimenesSeleccionados = watch("regimenes");
  const message = errorMessage(serverError);
  const regimenesDisponibles = regimenesPara(tipoPersona);

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-6">
      {message && (
        <div role="alert" className="rounded-lg bg-red-50 px-3 py-2.5 text-sm font-medium text-danger">
          {message}
        </div>
      )}

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Datos generales</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Nombre o razón comercial" htmlFor="nombre_completo" required error={errors.nombre_completo?.message}>
            <input id="nombre_completo" className={inputClass + " pl-4"} {...register("nombre_completo")} />
          </FormField>

          <FormField label="Tipo de persona" htmlFor="tipo_persona" required error={errors.tipo_persona?.message}>
            <select id="tipo_persona" className={inputClass + " pl-4"} {...register("tipo_persona")}>
              <option value="MORAL">Persona Moral</option>
              <option value="FISICA">Persona Física</option>
            </select>
          </FormField>

          <FormField label="RFC" htmlFor="rfc" required error={errors.rfc?.message} hint={tipoPersona === "MORAL" ? "12 caracteres" : "13 caracteres"}>
            <input id="rfc" className={inputClass + " pl-4 uppercase"} maxLength={13} {...register("rfc")} />
          </FormField>

          <FormField
            label="Razón social"
            htmlFor="razon_social"
            required={tipoPersona === "MORAL"}
            error={errors.razon_social?.message}
          >
            <input id="razon_social" className={inputClass + " pl-4"} {...register("razon_social")} />
          </FormField>

          <FormField label="Giro / actividad" htmlFor="giro" required error={errors.giro?.message}>
            <input id="giro" className={inputClass + " pl-4"} {...register("giro")} />
          </FormField>

          <FormField label="Forma de pago" htmlFor="forma_pago" required error={errors.forma_pago?.message}>
            <select id="forma_pago" className={inputClass + " pl-4"} {...register("forma_pago")}>
              <option value="TRANSFERENCIA">Transferencia</option>
              <option value="EFECTIVO">Efectivo</option>
            </select>
          </FormField>

          <FormField label="Teléfono" htmlFor="telefono" required error={errors.telefono?.message}>
            <input id="telefono" className={inputClass + " pl-4"} maxLength={10} {...register("telefono")} />
          </FormField>

          <FormField label="Correo" htmlFor="correo" required error={errors.correo?.message}>
            <input id="correo" type="email" className={inputClass + " pl-4"} {...register("correo")} />
          </FormField>

          <FormField
            label="Contador asignado"
            htmlFor="contador_asignado_id"
            required
            error={errors.contador_asignado_id?.message}
          >
            <Controller
              control={control}
              name="contador_asignado_id"
              render={({ field }) => (
                <SearchableSelect
                  value={field.value}
                  onChange={field.onChange}
                  options={contadorOptions}
                  loading={loadingContadores}
                  query={contadorQuery}
                  onQueryChange={setContadorQuery}
                  placeholder="Buscar colaborador…"
                  invalid={!!errors.contador_asignado_id}
                />
              )}
            />
          </FormField>
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Domicilio fiscal</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div className="sm:col-span-2 lg:col-span-2">
            <FormField label="Calle" htmlFor="calle" required error={errors.calle?.message}>
              <input id="calle" className={inputClass + " pl-4"} {...register("calle")} />
            </FormField>
          </div>
          <FormField label="Código postal" htmlFor="codigo_postal" required error={errors.codigo_postal?.message}>
            <input id="codigo_postal" className={inputClass + " pl-4"} maxLength={5} {...register("codigo_postal")} />
          </FormField>
          <FormField label="No. exterior" htmlFor="no_exterior" required error={errors.no_exterior?.message}>
            <input id="no_exterior" className={inputClass + " pl-4"} {...register("no_exterior")} />
          </FormField>
          <FormField label="No. interior" htmlFor="no_interior" error={errors.no_interior?.message}>
            <input id="no_interior" className={inputClass + " pl-4"} {...register("no_interior")} />
          </FormField>
          <FormField label="Colonia" htmlFor="colonia" required error={errors.colonia?.message}>
            <input id="colonia" className={inputClass + " pl-4"} {...register("colonia")} />
          </FormField>
          <FormField label="Ciudad" htmlFor="ciudad" required error={errors.ciudad?.message}>
            <input id="ciudad" className={inputClass + " pl-4"} {...register("ciudad")} />
          </FormField>
          <FormField label="Estado" htmlFor="estado" required error={errors.estado?.message}>
            <input id="estado" className={inputClass + " pl-4"} {...register("estado")} />
          </FormField>
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Régimen fiscal y nómina</h3>
        <FormField label="Regímenes fiscales" htmlFor="regimenes" required error={errors.regimenes?.message}>
          <Controller
            control={control}
            name="regimenes"
            render={({ field }) => (
              <div className="grid grid-cols-1 gap-2 rounded-lg bg-field p-3 sm:grid-cols-2">
                {regimenesDisponibles.map((r) => {
                  const checked = field.value.includes(r.clave);
                  return (
                    <label key={r.clave} className="flex items-start gap-2 text-[13px] text-ink">
                      <input
                        type="checkbox"
                        className="mt-0.5 size-4 rounded border-line accent-navy-900"
                        checked={checked}
                        onChange={(e) => {
                          field.onChange(
                            e.target.checked
                              ? [...field.value, r.clave]
                              : field.value.filter((v) => v !== r.clave),
                          );
                        }}
                      />
                      <span>
                        <b>{r.clave}</b> · {r.descripcion}
                      </span>
                    </label>
                  );
                })}
              </div>
            )}
          />
        </FormField>

        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-2 text-sm text-ink">
            <input type="checkbox" className="size-4 rounded border-line accent-navy-900" {...register("tiene_trabajadores")} />
            Tiene trabajadores a su cargo
          </label>
          {tieneTrabajadores && (
            <FormField label="Periodicidad de nómina" htmlFor="tipo_nomina" required error={errors.tipo_nomina?.message}>
              <select id="tipo_nomina" className={inputClass + " pl-4"} {...register("tipo_nomina")}>
                <option value="">Selecciona…</option>
                <option value="SEMANAL">Semanal</option>
                <option value="QUINCENAL">Quincenal</option>
                <option value="MENSUAL">Mensual</option>
              </select>
            </FormField>
          )}
        </div>
        {regimenesSeleccionados.length === 0 && (
          <p className="mt-1 text-xs text-muted">Selecciona al menos un régimen aplicable.</p>
        )}
      </section>

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Contacto principal</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Nombre" htmlFor="cp_nombre" required error={errors.contacto_principal?.nombre_completo?.message}>
            <input id="cp_nombre" className={inputClass + " pl-4"} {...register("contacto_principal.nombre_completo")} />
          </FormField>
          <FormField label="Cargo" htmlFor="cp_cargo" required error={errors.contacto_principal?.cargo?.message}>
            <input id="cp_cargo" className={inputClass + " pl-4"} {...register("contacto_principal.cargo")} />
          </FormField>
          <FormField label="Teléfono" htmlFor="cp_telefono" required error={errors.contacto_principal?.telefono?.message}>
            <input id="cp_telefono" className={inputClass + " pl-4"} maxLength={10} {...register("contacto_principal.telefono")} />
          </FormField>
          <FormField label="Correo" htmlFor="cp_correo" required error={errors.contacto_principal?.correo?.message}>
            <input id="cp_correo" type="email" className={inputClass + " pl-4"} {...register("contacto_principal.correo")} />
          </FormField>
        </div>
      </section>

      <section>
        <label className="flex items-center gap-2 text-sm text-ink">
          <input type="checkbox" className="size-4 rounded border-line accent-navy-900" {...register("tiene_contacto_pagos")} />
          Agregar contacto de pagos (opcional)
        </label>
        {tieneContactoPagos && (
          <div className="mt-3 grid grid-cols-1 gap-4 rounded-lg bg-field p-3 sm:grid-cols-2">
            <FormField label="Nombre" htmlFor="pg_nombre" required error={errors.contacto_pagos?.nombre_completo?.message}>
              <input id="pg_nombre" className={inputClass + " pl-4"} {...register("contacto_pagos.nombre_completo")} />
            </FormField>
            <FormField label="Cargo" htmlFor="pg_cargo" required error={errors.contacto_pagos?.cargo?.message}>
              <input id="pg_cargo" className={inputClass + " pl-4"} {...register("contacto_pagos.cargo")} />
            </FormField>
            <FormField label="Teléfono" htmlFor="pg_telefono" required error={errors.contacto_pagos?.telefono?.message}>
              <input id="pg_telefono" className={inputClass + " pl-4"} maxLength={10} {...register("contacto_pagos.telefono")} />
            </FormField>
            <FormField label="Correo" htmlFor="pg_correo" required error={errors.contacto_pagos?.correo?.message}>
              <input id="pg_correo" type="email" className={inputClass + " pl-4"} {...register("contacto_pagos.correo")} />
            </FormField>
          </div>
        )}
      </section>

      <div className="flex justify-end gap-2 border-t border-line pt-4">
        {onCancel && (
          <button type="button" onClick={onCancel} className="rounded-lg border border-line px-4 py-2.5 text-sm font-medium text-ink hover:bg-field">
            Cancelar
          </button>
        )}
        <button
          type="submit"
          disabled={pending}
          className="rounded-lg bg-gold-300 px-5 py-2.5 text-sm font-semibold text-ink hover:brightness-95 disabled:opacity-60"
        >
          {pending ? "Guardando…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
