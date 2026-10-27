import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { EstatusBadge } from "@/shared/components/Badge";
import type { ClienteListItem } from "../types";

const TIPO_LABEL: Record<string, string> = { FISICA: "Física", MORAL: "Moral" };

export function ClientTable({ items }: { items: ClienteListItem[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-line text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
          <th className="px-4 py-3">Cliente</th>
          <th className="px-4 py-3">RFC</th>
          <th className="px-4 py-3">Tipo</th>
          <th className="px-4 py-3">Tareas activas</th>
          <th className="px-4 py-3">Horas registradas</th>
          <th className="px-4 py-3">Estatus</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {items.map((c) => (
          <tr key={c.id} className="hover:bg-field/60">
            <td className="px-4 py-3">
              <Link to={`/clientes/${c.id}`} state={{ item: c }} className="min-w-0">
                <p className="truncate font-semibold text-ink">{c.razon_social || c.nombre_completo}</p>
                {c.contacto_principal_correo && <p className="truncate text-[12px] text-muted">{c.contacto_principal_correo}</p>}
              </Link>
            </td>
            <td className="px-4 py-3 font-mono text-[13px] text-ink">{c.rfc}</td>
            <td className="px-4 py-3 text-ink">{TIPO_LABEL[c.tipo_persona] ?? c.tipo_persona}</td>
            <td className="px-4 py-3 text-ink">{c.tareas_activas}</td>
            <td className="px-4 py-3 text-ink">{c.horas_registradas.toFixed(1)} hrs</td>
            <td className="px-4 py-3">
              <EstatusBadge estatus={c.estatus} />
            </td>
            <td className="px-4 py-3 text-right">
              <Link to={`/clientes/${c.id}`} state={{ item: c }} className="inline-flex items-center gap-1 text-[13px] font-medium text-navy-700 hover:underline">
                Ver expediente <ChevronRight size={14} />
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
