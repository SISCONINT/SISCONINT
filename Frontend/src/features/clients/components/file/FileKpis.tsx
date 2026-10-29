import { Clock3, ListChecks, Mail, ShieldCheck } from "lucide-react";
import type { ClienteExpediente } from "../../types";
import { formatHours, formatNumber } from "../../utils";
import { StatusBadge } from "../ClientBadges";

export function FileKpis({ cliente }: { cliente: ClienteExpediente }) {
  return (
    <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
      <article className="card flex items-center gap-3 p-3.5">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-navy-900 text-gold-500">
          <Mail size={16} />
        </span>
        <div className="min-w-0">
          <p className="text-[9.5px] font-semibold uppercase tracking-[0.12em] text-muted">
            Contacto principal
          </p>
          <p className="truncate text-[12px] font-semibold text-ink">
            {cliente.contacto_principal_correo ?? cliente.correo ?? "Sin registro"}
          </p>
        </div>
      </article>

      <article className="card flex items-center gap-3 p-3.5">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-gold-300/60 text-navy-900">
          <ListChecks size={16} />
        </span>
        <div>
          <p className="text-[9.5px] font-semibold uppercase tracking-[0.12em] text-muted">
            Tareas activas
          </p>
          <p className="text-[12px] font-semibold text-ink">
            {formatNumber(cliente.tareas_activas)}
            <span className="ml-1 font-normal text-muted">
              {cliente.tareas_activas === 1 ? "pendiente" : "en proceso"}
            </span>
          </p>
        </div>
      </article>

      <article className="card flex items-center gap-3 p-3.5">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-app text-navy-800">
          <Clock3 size={16} />
        </span>
        <div>
          <p className="text-[9.5px] font-semibold uppercase tracking-[0.12em] text-muted">
            Horas registradas
          </p>
          <p className="text-[12px] font-semibold text-ink">
            {formatHours(cliente.horas_registradas)}
            <span className="ml-1 font-normal text-muted">hrs acumuladas</span>
          </p>
        </div>
      </article>

      <article className="card flex items-center gap-3 p-3.5">
        <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-app text-navy-800">
          <ShieldCheck size={16} />
        </span>
        <div>
          <p className="text-[9.5px] font-semibold uppercase tracking-[0.12em] text-muted">
            Estatus del expediente
          </p>
          <div className="mt-0.5 flex items-center gap-1.5">
            <StatusBadge estatus={cliente.estatus} />
          </div>
        </div>
      </article>
    </div>
  );
}
