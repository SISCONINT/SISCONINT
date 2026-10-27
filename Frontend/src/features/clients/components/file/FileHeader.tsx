import { Link } from "react-router-dom";
import { ArrowLeft, Mail, Plus, ShieldCheck } from "lucide-react";
import { BTN_PRIMARY, BTN_SECONDARY, TIPO_PERSONA_LABELS } from "../../constants";
import type { ClienteExpediente } from "../../types";
import { ClientAvatar } from "../ClientAvatar";
import { StatusBadge, TipoPersonaBadge } from "../ClientBadges";

export function FileHeader({ cliente }: { cliente: ClienteExpediente }) {
  const correo = cliente.correo ?? cliente.contacto_principal_correo;

  return (
    <header className="card overflow-hidden">
      <div className="flex flex-col gap-4 p-5 lg:flex-row lg:items-start lg:justify-between">
        <div className="flex min-w-0 items-start gap-4">
          <div className="relative shrink-0">
            <ClientAvatar name={cliente.nombre_completo} size="xl" />
            <span className="absolute -bottom-1 -right-1 grid size-7 place-items-center rounded-full border-2 border-surface bg-gold-300 text-navy-900">
              <ShieldCheck size={14} />
            </span>
          </div>

          <div className="min-w-0">
            <p className="text-[10px] font-semibold uppercase tracking-[0.14em] text-gold-700">
              Expediente fiscal #{cliente.id}
            </p>
            <h1 className="mt-0.5 font-display text-2xl font-bold leading-tight text-ink">
              {cliente.nombre_completo}
            </h1>
            {cliente.razon_social && cliente.razon_social !== cliente.nombre_completo && (
              <p className="mt-0.5 text-[13px] text-muted">{cliente.razon_social}</p>
            )}

            <div className="mt-2 flex flex-wrap items-center gap-1.5">
              <span className="rounded bg-field px-2 py-0.5 text-[11px] font-semibold tracking-wide text-navy-800">
                {cliente.rfc}
              </span>
              <TipoPersonaBadge tipo={cliente.tipo_persona} />
              <StatusBadge estatus={cliente.estatus} />
              <span className="text-[11px] text-muted">{TIPO_PERSONA_LABELS[cliente.tipo_persona]}</span>
            </div>

            {cliente.giro && (
              <p className="mt-2 text-[11.5px] leading-snug text-muted">
                <span className="font-semibold text-ink">Giro:</span> {cliente.giro}
              </p>
            )}

            <p className="mt-1.5 inline-flex items-center gap-1.5 text-[11px] text-muted">
              <Mail size={13} />
              {correo ? <span className="break-all">{correo}</span> : "Sin correo registrado"}
            </p>
          </div>
        </div>

        <div className="flex flex-col gap-2 sm:flex-row lg:shrink-0 lg:flex-col xl:flex-row">
          <Link to="/clientes" className={BTN_SECONDARY}>
            <ArrowLeft size={15} />
            Cartera
          </Link>
          <Link to={`/tareas?cliente=${cliente.id}`} className={BTN_PRIMARY}>
            <Plus size={16} />
            Nueva tarea
          </Link>
        </div>
      </div>
    </header>
  );
}
