import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { clientsApi } from "@/features/clients/api/clientsApi";
import { plainInputClass, FormField } from "./FormField";

interface Props {
  value: number | "";
  onChange: (value: number | "") => void;
  label?: string;
  required?: boolean;
  error?: string;
  allowEmpty?: boolean;
}

/** Selector de cliente con búsqueda; usa GET /clients?q= (máx. 20 resultados por página). */
export function ClientPicker({ value, onChange, label = "Cliente", required, error, allowEmpty }: Props) {
  const [q, setQ] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["clients", "picker", q],
    queryFn: () => clientsApi.list({ q, estatus: "ACTIVO", tipo_persona: null, page: 1 }),
  });

  return (
    <FormField label={label} htmlFor="client-picker" required={required} error={error}>
      <input
        type="text"
        placeholder="Buscar por nombre o RFC…"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        className={plainInputClass + " mb-1.5"}
      />
      <select
        id="client-picker"
        className={plainInputClass}
        value={value}
        aria-invalid={!!error}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : "")}
      >
        <option value="">{allowEmpty ? "Sin cliente (interna)" : isLoading ? "Cargando…" : "Selecciona un cliente…"}</option>
        {(data?.items ?? []).map((c) => (
          <option key={c.id} value={c.id}>
            {c.razon_social || c.nombre_completo} · {c.rfc}
          </option>
        ))}
      </select>
    </FormField>
  );
}
