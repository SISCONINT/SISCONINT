import { useState } from "react";
import type { FieldError, UseFormRegisterReturn } from "react-hook-form";
import { Eye, EyeOff, Lock } from "lucide-react";
import { FormField, inputClass } from "./FormField";

interface Props {
  label: string;
  registration: UseFormRegisterReturn;
  error?: FieldError;
  hint?: string;
  autoComplete?: string;
}

export function PasswordField({
  label, registration, error, hint, autoComplete = "new-password",
}: Props) {
  const [show, setShow] = useState(false);

  return (
    <FormField label={label} htmlFor={registration.name} required error={error?.message} hint={hint}>
      <div className="relative">
        <Lock size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-ink" />
        <input
          id={registration.name}
          type={show ? "text" : "password"}
          autoComplete={autoComplete}
          aria-invalid={!!error}
          className={inputClass}
          {...registration}
        />
        <button
          type="button"
          onClick={() => setShow((s) => !s)}
          aria-label={show ? "Ocultar contraseña" : "Mostrar contraseña"}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-ink/70 hover:text-ink"
        >
          {show ? <EyeOff size={18} /> : <Eye size={18} />}
        </button>
      </div>
    </FormField>
  );
}