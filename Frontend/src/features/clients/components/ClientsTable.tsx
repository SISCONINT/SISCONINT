import { Link } from "react-router-dom";
import { ArrowUpRight, Clock3, ListChecks, Mail, ChevronRight } from "lucide-react";
import clsx from "clsx";
import type { ClienteListItem } from "../types";
import { TIPO_PERSONA_LABELS } from "../constants";
import { formatHours, formatNumber } from "../utils";
import { ClientAvatar } from "./ClientAvatar";
import { StatusBadge } from "./ClientBadges";

interface Props {
  items: ClienteListItem[];
  loading: boolean;
}

function TareasPill({ count }: { count: number }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold",
        count > 0 ? "bg-gold-300/45 text-navy-900" : "bg-app text-muted",
      )}
    >
      <ListChecks size={12} />
      {count} {count === 1 ? "activa" : "activas"}
    </span>
  );
}

function ContactLine({ email }: { email: string | null }) {
  if (!email) return <span className="text-xs italic text-muted">Sin contacto registrado</span>;
  return (
    <span className="flex min-w-0 items-center gap-1.5 text-xs text-ink">
      <Mail size={13} className="shrink-0 text-muted" />
      <span className="truncate" title={email}>
        {email}
      </span>
    </span>
  );
}

function RowSkeleton() {
  return (
    <tr className="animate-pulse">
      <td className="px-5 py-4">
        <div className="flex items-center gap-3">
          <div className="size-10 rounded-xl bg-line" />
          <div className="space-y-2">
            <div className="h-3.5 w-48 rounded bg-line" />
            <div className="h-2.5 w-32 rounded bg-line" />
          </div>
        </div>
      </td>
      <td className="hidden px-4 py-4 xl:table-cell"><div className="h-3 w-36 rounded bg-line" /></td>
      <td className="px-4 py-4"><div className="h-5 w-16 rounded-full bg-line" /></td>
      <td className="hidden px-4 py-4 xl:table-cell"><div className="h-3 w-12 rounded bg-line" /></td>
      <td className="px-4 py-4"><div className="h-5 w-16 rounded-full bg-line" /></td>
      <td className="px-5 py-4"><div className="ml-auto h-3 w-24 rounded bg-line" /></td>
    </tr>
  );
}

export function ClientsTable({ items, loading }: Props) {
  return (
    <>
      {/* Escritorio */}
      <div className="card hidden overflow-x-auto lg:block">
        <table className="w-full text-left">
          <thead className="border-b border-line bg-app/60">
            <tr className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
              <th scope="col" className="px-5 py-3">Cliente / contribuyente</th>
              <th scope="col" className="hidden px-4 py-3 xl:table-cell">Contacto principal</th>
              <th scope="col" className="px-4 py-3">Tareas activas</th>
              <th scope="col" className="hidden px-4 py-3 xl:table-cell">Horas registradas</th>
              <th scope="col" className="px-4 py-3">Estatus</th>
              <th scope="col" className="px-5 py-3 text-right">Expediente</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-line">
            {loading
              ? Array.from({ length: 6 }).map((_, index) => <RowSkeleton key={index} />)
              : items.map((cliente) => (
                  <tr key={cliente.id} className="group transition hover:bg-app/60">
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <ClientAvatar name={cliente.nombre_completo} />
                        <div className="min-w-0">
                          <p className="truncate text-sm font-semibold text-ink">
                            {cliente.nombre_completo}
                          </p>
                          {cliente.razon_social && cliente.razon_social !== cliente.nombre_completo && (
                            <p className="truncate text-[11px] text-muted">{cliente.razon_social}</p>
                          )}
                          <p className="mt-1 flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
                            <span className="rounded bg-field px-1.5 py-0.5 font-semibold tracking-wide text-navy-800">
                              {cliente.rfc}
                            </span>
                            <span aria-hidden="true">·</span>
                            {TIPO_PERSONA_LABELS[cliente.tipo_persona]}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="max-w-[220px] hidden px-4 py-4 xl:table-cell">
                      <ContactLine email={cliente.contacto_principal_correo} />
                    </td>
                    <td className="px-4 py-4">
                      <TareasPill count={cliente.tareas_activas} />
                    </td>
                    <td className="hidden px-4 py-4 xl:table-cell">
                      <p className="text-sm font-semibold text-ink">
                        {formatHours(cliente.horas_registradas)}
                        <span className="ml-1 text-[11px] font-normal text-muted">hrs</span>
                      </p>
                      <div className="mt-1.5 h-1 w-16 overflow-hidden rounded-full bg-line">
                        <div
                          className="h-full rounded-full bg-gold-500"
                          style={{ width: `${Math.min(100, cliente.horas_registradas * 1.2)}%` }}
                        />
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <StatusBadge estatus={cliente.estatus} />
                    </td>
                    <td className="px-5 py-4 text-right">
                      <Link
                        to={`/clientes/${cliente.id}`}
                        state={{ cliente }}
                        className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold text-navy-800 transition hover:bg-navy-900/5 hover:text-navy-900"
                      >
                        Ver expediente
                        <ArrowUpRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>

      {/* Móvil / tableta */}
      <div className="grid gap-3 sm:grid-cols-2 lg:hidden">
        {loading
          ? Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="card animate-pulse p-4">
                <div className="flex items-center gap-3">
                  <div className="size-10 rounded-xl bg-line" />
                  <div className="flex-1 space-y-2">
                    <div className="h-3.5 w-40 rounded bg-line" />
                    <div className="h-2.5 w-24 rounded bg-line" />
                  </div>
                </div>
                <div className="mt-4 h-2.5 w-full rounded bg-line" />
              </div>
            ))
          : items.map((cliente) => (
              <Link
                key={cliente.id}
                to={`/clientes/${cliente.id}`}
                state={{ cliente }}
                className="card block p-4 transition hover:border-navy-900/20"
              >
                <div className="flex items-start gap-3">
                  <ClientAvatar name={cliente.nombre_completo} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink">
                      {cliente.nombre_completo}
                    </p>
                    <p className="truncate text-[11px] text-muted">
                      {cliente.razon_social ?? TIPO_PERSONA_LABELS[cliente.tipo_persona]}
                    </p>
                  </div>
                  <ChevronRight size={16} className="mt-1 shrink-0 text-muted" />
                </div>

                <div className="mt-3 flex flex-wrap items-center gap-1.5">
                  <span className="rounded bg-field px-1.5 py-0.5 text-[10px] font-semibold text-navy-800">
                    {cliente.rfc}
                  </span>
                  <TareasPill count={cliente.tareas_activas} />
                  <StatusBadge estatus={cliente.estatus} />
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2 border-t border-line pt-3 text-[11px]">
                  <div className="min-w-0">
                    <p className="mb-0.5 text-muted">Contacto</p>
                    {cliente.contacto_principal_correo ? (
                      <p className="truncate text-ink">{cliente.contacto_principal_correo}</p>
                    ) : (
                      <p className="italic text-muted">Sin registro</p>
                    )}
                  </div>
                  <div>
                    <p className="mb-0.5 flex items-center gap-1 text-muted">
                      <Clock3 size={11} /> Horas
                    </p>
                    <p className="font-semibold text-ink">
                      {formatHours(cliente.horas_registradas)} hrs
                      <span className="ml-1 font-normal text-muted">
                        · {formatNumber(cliente.tareas_activas)} tareas
                      </span>
                    </p>
                  </div>
                </div>
              </Link>
            ))}
      </div>
    </>
  );
}
