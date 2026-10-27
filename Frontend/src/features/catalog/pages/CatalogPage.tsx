import { useState } from "react";
import { ListTree, Search } from "lucide-react";
import { PageHeader } from "@/shared/components/PageHeader";
import { EmptyState } from "@/shared/components/EmptyState";
import { inputClass } from "@/shared/components/FormField";
import { useDebouncedValue } from "@/shared/hooks/useDebouncedValue";
import { useCatalog } from "../api/useCatalog";
import { CategoryNode } from "../components/CategoryNode";

export function CatalogPage() {
  const [q, setQ] = useState("");
  const [soloActivas, setSoloActivas] = useState(false);
  const debouncedQ = useDebouncedValue(q);

  const { data, isLoading, isError } = useCatalog({ q: debouncedQ || undefined, solo_activas: soloActivas });

  const categorias = data ?? [];
  const totalSub = categorias.reduce((acc, c) => acc + c.subcategorias.length, 0);
  const activasSub = categorias.reduce((acc, c) => acc + c.subcategorias.filter((s) => s.activa).length, 0);

  return (
    <div>
      <PageHeader
        title="Catálogo de servicios"
        subtitle="Categorías y subcategorías disponibles para clasificar tareas."
      />

      <div className="mb-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <SummaryCard label="Categorías" value={categorias.length} />
        <SummaryCard label="Subcategorías" value={totalSub} />
        <SummaryCard label="Activas" value={activasSub} />
        <SummaryCard label="Inactivas" value={totalSub - activasSub} />
      </div>

      <div className="card">
        <div className="flex flex-wrap items-center gap-3 border-b border-line p-4">
          <div className="relative flex-1 min-w-[220px]">
            <Search size={16} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted" />
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Buscar categoría o subcategoría…"
              className={inputClass + " pl-10"}
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-ink">
            <input
              type="checkbox"
              checked={soloActivas}
              onChange={(e) => setSoloActivas(e.target.checked)}
              className="size-4 rounded border-line accent-navy-900"
            />
            Solo activas
          </label>
        </div>

        {isLoading ? (
          <p className="p-6 text-sm text-muted">Cargando catálogo…</p>
        ) : isError ? (
          <p className="p-6 text-sm text-danger">No se pudo cargar el catálogo.</p>
        ) : categorias.length === 0 ? (
          <EmptyState
            icon={ListTree}
            title="Sin resultados"
            description="No hay categorías que coincidan con la búsqueda."
          />
        ) : (
          <div>
            {categorias.map((c) => (
              <CategoryNode key={c.id} categoria={c} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="card px-4 py-3.5">
      <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">{label}</p>
      <p className="mt-1 font-display text-2xl font-bold text-ink">{value}</p>
    </div>
  );
}
