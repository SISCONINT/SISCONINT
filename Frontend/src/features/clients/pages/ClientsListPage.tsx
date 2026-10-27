import { useCallback, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  Download,
  Loader2,
  Plus,
  RefreshCw,
  ShieldCheck,
  Users,
} from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import { clientsApi } from "../api/clientsApi";
import { useAccountants, useClients, useClientsSummary } from "../api/useClients";
import { ClientFilters } from "../components/ClientFilters";
import { ClientsKpiCards } from "../components/ClientsKpiCards";
import { ClientsTable } from "../components/ClientsTable";
import { Pagination } from "../components/Pagination";
import { BTN_PRIMARY, BTN_SECONDARY, ESTATUS_CLIENTE, ESTATUS_LABELS, TIPO_PERSONA_LABELS } from "../constants";
import { useDebouncedValue } from "../hooks";
import type { ClientesQuery, EstatusCliente, TipoPersona } from "../types";
import { downloadCsv } from "../utils";

function readFilters(params: URLSearchParams): ClientesQuery {
  const estatus = params.get("estatus");
  const tipo = params.get("tipo_persona");
  const contador = Number(params.get("contador"));
  const page = Number(params.get("page"));

  return {
    q: params.get("q") ?? "",
    estatus: ESTATUS_CLIENTE.includes(estatus as EstatusCliente)
      ? (estatus as EstatusCliente)
      : "ACTIVO",
    tipo_persona: tipo === "FISICA" || tipo === "MORAL" ? (tipo as TipoPersona) : null,
    contador: Number.isInteger(contador) && contador > 0 ? contador : undefined,
    page: Number.isInteger(page) && page > 0 ? page : 1,
  };
}

export function ClientsListPage() {
  const user = useAuthStore((state) => state.user);
  const [searchParams, setSearchParams] = useSearchParams();
  const filters = useMemo(() => readFilters(searchParams), [searchParams]);

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const canManageClients =
    user?.rol === ROLES.DUENO || user?.rol === ROLES.ADMINISTRADOR;
  const canFilterByAccountant = canManageClients;

  const updateFilters = useCallback(
    (patch: Partial<ClientesQuery>) => {
      const next = { ...filters, ...patch };
      const params = new URLSearchParams();

      if (next.q) params.set("q", next.q);
      if (next.estatus !== "ACTIVO") params.set("estatus", next.estatus);
      if (next.tipo_persona) params.set("tipo_persona", next.tipo_persona);
      if (next.contador) params.set("contador", String(next.contador));
      if (next.page > 1) params.set("page", String(next.page));

      setSearchParams(params, { replace: true });
    },
    [filters, setSearchParams],
  );

  // La barra de búsqueda se refleja en la URL al instante; la consulta espera el debounce.
  const debouncedSearch = useDebouncedValue(filters.q, 350);
  const queryFilters = useMemo(
    () => ({ ...filters, q: debouncedSearch }),
    [filters, debouncedSearch],
  );

  const clientsQuery = useClients(queryFilters);
  const summary = useClientsSummary();
  const accountantsQuery = useAccountants(canFilterByAccountant);

  const items = clientsQuery.data?.items ?? [];
  const total = clientsQuery.data?.meta.total ?? 0;
  const perPage = clientsQuery.data?.meta.per_page ?? 20;
  const isInitialLoading = clientsQuery.isLoading && !clientsQuery.data;

  const [activos = 0, pausados = 0, bajas = 0] = summary.map((query) => query.data ?? 0);
  const summaryLoading = summary.some((query) => query.isLoading);

  const hasActiveFilters =
    filters.q !== "" ||
    filters.tipo_persona !== null ||
    filters.contador !== undefined ||
    filters.estatus !== "ACTIVO";

  const handleClear = () => {
    updateFilters({
      q: "",
      estatus: "ACTIVO",
      tipo_persona: null,
      contador: undefined,
      page: 1,
    });
  };

  const handleExport = async () => {
    setExporting(true);
    setExportError(null);
    try {
      const rows = await clientsApi.listAll(queryFilters);
      downloadCsv(`padron-clientes-${new Date().toISOString().slice(0, 10)}.csv`, [
        [
          "Cliente / contribuyente",
          "Razón social",
          "RFC",
          "Tipo de persona",
          "Contacto principal",
          "Tareas activas",
          "Horas registradas",
          "Estatus",
        ],
        ...rows.map((cliente) => [
          cliente.nombre_completo,
          cliente.razon_social ?? "",
          cliente.rfc,
          TIPO_PERSONA_LABELS[cliente.tipo_persona],
          cliente.contacto_principal_correo ?? "",
          cliente.tareas_activas,
          cliente.horas_registradas,
          ESTATUS_LABELS[cliente.estatus],
        ]),
      ]);
    } catch (error) {
      setExportError(
        error instanceof ApiError ? error.message : "No se pudo exportar el padrón.",
      );
    } finally {
      setExporting(false);
    }
  };

  const handlePageChange = (page: number) => {
    updateFilters({ page });
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="max-w-2xl">
          <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
            <span>Gestión</span>
            <span aria-hidden="true">/</span>
            <span className="font-semibold text-navy-800">Cartera de clientes</span>
          </nav>

          <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-gold-700">
            Módulo de gobierno fiduciario
          </p>
          <h1 className="mt-1 font-display text-2xl font-bold leading-tight text-ink sm:text-3xl">
            Cartera de Clientes y Contribuyentes
          </h1>
          <p className="mt-1.5 text-sm text-muted">
            Control centralizado de expedientes fiscales, régimen tributario SAT y
            asignación contable para personas físicas y morales.
          </p>
        </div>

        <div className="flex flex-col items-stretch gap-2 sm:flex-row sm:items-center">
          <button
            type="button"
            onClick={handleExport}
            disabled={exporting || total === 0}
            className={BTN_SECONDARY}
          >
            {exporting ? <Loader2 size={16} className="animate-spin" /> : <Download size={16} />}
            {exporting ? "Generando…" : "Exportar padrón"}
          </button>

          {canManageClients && (
            <Link to="/clientes/nuevo" className={BTN_PRIMARY}>
              <Plus size={17} />
              Nuevo cliente
            </Link>
          )}
        </div>
      </header>

      {exportError && (
        <p role="alert" className="rounded-lg bg-red-50 px-4 py-2.5 text-xs font-medium text-danger">
          {exportError}
        </p>
      )}

      <ClientsKpiCards
        activos={activos}
        pausados={pausados}
        bajas={bajas}
        loading={summaryLoading}
      />

      <ClientFilters
        q={filters.q}
        estatus={filters.estatus}
        tipoPersona={filters.tipo_persona}
        contador={filters.contador}
        canFilterByAccountant={canFilterByAccountant}
        accountants={accountantsQuery.data ?? []}
        accountantsLoading={accountantsQuery.isLoading}
        accountantsError={accountantsQuery.isError}
        total={total}
        isFetching={clientsQuery.isFetching}
        onSearchChange={(value) => updateFilters({ q: value, page: 1 })}
        onEstatusChange={(estatus) => updateFilters({ estatus, page: 1 })}
        onTipoPersonaChange={(tipo_persona) => updateFilters({ tipo_persona, page: 1 })}
        onContadorChange={(contador) => updateFilters({ contador, page: 1 })}
        onClear={handleClear}
      />

      {clientsQuery.isError && (
        <div role="alert" className="card flex flex-col items-center gap-3 px-6 py-12 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-red-50 text-danger">
            <AlertTriangle size={22} />
          </span>
          <div>
            <h2 className="font-display text-lg font-bold text-ink">No se pudo cargar la cartera</h2>
            <p className="mt-1 max-w-md text-sm text-muted">
              {clientsQuery.error instanceof ApiError
                ? clientsQuery.error.message
                : "Ocurrió un error inesperado al consultar los clientes."}
            </p>
          </div>
          <button type="button" onClick={() => clientsQuery.refetch()} className={BTN_SECONDARY}>
            <RefreshCw size={15} />
            Reintentar
          </button>
        </div>
      )}

      {!clientsQuery.isError && !isInitialLoading && items.length === 0 && (
        <div className="card flex flex-col items-center gap-3 px-6 py-14 text-center">
          <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
            <Users size={22} />
          </span>
          <div>
            <h2 className="font-display text-lg font-bold text-ink">
              {hasActiveFilters ? "Sin resultados con estos filtros" : "La cartera está vacía"}
            </h2>
            <p className="mt-1 max-w-md text-sm text-muted">
              {hasActiveFilters
                ? "Prueba con otro estatus, tipo de persona o término de búsqueda."
                : "Registra al primer contribuyente para comenzar a integrar su expediente fiscal."}
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-2">
            {hasActiveFilters && (
              <button type="button" onClick={handleClear} className={BTN_SECONDARY}>
                Limpiar filtros
              </button>
            )}
            {!hasActiveFilters && canManageClients && (
              <Link to="/clientes/nuevo" className={BTN_PRIMARY}>
                <Plus size={16} />
                Registrar contribuyente
              </Link>
            )}
          </div>
        </div>
      )}

      {!clientsQuery.isError && (isInitialLoading || items.length > 0) && (
        <section aria-label="Listado de contribuyentes" aria-busy={clientsQuery.isFetching}>
          <ClientsTable items={items} loading={isInitialLoading} />
          {!isInitialLoading && total > 0 && (
            <div className="card mt-2">
              <Pagination
                page={filters.page}
                total={total}
                perPage={perPage}
                onPageChange={handlePageChange}
              />
            </div>
          )}
        </section>
      )}

      <p className="flex items-start gap-2 rounded-xl bg-navy-900/[0.04] px-4 py-3 text-[11px] leading-relaxed text-navy-800">
        <ShieldCheck size={15} className="mt-0.5 shrink-0" />
        El Contador solo visualiza los clientes que tiene asignados o con permiso de atención
        vigente. El alta de contribuyentes está reservada al Socio Director y al Administrador.
      </p>
    </div>
  );
}
