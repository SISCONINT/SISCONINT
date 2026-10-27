import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { CheckCircle2, TriangleAlert } from "lucide-react";
import { PasswordField } from "@/shared/components/PasswordField";
import { ApiError } from "@/shared/api/types";
import { activateSchema, type ActivateFormValues } from "../schemas/activate.schema";
import { useActivateAccount } from "../api/useActivateAccount";

export function ActivateAccountForm({ token }: { token: string }) {
  const [done, setDone] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const { mutate, isPending } = useActivateAccount();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm<ActivateFormValues>({
    resolver: zodResolver(activateSchema),
    defaultValues: { password: "", confirmacion: "" },
  });

  const onSubmit = (values: ActivateFormValues) => {
    setMessage(null);
    mutate(
      { token, password: values.password, password_confirm: values.confirmacion },
      {
        onSuccess: () => setDone(true),
        onError: (error) => {
          const apiError = error instanceof ApiError ? error : null;
          const passwordErrors = apiError?.fields?.password;
          const confirmErrors = apiError?.fields?.password_confirm;

          if (passwordErrors) {
            setError("password", { type: "server", message: passwordErrors[0] });
          } else if (confirmErrors) {
            setError("confirmacion", { type: "server", message: confirmErrors[0] });
          } else {
            setMessage(apiError?.message ?? "Ocurrió un error inesperado. Intenta de nuevo.");
          }
        },
      },
    );
  };

  if (done) {
    return (
      <div className="flex flex-col items-center gap-4 py-6 text-center">
        <CheckCircle2 size={44} className="text-green-600" />
        <h2 className="font-display text-xl font-bold text-ink">Cuenta activada</h2>
        <p className="text-sm text-muted">Tu contraseña quedó guardada. Ya puedes iniciar sesión.</p>
        <Link
          to="/login"
          className="rounded-lg bg-gold-300 px-6 py-3 text-sm font-semibold text-ink hover:brightness-95"
        >
          Ir a iniciar sesión
        </Link>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      {message && (
        <div role="alert" className="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm font-medium text-danger">
          <TriangleAlert size={16} className="mt-0.5 shrink-0" />
          <span>{message} Si el enlace venció, pide a un administrador que te envíe uno nuevo.</span>
        </div>
      )}

      <PasswordField
        label="Nueva contraseña"
        registration={register("password")}
        error={errors.password}
        hint="Mínimo 10 caracteres, con mayúscula, minúscula, número y símbolo."
      />
      <PasswordField
        label="Confirmar contraseña"
        registration={register("confirmacion")}
        error={errors.confirmacion}
      />

      <button
        type="submit"
        disabled={isPending}
        className="rounded-lg bg-gold-300 py-3.5 text-base font-semibold text-ink
                   shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95
                   disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isPending ? "Guardando…" : "Activar cuenta"}
      </button>
    </form>
  );
}