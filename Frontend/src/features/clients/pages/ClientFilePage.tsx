import { useState } from "react";
import { Link, useLocation, useParams } from "react-router-dom";
import {
  AlertTriangle,
  Building2,
  CheckCircle2,
  ClipboardList,
  FileText,
  Info,
  ListChecks,
  RefreshCw,
  ShieldCheck,
  UsersRound,
  X,
} from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { isDetailUnavailable } from "../api/clientsApi";
import { useClientDetail } from "../api/useClients";
import { BTN_SECONDARY, BTN_PRIMARY } from "../constants";
import type { ClientFileLocationState, ClienteExpediente } from "../types";
import { FileHeader } from "../components/file/FileHeader";
import { FileKpis } from "../components/file/FileKpis";
import { FileTabs, type FileTab, type FileTabId } from "../components/file/FileTabs";
import { GeneralPanel } from "../components/file/GeneralPanel";
import { FiscalPanel } from "../components/file/FiscalPanel";
import { ContactsPanel } from "../components/file/ContactsPanel";
import { LinkedPanel } from "../components/file/LinkedPanel";

function PageSkeleton() {
  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4" aria-busy="true">
      <div className="card animate-pulse p-5">
        <div className="flex items-center gap-4">
          <div className="size-20 rounded-xl bg-line" />
          <div className="flex-1 space-y-3">
            <div className="h-3 w-32 rounded bg-line" />
            <div className="h-6 w-72 rounded bg-line" />
            <div className="h-3 w-48 rounded bg-line" />
          </div>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <div key={index} className="card h-20 animate-pulse" />
        ))}
      </div>
      <div className="card h-14 animate-pulse" />
      <div className="grid gap-3 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <div key={index} className="card h-64 animate-pulse" />
        ))}
      </div>
    </div>
  );
}

export function ClientFilePage() {
  const { id } = useParams<{ id: string }>();
  const location = useLocation();
  const state = location.state as ClientFileLocationState | null;

  const clientId = Number(id);
  const validId = Number.isInteger(clientId) && clientId > 0;

  const detailQuery = useClientDetail(clientId, validId);
  const [tab, setTab] = useState<FileTabId>("general");
  const [showWelcome, setShowWelcome] = useState(Boolean(state?.recienCreado));

  const expediente: ClienteExpediente | undefined = detailQuery.data
    ? { ...detailQuery.data, ...state?.cliente }
    : state?.cliente;

  const hasFullDetail = Boolean(detailQuery.data);

  if (!validId) {
    return (
      <div className="card mx-auto flex max-w-lg flex-col items-center gap-3 px-6 py-12 text-center">
        <span className="grid size-12 place-items-center rounded-full bg-red-50 text-danger">
          <AlertTriangle size={22} />
        </span>
        <h1 className="font-display text-lg font-bold text-ink">Expediente no válido</h1>
        <p className="text-sm text-muted">El identificador del cliente no es correcto.</p>
        <Link to="/clientes" className={BTN_SECONDARY}>
          Volver a la cartera
        </Link>
      </div>
    );
  }

  if (detailQuery.isLoading && !expediente) return <PageSkeleton />;

  if (!expediente) {
    return (
      <div className="card mx-auto flex max-w-xl flex-col items-center gap-3 px-6 py-12 text-center">
        <span className="grid size-12 place-items-center rounded-full bg-app text-navy-800">
          <FileText size={22} />
        </span>
        <h1 className="font-display text-lg font-bold text-ink">
          No pudimos abrir este expediente
        </h1>
        <p className="max-w-md text-sm text-muted">
          {isDetailUnavailable(detailQuery.error)
            ? "La consulta del expediente fiscal aún no está disponible. Abre el cliente desde la cartera para ver el resumen registrado."
            : detailQuery.error instanceof ApiError
              ? detailQuery.error.message
              : "Ocurrió un error inesperado al consultar el expediente."}
        </p>
        <div className="flex flex-wrap justify-center gap-2">
          <Link to="/clientes" className={BTN_PRIMARY}>
            Ir a la cartera
          </Link>
          <button type="button" onClick={() => detailQuery.refetch()} className={BTN_SECONDARY}>
            <RefreshCw size={15} />
            Reintentar
          </button>
        </div>
      </div>
    );
  }

  const tabs: FileTab[] = [
    { id: "general", label: "Datos generales", icon: Building2 },
    { id: "fiscal", label: "Situación fiscal", icon: ShieldCheck },
    { id: "contactos", label: "Contactos", icon: UsersRound, badge: expediente.contactos?.length },
    { id: "obligaciones", label: "Obligaciones", icon: ClipboardList },
    { id: "tareas", label: "Tareas", icon: ListChecks, badge: expediente.tareas_activas },
    { id: "minutas", label: "Minutas y acuerdos", icon: FileText },
  ];

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <nav aria-label="Ruta de navegación" className="flex flex-wrap items-center gap-1.5 text-[11px] text-muted">
        <Link to="/clientes" className="transition hover:text-navy-800">
          Gestión
        </Link>
        <span aria-hidden="true">/</span>
        <Link to="/clientes" className="transition hover:text-navy-800">
          Cartera de clientes
        </Link>
        <span aria-hidden="true">/</span>
        <span className="font-semibold text-navy-800">Expediente</span>
      </nav>

      {showWelcome && (
        <div
          role="status"
          className="flex items-start justify-between gap-3 rounded-lg bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-800"
        >
          <span className="flex items-start gap-2">
            <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
            Contribuyente registrado correctamente. Su expediente fiscal quedó integrado en la
            cartera.
          </span>
          <button
            type="button"
            onClick={() => setShowWelcome(false)}
            aria-label="Cerrar mensaje"
            className="grid size-6 shrink-0 place-items-center rounded transition hover:bg-emerald-100"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {!hasFullDetail && (
        <div className="flex items-start gap-2 rounded-lg bg-navy-900/[0.04] px-4 py-2.5 text-[11px] leading-relaxed text-navy-800">
          <Info size={15} className="mt-0.5 shrink-0" />
          Estás viendo el resumen registrado en la cartera. Los datos de domicilio, regímenes y
          contactos se completarán al habilitarse la consulta del expediente fiscal.
        </div>
      )}

      <FileHeader cliente={expediente} />
      <FileKpis cliente={expediente} />

      <FileTabs tabs={tabs} active={tab} onChange={setTab} />

      <div role="tabpanel">
        {tab === "general" && <GeneralPanel cliente={expediente} />}
        {tab === "fiscal" && <FiscalPanel cliente={expediente} />}
        {tab === "contactos" && <ContactsPanel cliente={expediente} />}
        {tab === "obligaciones" && (
          <LinkedPanel
            icon={ClipboardList}
            title="Obligaciones periódicas del contribuyente"
            description="Las obligaciones se generan a partir de los regímenes fiscales y del esquema de nómina registrado en el expediente."
            to="/obligaciones"
            actionLabel="Ir a obligaciones periódicas"
          />
        )}
        {tab === "tareas" && (
          <LinkedPanel
            icon={ListChecks}
            title="Tareas del expediente"
            description="Consulta y da seguimiento a las tareas asignadas al equipo contable para este contribuyente."
            to={`/tareas?cliente=${expediente.id}`}
            actionLabel="Ver tareas del cliente"
            count={expediente.tareas_activas}
            countLabel="tareas activas registradas"
          />
        )}
        {tab === "minutas" && (
          <LinkedPanel
            icon={FileText}
            title="Minutas y acuerdos"
            description="Documenta juntas, acuerdos y decisiones relevantes del expediente fiscal."
            to="/minutas"
            actionLabel="Ir a minutas"
          />
        )}
      </div>
    </div>
  );
}
