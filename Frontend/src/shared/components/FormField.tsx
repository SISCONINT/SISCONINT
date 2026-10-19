import type { ReactNode } from "react";

export const inputClass =
  "w-full rounded-lg bg-field py-3 pl-10 pr-10 text-sm text-ink placeholder:text-muted/70 " +
  "outline-none ring-1 ring-transparent transition focus:ring-gold-500 " +
  "aria-[invalid=true]:ring-danger disabled:opacity-60";

interface Props {
  label: string;
  htmlFor: string;
  required?: boolean;
  error?: string;
  hint?: string;
  aside?: ReactNode; // contenido a la derecha del label (ej. "¿Olvidaste...?")
  children: ReactNode;
}

export function FormField({ label, htmlFor, required, error, hint, aside, children }: Props) {
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between">
        <label htmlFor={htmlFor} className="text-sm font-semibold text-ink">
          {label} {required && <span className="text-danger">*</span>}
        </label>
        {aside}
      </div>
      {children}
      {error ? (
        <p role="alert" className="mt-1 text-xs font-medium text-danger">{error}</p>
      ) : (
        hint && <p className="mt-1 text-[11px] text-muted">{hint}</p>
      )}
    </div>
  );
}