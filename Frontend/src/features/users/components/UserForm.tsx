import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { FormField, inputClass } from "@/shared/components/FormField";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { userSchema, type UserFormValues } from "../schemas/user.schema";
import { GRADO_LABELS, GRADOS } from "../types";
import { assignableRoles } from "../permissions";

interface Props {
  defaultValues?: Partial<UserFormValues>;
  submitLabel: string;
  pending?: boolean;
  serverError?: unknown;
  onSubmit: (values: UserFormValues) => void;
  onCancel?: () => void;
}

function errorMessage(e: unknown): string | null {
  if (!e) return null;
  if (e instanceof ApiError) {
    if (e.status === 409) return "Ya existe un colaborador con ese correo.";
    return e.message;
  }
  return "Ocurrió un error inesperado.";
}

export function UserForm({ defaultValues, submitLabel, pending, serverError, onSubmit, onCancel }: Props) {
  const actor = useAuthStore((s) => s.user);
  const roles = actor ? assignableRoles(actor.rol) : [];

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<UserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues: {
      nombre_completo: "",
      telefono_despacho: "",
      correo_institucional: "",
      rol: roles[0] ?? "CONTADOR",
      grado_escalafon: "JUNIOR",
      telefono_personal: "",
      emergencia_nombre: "",
      emergencia_telefono: "",
      licenciatura: "",
      cedula: "",
      calle: "",
      no_ext_int: "",
      colonia: "",
      municipio: "",
      estado: "",
      ...defaultValues,
    },
  });

  const message = errorMessage(serverError);

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      {message && (
        <div role="alert" className="rounded-lg bg-red-50 px-3 py-2.5 text-sm font-medium text-danger">
          {message}
        </div>
      )}

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Datos generales</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <FormField label="Nombre completo" htmlFor="nombre_completo" required error={errors.nombre_completo?.message}>
              <input id="nombre_completo" className={inputClass + " pl-4"} {...register("nombre_completo")} />
            </FormField>
          </div>

          <FormField
            label="Correo institucional"
            htmlFor="correo_institucional"
            required
            error={errors.correo_institucional?.message}
          >
            <input id="correo_institucional" type="email" className={inputClass + " pl-4"} {...register("correo_institucional")} />
          </FormField>

          <FormField label="Teléfono del despacho" htmlFor="telefono_despacho" required error={errors.telefono_despacho?.message}>
            <input id="telefono_despacho" className={inputClass + " pl-4"} maxLength={10} {...register("telefono_despacho")} />
          </FormField>

          <FormField label="Rol" htmlFor="rol" required error={errors.rol?.message}>
            <select id="rol" className={inputClass + " pl-4"} {...register("rol")}>
              {roles.map((r) => (
                <option key={r} value={r}>
                  {ROLE_LABELS[r]}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Grado / escalafón" htmlFor="grado_escalafon" required error={errors.grado_escalafon?.message}>
            <select id="grado_escalafon" className={inputClass + " pl-4"} {...register("grado_escalafon")}>
              {GRADOS.map((g) => (
                <option key={g} value={g}>
                  {GRADO_LABELS[g]}
                </option>
              ))}
            </select>
          </FormField>

          <FormField label="Teléfono personal" htmlFor="telefono_personal" required error={errors.telefono_personal?.message}>
            <input id="telefono_personal" className={inputClass + " pl-4"} maxLength={10} {...register("telefono_personal")} />
          </FormField>

          <FormField label="Licenciatura" htmlFor="licenciatura" error={errors.licenciatura?.message}>
            <input id="licenciatura" className={inputClass + " pl-4"} {...register("licenciatura")} />
          </FormField>

          <FormField label="Cédula profesional" htmlFor="cedula" error={errors.cedula?.message} hint="7 u 8 dígitos">
            <input id="cedula" className={inputClass + " pl-4"} maxLength={8} {...register("cedula")} />
          </FormField>
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Domicilio (opcional)</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <FormField label="Calle" htmlFor="calle" error={errors.calle?.message}>
              <input id="calle" className={inputClass + " pl-4"} {...register("calle")} />
            </FormField>
          </div>
          <FormField label="No. exterior / interior" htmlFor="no_ext_int" error={errors.no_ext_int?.message}>
            <input id="no_ext_int" className={inputClass + " pl-4"} {...register("no_ext_int")} />
          </FormField>
          <FormField label="Colonia" htmlFor="colonia" error={errors.colonia?.message}>
            <input id="colonia" className={inputClass + " pl-4"} {...register("colonia")} />
          </FormField>
          <FormField label="Municipio" htmlFor="municipio" error={errors.municipio?.message}>
            <input id="municipio" className={inputClass + " pl-4"} {...register("municipio")} />
          </FormField>
          <FormField label="Estado" htmlFor="estado" error={errors.estado?.message}>
            <input id="estado" className={inputClass + " pl-4"} {...register("estado")} />
          </FormField>
        </div>
      </section>

      <section>
        <h3 className="mb-3 text-[11px] font-semibold uppercase tracking-wide text-muted">Contacto de emergencia</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FormField label="Nombre" htmlFor="emergencia_nombre" required error={errors.emergencia_nombre?.message}>
            <input id="emergencia_nombre" className={inputClass + " pl-4"} {...register("emergencia_nombre")} />
          </FormField>
          <FormField label="Teléfono" htmlFor="emergencia_telefono" required error={errors.emergencia_telefono?.message}>
            <input id="emergencia_telefono" className={inputClass + " pl-4"} maxLength={10} {...register("emergencia_telefono")} />
          </FormField>
        </div>
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
