import type { FieldError, UseFormRegisterReturn } from "react-hook-form";
import { FormField, plainInputClass } from "./FormField";
import { ESTADOS_MEXICO } from "../constants/estadosMexico";

const DATALIST_ID = "estados-mexico-datalist";

interface Props {
  label?: string;
  required?: boolean;
  hint?: string;
  disabled?: boolean;
  error?: FieldError;
  registration: UseFormRegisterReturn;
}

/**
 * Campo de entidad federativa: deja escribir y filtra la lista (datalist nativo), pero el
 * valor final se valida contra el catálogo oficial de 32 estados (ver estadosMexico.ts) para
 * evitar nombres mal escritos o inconsistentes.
 */
export function EstadoField({ label = "Entidad federativa", required, hint, disabled, error, registration }: Props) {
  return (
    <FormField label={label} htmlFor={registration.name} required={required} hint={hint} error={error?.message}>
      <input
        id={registration.name}
        list={DATALIST_ID}
        autoComplete="off"
        disabled={disabled}
        className={plainInputClass}
        aria-invalid={!!error}
        placeholder="Escribe o selecciona un estado…"
        {...registration}
      />
      <datalist id={DATALIST_ID}>
        {ESTADOS_MEXICO.map((estado) => (
          <option key={estado} value={estado} />
        ))}
      </datalist>
    </FormField>
  );
}
