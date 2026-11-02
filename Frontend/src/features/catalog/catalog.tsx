import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/shared/api/client";
import { Loader2, Search, ListTree } from "lucide-react";

interface Subcategoria {
  id: number;
  nombre: string;
  activa: boolean;
  orden: number;
}

interface Categoria {
  id: number;
  nombre: string;
  activa: boolean;
  orden: number;
  subcategorias?: Subcategoria[];
}

interface CatalogResponse {
  data: Categoria[];
}

async function fetchCatalog(q: string, soloActivas: boolean): Promise<Categoria[]> {
  const res = await api.get<CatalogResponse>("/catalog", {
    params: {
      q: q.trim() || undefined,
      solo_activas: soloActivas || undefined,
    },
  });
  return res.data.data ?? [];
}

export function CatalogPage() {
  const [q, setQ] = useState("");
  const [soloActivas, setSoloActivas] = useState(false);
  const debounced = q.trim();

  const query = useQuery({
    queryKey: ["catalog", debounced, soloActivas],
    queryFn: () => fetchCatalog(debounced, soloActivas),
    staleTime: 30_000,
  });

  const items = query.data ?? [];
  const totalSubs = useMemo(
    () => items.reduce((acc, c) => acc + (c.subcategorias?.length ?? 0), 0),
    [items],
  );

  return (
    <div className="mx-auto flex w-full max-w-[1240px] flex-col gap-4">
      <header className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo 4 · Catálogo de proyectos y actividades
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold text-ink sm:text-3xl">
            Catálogo de Servicios
          </h1>
          <p className="mt-1.5 max-w-2xl text-sm text-muted">
            Árbol de categorías y subcategorías disponibles para clasificar tareas y obligaciones.
          </p>
        </div>
        <label className="inline-flex items-center gap-2 text-sm text-ink">
          <input
            type="checkbox"
            checked={soloActivas}
            onChange={(e) => setSoloActivas(e.target.checked)}
            className="size-4 rounded border-line accent-navy-900"
          />
          Solo activas
        </label>
      </header>

      <div className="card flex items-center gap-2 p-3">
        <Search size={16} className="text-muted" />
        <input
          type="search"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="Buscar categoría o subcategoría…"
          className="w-full bg-transparent text-sm text-ink outline-none placeholder:text-muted/70"
        />
      </div>

      {query.isLoading && (
        <div className="card flex items-center justify-center gap-2 p-8 text-muted">
          <Loader2 size={18} className="animate-spin" />
          Cargando catálogo…
        </div>
      )}

      {query.isError && (
        <div className="card p-6 text-center text-sm text-danger">
          No se pudo cargar el catálogo.
        </div>
      )}

      {!query.isLoading && !query.isError && items.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
            <ListTree size={22} />
          </span>
          <p className="text-sm text-muted">Sin resultados para los filtros seleccionados.</p>
        </div>
      )}

      {!query.isLoading && !query.isError && items.length > 0 && (
        <section className="flex flex-col gap-3">
          <p className="text-[11px] text-muted">
            {items.length} categorías · {totalSubs} subcategorías
          </p>
          <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
            {items.map((categoria) => (
              <article key={categoria.id} className="card p-4">
                <header className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="font-display text-base font-bold text-ink">
                      {categoria.nombre}
                    </h2>
                    <p className="text-[10px] uppercase tracking-wide text-muted">
                      Orden {categoria.orden}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                      categoria.activa
                        ? "bg-emerald-50 text-emerald-700"
                        : "bg-app text-muted"
                    }`}
                  >
                    {categoria.activa ? "Activa" : "Inactiva"}
                  </span>
                </header>
                {categoria.subcategorias && categoria.subcategorias.length > 0 ? (
                  <ul className="mt-3 flex flex-col gap-1.5">
                    {categoria.subcategorias.map((sub) => (
                      <li
                        key={sub.id}
                        className="flex items-center justify-between rounded-lg bg-app/60 px-3 py-2 text-xs"
                      >
                        <span className="font-medium text-ink">{sub.nombre}</span>
                        <span
                          className={`rounded-full px-2 py-0.5 text-[9.5px] font-semibold ${
                            sub.activa ? "bg-emerald-50 text-emerald-700" : "bg-line text-muted"
                          }`}
                        >
                          {sub.activa ? "Activa" : "Inactiva"}
                        </span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="mt-3 text-[11px] italic text-muted">
                    Sin subcategorías registradas.
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}