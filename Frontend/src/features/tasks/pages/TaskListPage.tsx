import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ChevronRight, ListTodo, Plus } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { Pagination } from "@/shared/components/Pagination";
import { SearchableSelect } from "@/shared/components/SearchableSelect";
import { inputClass } from "@/shared/components/FormField";
import { Avatar } from "@/shared/components/Avatar";
import { EstadoBadge, PrioridadBadge, SemaforoDot } from "@/shared/components/Badge";
import { formatDate } from "@/shared/utils/format";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { useClienteOptions } from "@/features/clients/api/useClients";
import { useColaboradorOptions } from "@/features/users/api/useUsers";
import { useTasks } from "../api/useTasks";
import type { Estado, Prioridad } from "../types";

export function TaskListPage() {
  const navigate = useNavigate();
  const actor = useAuthStore((s) => s.user);
  const canFilterResponsable = actor?.rol !== ROLES.CONTADOR;

  const [clienteId, setClienteId] = useState<number | null>(null);
  const [clienteQuery, setClienteQuery] = useState("");
  const [responsableId, setResponsableId] = useState<number | null>(null);
  const [responsableQuery, setResponsableQuery] = useState("");
  const [estado, setEstado] = useState<Estado | "">("");
  const [prioridad, setPrioridad] = useState<Prioridad | "">("");
  const [page, setPage] = useState(1);

  const { options: clienteOptions, isLoading: loadingClientes } = useClienteOptions(clienteQuery);
  const { options: responsableOptions, isLoading: loadingResponsables } = useColaboradorOptions(responsableQuery);

  const { data, isLoading, isError } = useTasks({
    cliente: clienteId ?? undefined,
    responsable: canFilterResponsable ? responsableId ?? undefined : undefined,
    estado: estado || undefined,
    prioridad: prioridad || undefined,
    page,
  });

  const items = data?.data ?? [];
  const meta = data?.meta;

  return (
    <div>
      <PageHeader
        title="Tareas"
        subtitle="Listado de tareas con su semáforo de vencimiento (HU_30)."
        actions={
          <button
            type="button"
            onClick={() => navigate("/tareas/nuevo")}
            className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
          >
            <Plus size={16} /> Nueva tarea
          </button>
        }
      />

      <div className="card">
        <div className="flex flex-wrap items-center gap-2.5 border-b border-line p-4">
          <div className="w-52">
            <SearchableSelect
              value={clienteId}
              onChange={(v) => {
                setClienteId(v);
                setPage(1);
              }}
              options={clienteOptions}
              loading={loadingClientes}
              query={clienteQuery}
              onQueryChange={setClienteQuery}
              placeholder="Cliente…"
            />
          </div>
          {canFilterResponsable && (
            <div className="w-52">
              <SearchableSelect
                value={responsableId}
                onChange={(v) => {
                  setResponsableId(v);
                  setPage(1);
                }}
                options={responsableOptions}
                loading={loadingResponsables}
                query={responsableQuery}
                onQueryChange={setResponsableQuery}
                placeholder="Responsable…"
              />
            </div>
          )}
          <select
            value={estado}
            onChange={(e) => {
              setEstado(e.target.value as Estado | "");
              setPage(1);
            }}
            className={inputClass + " w-44 pl-4"}
          >
            <option value="">Todo estado</option>
            <option value="POR_HACER">Por hacer</option>
            <option value="EN_PROGRESO">En progreso</option>
            <option value="EN_REVISION">En revisión</option>
            <option value="COMPLETADO">Completado</option>
          </select>
          <select
            value={prioridad}
            onChange={(e) => {
              setPrioridad(e.target.value as Prioridad | "");
              setPage(1);
            }}
            className={inputClass + " w-40 pl-4"}
          >
            <option value="">Toda prioridad</option>
            <option value="ALTA">Alta</option>
            <option value="MEDIA">Media</option>
            <option value="BAJA">Baja</option>
          </select>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted">Cargando tareas…</p>
        ) : isError ? (
          <p className="p-6 text-sm text-danger">No se pudo cargar el listado.</p>
        ) : items.length === 0 ? (
          <EmptyState icon={ListTodo} title="Sin tareas" description="No hay tareas con estos filtros." />
        ) : (
          <>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
                  <th className="px-4 py-3">Tarea</th>
                  <th className="px-4 py-3">Cliente</th>
                  <th className="px-4 py-3">Responsable</th>
                  <th className="px-4 py-3">Prioridad</th>
                  <th className="px-4 py-3">Estado</th>
                  <th className="px-4 py-3">Fecha límite</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {items.map((t) => (
                  <tr key={t.id} className="hover:bg-field/60">
                    <td className="px-4 py-3">
                      <Link to={`/tareas/${t.id}`} className="font-semibold text-ink hover:underline">
                        {t.titulo}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-ink">{t.cliente_nombre ?? "—"}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Avatar nombre={t.asignado_nombre} size={24} />
                        <span className="text-ink">{t.asignado_nombre ?? "—"}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <PrioridadBadge prioridad={t.prioridad} />
                    </td>
                    <td className="px-4 py-3">
                      <EstadoBadge estado={t.estado} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 text-ink">
                        <SemaforoDot semaforo={t.semaforo} />
                        {formatDate(t.fecha_limite)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Link to={`/tareas/${t.id}`} className="inline-flex items-center gap-1 text-[13px] font-medium text-navy-700 hover:underline">
                        Ver <ChevronRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {meta && (
              <Pagination page={meta.page} pages={meta.pages ?? 1} total={meta.total} perPage={meta.per_page} onChange={setPage} />
            )}
          </>
        )}
      </div>
    </div>
  );
}
