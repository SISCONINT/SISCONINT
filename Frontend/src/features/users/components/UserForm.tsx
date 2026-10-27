import { useEffect, useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, TriangleAlert } from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ASSIGNABLE_ROLES } from "@/shared/auth/permissions";
import { ROLE_LABELS, type Role } from "@/shared/constants/roles";
import { GRADOS, GRADO_LABELS } from "@/shared/constants/grados";
import { TextField } from "@/shared/components/TextField";
import { SelectField } from "@/shared/components/SelectField";
import { userSchema, type RegisterUserFormValues } from "../schemas/user.schema";
import { useCreateUser } from "../api/useCreateUser";
import { useUpdateUser } from "../api/useUpdateUser";
import type { Colaborador } from "../types";

type Feedback = { kind: "ok" | "warning" | "error"; text: string } | null;

const FEEDBACK_STYLES = {
  ok: "bg-green-50 text-green-800",
  warning: "bg-amber-50 text-amber-800",
  error: "bg-red-50 text-danger",
} as const;

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="card p-5">
      <legend className="px-1 font-display text-base font-bold text-ink">{title}</legend>
      <div className="mt-2 grid gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  );
}

const EMPTY_VALUES: RegisterUserFormValues = {
  nombre_completo: "",
  correo_institucional: "",
  telefono_despacho: "",
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
  rol: "" as unknown as Role,
  grado_escalafon: "" as unknown as RegisterUserFormValues["grado_escalafon"],
};

function toFormValues(c: Colaborador): RegisterUserFormValues {
  return {
    nombre_completo: c.nombre_completo,
    correo_institucional: c.correo_institucional,
    rol: c.rol,
    grado_escalafon: c.grado_escalafon,
    telefono_despacho: c.telefono_despacho,
    telefono_personal: c.telefono_personal,
    emergencia_nombre: c.emergencia_nombre,
    emergencia_telefono: c.emergencia_telefono,
    licenciatura: c.licenciatura ?? "",
    cedula: c.cedula ?? "",
    calle: c.calle ?? "",
    no_ext_int: c.no_ext_int ?? "",
    colonia: c.colonia ?? "",
    municipio: c.municipio ?? "",
    estado: c.estado ?? "",
  };
}

function applyFieldErrors(
  fields: Record<string, string[]>,
  setError: (name: keyof RegisterUserFormValues, error: { type: string; message: string }) => void,
) {
  Object.entries(fields).forEach(([field, messages]) => {
    if (field in userSchema.shape) {
      setError(field as keyof RegisterUserFormValues, {
        type: "server",
        message: messages[0],
      });
    }
  });
}

interface Props {
  colaborador?: Colaborador;
  lastActiveOwner?: boolean;
  readOnly?: boolean;
}

export function UserForm({ colaborador, lastActiveOwner = false, readOnly = false }: Props) {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const user = useAuthStore((s) => s.user);
  const setAuthUser = useAuthStore((s) => s.setUser);
  const isEdit = !!colaborador;
  const create = useCreateUser();
  const update = useUpdateUser(colaborador?.id ?? 0);
  const isPending = isEdit ? update.isPending : create.isPending;

  const {
    register,
    handleSubmit,
    reset,
    setError,
    watch,
    formState: { errors },
  } = useForm<RegisterUserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues: colaborador ? toFormValues(colaborador) : EMPTY_VALUES,
  });

  useEffect(() => {
    if (colaborador) reset(toFormValues(colaborador));
  }, [colaborador, reset]);

  const isSelf = isEdit && user?.id === colaborador.id;
  const rolLocked = isEdit && (isSelf || lastActiveOwner || readOnly);
  const selectedRol = watch("rol");
  const roleWillChange = isEdit && !rolLocked && selectedRol && selectedRol !== colaborador.rol;

  const rolesDisponibles = user ? ASSIGNABLE_ROLES[user.rol] : [];
  const rolOptions = [
    ...rolesDisponibles.map((r) => ({ value: r, label: ROLE_LABELS[r] })),
  ];
  if (colaborador && !rolesDisponibles.includes(colaborador.rol)) {
    rolOptions.unshift({ value: colaborador.rol, label: ROLE_LABELS[colaborador.rol] });
  }
  const gradoOptions = Object.values(GRADOS).map((g) => ({ value: g, label: GRADO_LABELS[g] }));

  const goTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  const rolHint = (() => {
    if (!isEdit) return undefined;
    if (isSelf) return "No puedes cambiar tu propio rol.";
    if (lastActiveOwner) return "No se puede cambiar el rol del último Dueño activo.";
    if (roleWillChange) {
      return "El nuevo rol aplica en el siguiente inicio de sesión y se cerrará su sesión actual.";
    }
    return undefined;
  })();

  const onSubmit = (values: RegisterUserFormValues) => {
    setFeedback(null);
    const payload = rolLocked && colaborador ? { ...values, rol: colaborador.rol } : values;

    if (!isEdit) {
      create.mutate(payload, {
        onSuccess: (created) => {
          setFeedback(
            created.correo_activacion_enviado
              ? {
                  kind: "ok",
                  text: "Colaborador registrado. Se envió un enlace para definir su contraseña (vigente 48 horas).",
                }
              : {
                  kind: "warning",
                  text: "Colaborador registrado, pero no se pudo enviar el correo de activación. Avisa al administrador del sistema.",
                },
          );
          reset();
          goTop();
        },
        onError: (error) => {
          const apiError = error instanceof ApiError ? error : null;
          if (apiError?.fields) applyFieldErrors(apiError.fields, setError);
          setFeedback({
            kind: "error",
            text: apiError?.fields
              ? "Revisa los campos marcados en rojo."
              : (apiError?.message ?? "Ocurrió un error inesperado. Intenta de nuevo."),
          });
          goTop();
        },
      });
      return;
    }

    const rolChanged = payload.rol !== colaborador.rol;
    const gradoChanged = payload.grado_escalafon !== colaborador.grado_escalafon;

    update.mutate(payload, {
      onSuccess: (updated) => {
        reset(toFormValues(updated));
        if (isSelf && user) {
          setAuthUser({ ...user, nombre: updated.nombre_completo });
        }

        const notes: string[] = ["Colaborador actualizado. Los cambios ya se ven en esta ficha."];
        if (rolChanged) {
          notes.push("El nuevo rol aplica en su siguiente inicio de sesión; se cerró su sesión actual.");
        }
        if (gradoChanged) {
          notes.push("El nuevo grado aplica solo a registros de tiempo posteriores.");
        }
        setFeedback({ kind: "ok", text: notes.join(" ") });
        goTop();
      },
      onError: (error) => {
        const apiError = error instanceof ApiError ? error : null;
        if (apiError?.fields) applyFieldErrors(apiError.fields, setError);
        setFeedback({
          kind: "error",
          text: apiError?.fields
            ? "Revisa los campos marcados en rojo."
            : (apiError?.message ?? "Ocurrió un error inesperado. Intenta de nuevo."),
        });
        goTop();
      },
    });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      {feedback && (
        <div
          role={feedback.kind === "error" ? "alert" : "status"}
          className={`flex items-start gap-2 rounded-lg px-4 py-3 text-sm font-medium ${FEEDBACK_STYLES[feedback.kind]}`}
        >
          {feedback.kind === "ok" ? (
            <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
          ) : (
            <TriangleAlert size={18} className="mt-0.5 shrink-0" />
          )}
          {feedback.text}
        </div>
      )}

      <Section title="Información general">
        <TextField label="Nombre completo" required autoComplete="off" disabled={readOnly}
          registration={register("nombre_completo")} error={errors.nombre_completo} />
        <TextField label="Correo institucional" type="email" required autoComplete="off" disabled={readOnly}
          registration={register("correo_institucional")} error={errors.correo_institucional} />
      </Section>

      <Section title="Rol y nivel">
        <SelectField label="Rol" required options={rolOptions}
          disabled={rolLocked}
          hint={rolHint}
          registration={register("rol")} error={errors.rol} />
        <SelectField label="Grado escalafón" required options={gradoOptions}
          disabled={readOnly}
          hint={isEdit ? "El cambio de grado aplica solo a registros de tiempo posteriores; los anteriores conservan el grado con el que se registraron." : undefined}
          registration={register("grado_escalafon")} error={errors.grado_escalafon} />
      </Section>

      <Section title="Contacto">
        <TextField label="Teléfono del despacho" required inputMode="numeric" maxLength={10} disabled={readOnly}
          hint="10 dígitos" registration={register("telefono_despacho")} error={errors.telefono_despacho} />
        <TextField label="Teléfono personal" required inputMode="numeric" maxLength={10} disabled={readOnly}
          hint="10 dígitos" registration={register("telefono_personal")} error={errors.telefono_personal} />
        <TextField label="Contacto de emergencia (nombre)" required disabled={readOnly}
          registration={register("emergencia_nombre")} error={errors.emergencia_nombre} />
        <TextField label="Contacto de emergencia (teléfono)" required inputMode="numeric" maxLength={10} disabled={readOnly}
          hint="10 dígitos" registration={register("emergencia_telefono")} error={errors.emergencia_telefono} />
      </Section>

      <Section title="Información profesional">
        <TextField label="Licenciatura" disabled={readOnly}
          registration={register("licenciatura")} error={errors.licenciatura} />
        <TextField label="No. de cédula" inputMode="numeric" maxLength={8} disabled={readOnly}
          hint="7 u 8 dígitos (opcional)" registration={register("cedula")} error={errors.cedula} />
      </Section>

      <Section title="Dirección">
        <TextField label="Calle" disabled={readOnly}
          registration={register("calle")} error={errors.calle} />
        <TextField label="No. exterior / interior" disabled={readOnly}
          registration={register("no_ext_int")} error={errors.no_ext_int} />
        <TextField label="Colonia" disabled={readOnly}
          registration={register("colonia")} error={errors.colonia} />
        <TextField label="Municipio" disabled={readOnly}
          registration={register("municipio")} error={errors.municipio} />
        <TextField label="Estado" disabled={readOnly}
          registration={register("estado")} error={errors.estado} />
      </Section>

      {!readOnly && (
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isPending}
            className="rounded-lg bg-gold-300 px-6 py-3 text-sm font-semibold text-ink
                       shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95
                       disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isPending
              ? (isEdit ? "Guardando…" : "Registrando…")
              : (isEdit ? "Guardar cambios" : "Registrar colaborador")}
          </button>
        </div>
      )}
    </form>
  );
}
