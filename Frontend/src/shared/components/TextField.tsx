import type { InputHTMLAttributes } from "react";
import type { FieldError, UseFormRegisterReturn } from "react-hook-form";
import { FormField, plainInputClass } from './FormField';

interface Props extends Omit<InputHTMLAttributes<HTMLInputElement>, "name"> {
    label: string;
    required?: boolean;
    hint?: string;
    error?: FieldError;
    registration: UseFormRegisterReturn;
}

export function TextField({label, required, hint, error, registration, ...rest}: Props){
    return(
        <FormField label={label} htmlFor={registration.name} required={required}
        hint={hint} error={error?.message}>
            <input id={registration.name} className={plainInputClass}
            aria-invalid={!!error} {...rest} {...registration}/>
        </FormField>
    );
}