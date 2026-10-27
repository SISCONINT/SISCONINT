import { FileSearch, Landmark, ShieldCheck, Clock3 } from "lucide-react";
import type { ClienteExpediente } from "../../types";
import { regimenDescription, regimenName } from "../../utils";
import { PanelCard } from "./PanelCard";

function PendingCard({ label, text }: { label: string; text: string }) {
  return (
    <div className="flex items-start gap-2.5 rounded-lg bg-app/70 px-3 py-3">
      <Clock3 size={15} className="mt-0.5 shrink-0 text-muted" />
      <div>
        <p className="text-[12px] font-semibold text-ink">{label}</p>
        <p className="mt-0.5 text-[10.5px] leading-snug text-muted">{text}</p>
      </div>
    </div>
  );
}

export function FiscalPanel({ cliente }: { cliente: ClienteExpediente }) {
  const regimenes = cliente.regimenes ?? [];

  return (
    <div className="grid gap-3 lg:grid-cols-5">
      <PanelCard
        icon={Landmark}
        title="Regímenes fiscales vigentes"
        subtitle="Catálogo Anexo 20 del SAT"
        className="lg:col-span-3"
        aside={
          <span className="rounded-full bg-app px-2 py-0.5 text-[10px] font-semibold text-muted">
            {regimenes.length} {regimenes.length === 1 ? "régimen" : "regímenes"}
          </span>
        }
      >
        {regimenes.length > 0 ? (
          <ul className="grid gap-2 sm:grid-cols-2">
            {regimenes.map((clave) => (
              <li key={clave} className="rounded-lg border border-line bg-surface p-3">
                <span className="inline-flex rounded bg-navy-900 px-1.5 py-0.5 text-[9.5px] font-bold tracking-wider text-gold-300">
                  CLAVE {clave}
                </span>
                <p className="mt-1.5 text-[12px] font-semibold leading-snug text-ink">
                  {regimenName(clave)}
                </p>
                <p className="mt-0.5 text-[10.5px] leading-snug text-muted">
                  {regimenDescription(clave)}
                </p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="rounded-lg bg-app/70 px-3 py-5 text-center text-[11px] text-muted">
            Los regímenes fiscales se mostrarán aquí cuando el expediente completo esté disponible.
          </p>
        )}
      </PanelCard>

      <div className="flex flex-col gap-3 lg:col-span-2">
        <PanelCard icon={ShieldCheck} title="Opinión de cumplimiento 32-D">
          <PendingCard
            label="Pendiente de sincronización"
            text="La opinión se consultará automáticamente con el monitoreo fiscal del SAT."
          />
        </PanelCard>
        <PanelCard icon={FileSearch} title="Constancia de Situación Fiscal">
          <PendingCard
            label="Sin constancia cargada"
            text="El documento PDF del SAT podrá adjuntarse al expediente en una próxima actualización."
          />
        </PanelCard>
      </div>
    </div>
  );
}
