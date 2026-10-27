import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";
import { Avatar } from "@/shared/components/Avatar";
import { EstatusBadge } from "@/shared/components/Badge";
import { ROLE_LABELS } from "@/shared/constants/roles";
import { GRADO_LABELS } from "../types";
import type { ColaboradorListItem } from "../types";

export function UserTable({ items }: { items: ColaboradorListItem[] }) {
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="border-b border-line text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
          <th className="px-4 py-3">Colaborador</th>
          <th className="px-4 py-3">Rol / Grado</th>
          <th className="px-4 py-3">Estatus</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody className="divide-y divide-line">
        {items.map((u) => (
          <tr key={u.id} className="hover:bg-field/60">
            <td className="px-4 py-3">
              <Link to={`/colaboradores/${u.id}`} className="flex items-center gap-3">
                <Avatar nombre={u.nombre_completo} />
                <div className="min-w-0">
                  <p className="truncate font-semibold text-ink">{u.nombre_completo}</p>
                  <p className="truncate text-[12px] text-muted">{u.correo_institucional}</p>
                </div>
              </Link>
            </td>
            <td className="px-4 py-3">
              <p className="text-ink">{ROLE_LABELS[u.rol]}</p>
              <p className="text-[12px] text-muted">{GRADO_LABELS[u.grado_escalafon]}</p>
            </td>
            <td className="px-4 py-3">
              <EstatusBadge estatus={u.estatus} />
            </td>
            <td className="px-4 py-3 text-right">
              <Link to={`/colaboradores/${u.id}`} className="inline-flex items-center gap-1 text-[13px] font-medium text-navy-700 hover:underline">
                Ver ficha <ChevronRight size={14} />
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
