import { useState, type ReactNode } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, TriangleAlert } from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ASSIGNABLE_ROLES } from "@/shared/auth/permissions";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { GRADOS, GRADO_LABELS } from "@/shared/constants/grados";
import { TextField } from "@/shared/components/TextField";
import { SelectField } from "@/shared/components/SelectField";
import { userSchema, type RegisterUserFormValues } from "../schemas/user.schema";
import { useCreateUser } from "../api/useCreateUser";

type Feedback = { kind: "ok" | "warning" | "error"; text: string } | null;

const FEEDBACK_STYLES = {
  ok: "bg-green-50 text-green-800",
  warning: "bg-amber-50 text-amber-800",
  error: "bg-red-50 text-danger",
} as const;

/** Agrupa campos relacionados bajo un título */
function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <fieldset className="card p-5">
      <legend className="px-1 font-display text-base font-bold text-ink">{title}</legend>
      <div className="mt-2 grid gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  );
}

const EMPTY_VALUES = {
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
  // rol y grado_escalafon no llevan valor: el select empieza en "Selecciona…"
};

export function UserForm() {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const user = useAuthStore((s) => s.user);
  const { mutate, isPending } = useCreateUser();

  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm<RegisterUserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues: EMPTY_VALUES,
  });

  // Solo los roles que el usuario actual puede asignar (el backend lo vuelve a validar)
  const rolesDisponibles = user ? ASSIGNABLE_ROLES[user.rol] : [];
  const rolOptions = rolesDisponibles.map((r) => ({ value: r, label: ROLE_LABELS[r] }));
  const gradoOptions = Object.values(GRADOS).map((g) => ({ value: g, label: GRADO_LABELS[g] }));

  const goTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  const onSubmit = (values: RegisterUserFormValues) => {
    setFeedback(null);

    mutate(values, {
      onSuccess: (colaborador) => {
        setFeedback(
          colaborador.correo_activacion_enviado
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
        const fields = apiError?.fields;

        // Errores por campo (ej. correo duplicado) → debajo del input correspondiente
        if (fields) {
          Object.entries(fields).forEach(([field, messages]) => {
            if (field in userSchema.shape) {
              setError(field as keyof RegisterUserFormValues, {
                type: "server",
                message: messages[0],
              });
            }
          });
        }

        setFeedback({
          kind: "error",
          text: fields
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
        <TextField label="Nombre completo" required autoComplete="off"
          registration={register("nombre_completo")} error={errors.nombre_completo} />
        <TextField label="Correo institucional" type="email" required autoComplete="off"
          registration={register("correo_institucional")} error={errors.correo_institucional} />
      </Section>

      <Section title="Rol y nivel">
        <SelectField label="Rol" required options={rolOptions}
          registration={register("rol")} error={errors.rol} />
        <SelectField label="Grado escalafón" required options={gradoOptions}
          registration={register("grado_escalafon")} error={errors.grado_escalafon} />
      </Section>

      <Section title="Contacto">
        <TextField label="Teléfono del despacho" required inputMode="numeric" maxLength={10}
          hint="10 dígitos" registration={register("telefono_despacho")} error={errors.telefono_despacho} />
        <TextField label="Teléfono personal" required inputMode="numeric" maxLength={10}
          hint="10 dígitos" registration={register("telefono_personal")} error={errors.telefono_personal} />
        <TextField label="Contacto de emergencia (nombre)" required
          registration={register("emergencia_nombre")} error={errors.emergencia_nombre} />
        <TextField label="Contacto de emergencia (teléfono)" required inputMode="numeric" maxLength={10}
          hint="10 dígitos" registration={register("emergencia_telefono")} error={errors.emergencia_telefono} />
      </Section>

      <Section title="Información profesional">
        <TextField label="Licenciatura"
          registration={register("licenciatura")} error={errors.licenciatura} />
        <TextField label="No. de cédula" inputMode="numeric" maxLength={8}
          hint="7 u 8 dígitos (opcional)" registration={register("cedula")} error={errors.cedula} />
      </Section>

      <Section title="Dirección">
        <TextField label="Calle" registration={register("calle")} error={errors.calle} />
        <TextField label="No. exterior / interior"
          registration={register("no_ext_int")} error={errors.no_ext_int} />
        <TextField label="Colonia" registration={register("colonia")} error={errors.colonia} />
        <TextField label="Municipio" registration={register("municipio")} error={errors.municipio} />
        <TextField label="Estado" registration={register("estado")} error={errors.estado} />
      </Section>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isPending}
          className="rounded-lg bg-gold-300 px-6 py-3 text-sm font-semibold text-ink
                     shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95
                     disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isPending ? "Registrando…" : "Registrar colaborador"}
        </button>
      </div>
    </form>
  );
}