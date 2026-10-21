import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, Lock, LogIn, Mail, TriangleAlert } from "lucide-react";
import { FormField, inputClass } from "@/shared/components/FormField";
import { formatMmSs, useCountdown } from "@/shared/hooks/useCountdown";
import { ApiError } from "@/shared/api/types";
import { loginSchema, type LoginFormValues } from "../schemas/login.schema";
import { useLogin } from "../api/useLogin";
import { loginErrorMessage } from "../errors";

const DEFAULT_LOCK_SECONDS = 15 * 60; // si el backend no envía el tiempo restante

export function LoginForm() {
  const [showPassword, setShowPassword] = useState(false);
  const { mutate, isPending, error, submittedAt } = useLogin();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { correo: "", password: "", recordar: false },
  });

  const isLockError = error instanceof ApiError && error.status === 423;
  const remaining = useCountdown(
    isLockError ? (error.retryAfter ?? DEFAULT_LOCK_SECONDS) : null,
    submittedAt,
  );
  const locked = isLockError && remaining > 0;

  const message = isLockError
    ? locked
      ? `Demasiados intentos fallidos. Intenta de nuevo en ${formatMmSs(remaining)}.`
      : null
    : error
      ? loginErrorMessage(error)
      : null;

  const onSubmit = (v: LoginFormValues) => {
    // "recordar" aún no lo soporta el backend; no se envía
    mutate({ correo: v.correo, password: v.password });
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-5">
      {message && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg bg-red-50 px-3 py-2.5 text-sm font-medium text-danger"
        >
          <TriangleAlert size={16} className="mt-0.5 shrink-0" />
          {message}
        </div>
      )}

      <FormField
        label="Correo institucional"
        htmlFor="correo"
        required
        error={errors.correo?.message}
        hint="Obligatorio: Use exclusivamente su dominio corporativo asignado."
      >
        <div className="relative">
          <Mail size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink" />
          <input
            id="correo"
            type="email"
            autoComplete="username"
            placeholder="usuario@tellezponce.com"
            aria-invalid={!!errors.correo}
            className={inputClass}
            {...register("correo")}
          />
        </div>
      </FormField>

      <FormField
        label="Contraseña"
        htmlFor="password"
        required
        error={errors.password?.message}
        aside={
          <Link to="/recuperar" className="text-[11px] font-medium text-gold-700 hover:underline">
            ¿Olvidaste tu contraseña?
          </Link>
        }
      >
        <div className="relative">
          <Lock size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink" />
          <input
            id="password"
            type={showPassword ? "text" : "password"}
            autoComplete="current-password"
            placeholder="••••••••••••"
            aria-invalid={!!errors.password}
            className={inputClass}
            {...register("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((s) => !s)}
            aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/70 hover:text-ink"
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>
      </FormField>

      <label className="flex items-center gap-2.5 text-sm text-ink">
        <input type="checkbox" className="size-4 rounded border-line accent-navy-900" {...register("recordar")} />
        Recordar sesión en este equipo fiscal autorizado
      </label>

      <button
        type="submit"
        disabled={isPending || locked}
        className="flex items-center justify-center gap-2 rounded-lg bg-gold-300 py-3.5 text-base font-semibold text-ink
                   shadow-[0_6px_14px_rgb(245_213_71/35%)] transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isPending ? "Verificando…" : "Iniciar sesión"}
        {!isPending && <LogIn size={18} />}
      </button>
    </form>
  );
}