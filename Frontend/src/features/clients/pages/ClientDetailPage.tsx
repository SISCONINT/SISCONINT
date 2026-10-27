import { useLocation, useNavigate, useParams, Link } from "react-router-dom";
import { ChevronRight, Plus } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { EstadoBadge, EstatusBadge, PrioridadBadge, SemaforoDot } from "@/shared/components/Badge";
import { EmptyState } from "@/shared/components/EmptyState";
import { formatDate } from "@/shared/utils/format";
import { useTasks } from "@/features/tasks/api/useTasks";
import type { ClienteListItem } from "../types";

const TIPO_LABEL: Record<string, string> = { FISICA: "Física", MORAL: "Moral" };

export function ClientDetailPage() {
  const { id } = useParams();
  const clienteId = Number(id);
  const location = useLocation();
  const navigate = useNavigate();
  const item = (location.state as { item?: ClienteListItem } | null)?.item;

  const { data: tasksData, isLoading: loadingTasks } = useTasks({ cliente: clienteId, page: 1 });
  const tareas = tasksData?.data ?? [];

  if (!item) {
    return (
      <div>
        <PageHeader title="Expediente de cliente" crumbs={[{ label: "Clientes", to: "/clientes" }]} />
        <EmptyState
          title="Abre el expediente desde la lista"
          description="El backend todavía no tiene un endpoint para consultar un cliente por id directamente, así que esta vista usa los datos de la fila que seleccionaste en el listado."
          action={
            <Link to="/clientes" className="rounded-lg bg-gold-300 px-4 py-2 text-sm font-semibold text-ink">
              Ir al listado de clientes
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={item.razon_social || item.nombre_completo}
        subtitle={`RFC ${item.rfc} · Persona ${TIPO_LABEL[item.tipo_persona] ?? item.tipo_persona}`}
        crumbs={[{ label: "Clientes", to: "/clientes" }, { label: item.nombre_completo }]}
        actions={
          <button
            type="button"
            onClick={() => navigate("/tareas/nuevo", { state: { clienteId } })}
            className="flex items-center gap-2 rounded-lg bg-gold-300 px-4 py-2.5 text-sm font-semibold text-ink hover:brightness-95"
          >
            <Plus size={16} /> Nueva tarea para este cliente
          </button>
        }
      />

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div className="card px-4 py-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Estatus</p>
          <p className="mt-1.5">
            <EstatusBadge estatus={item.estatus} />
          </p>
        </div>
        <div className="card px-4 py-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Tareas activas</p>
          <p className="mt-1 font-display text-2xl font-bold text-ink">{item.tareas_activas}</p>
        </div>
        <div className="card px-4 py-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Horas registradas</p>
          <p className="mt-1 font-display text-2xl font-bold text-ink">{item.horas_registradas.toFixed(1)}</p>
        </div>
        <div className="card px-4 py-3.5">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">Contacto principal</p>
          <p className="mt-1.5 truncate text-sm font-medium text-ink">{item.contacto_principal_correo ?? "—"}</p>
        </div>
      </div>

      <div className="card mb-5 p-5">
        <h3 className="mb-1 font-semibold text-ink">Nota sobre este expediente</h3>
        <p className="text-sm text-muted">
          La edición de datos generales, domicilio fiscal, régimen y contactos (HU_14) todavía no está disponible en esta
          rama del backend. En cuanto se publique el endpoint de consulta y edición por id, este expediente mostrará esos
          datos completos y el botón de editar.
        </p>
      </div>

      <div className="card">
        <div className="border-b border-line p-4">
          <h3 className="font-semibold text-ink">Tareas de este cliente</h3>
        </div>
        {loadingTasks ? (
          <p className="p-6 text-sm text-muted">Cargando tareas…</p>
        ) : tareas.length === 0 ? (
          <EmptyState title="Sin tareas" description="Este cliente no tiene tareas registradas todavía." />
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-line text-left text-[11px] font-semibold uppercase tracking-wide text-muted">
                <th className="px-4 py-3">Tarea</th>
                <th className="px-4 py-3">Responsable</th>
                <th className="px-4 py-3">Prioridad</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3">Fecha límite</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {tareas.map((t) => (
                <tr key={t.id} className="hover:bg-field/60">
                  <td className="px-4 py-3 font-semibold text-ink">{t.titulo}</td>
                  <td className="px-4 py-3 text-ink">{t.asignado_nombre}</td>
                  <td className="px-4 py-3">
                    <PrioridadBadge prioridad={t.prioridad} />
                  </td>
                  <td className="px-4 py-3">
                    <EstadoBadge estado={t.estado} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 text-ink">
                      <SemaforoDot semaforo={t.semaforo} /> {formatDate(t.fecha_limite)}
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
        )}
      </div>
    </div>
  );
}
