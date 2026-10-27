import type { SelectHTMLAttributes } from 'react';
import type { FieldError, UseFormRegisterReturn } from 'react-hook-form';
import { FormField, plainInputClass } from './FormField';

interface Props extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "name">{
    label:string;
    required?: boolean;
    hint?: string;
    error?: FieldError;
    registration: UseFormRegisterReturn;
    options: { value: string; label: string }[];
    placeholder?: string;
}

export function SelectField({
    label, required, hint, error, registration, options, placeholder = "Selecciona...", ...rest
}: Props){
    return(
        <FormField label={label} htmlFor={registration.name} required={required}
        hint={hint} error={error?.message}>
            <select id={registration.name} className={plainInputClass}
            aria-invalid={!!error} {...registration} {...rest}>
                <option value="">{placeholder}</option>
                {options.map((o)=>(
                    <option value={o.value} key={o.value}>
                        {o.label}
                    </option>
                ))}
            </select>
        </FormField>
    )
}