import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { CalendarDays, ChevronLeft, ChevronRight, Clock3 } from "lucide-react";
import { api } from "@/shared/api/client";
import { useAuthStore } from "@/shared/auth/authStore";
import { ROLES } from "@/shared/constants/roles";
import {
  BTN_SECONDARY,
  ESTADO_BADGE,
  ESTADO_LABELS,
  PRIORIDAD_BADGE,
  PRIORIDAD_LABELS,
  SEMAFORO_BADGE,
  SEMAFORO_LABELS,
} from "@/shared/constants/constants";
import {
  Badge,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
} from "@/shared/components/components";
import { formatDate, getErrorMessage, monthBounds, toISO, todayISO } from "@/shared/utils/utils";

const MONTH_NAMES = [
  "Enero",
  "Febrero",
  "Marzo",
  "Abril",
  "Mayo",
  "Junio",
  "Julio",
  "Agosto",
  "Septiembre",
  "Octubre",
  "Noviembre",
  "Diciembre",
];

const WEEKDAYS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

interface Option {
  id: number;
  nombre_completo: string;
}

interface CalendarEvent {
  id: number;
  tipo: string;
  titulo: string;
  fecha: string;
  hora: string | null;
  cliente_id: number;
  cliente_nombre: string | null;
  asignado_id: number | null;
  asignado_nombre: string | null;
  estado: string | null;
  prioridad: string | null;
  semaforo: string | null;
}

interface CalendarData {
  desde: string;
  hasta: string;
  eventos: CalendarEvent[];
  total: number;
  por_dia: Record<string, number>;
  mensaje: string | null;
}

interface CalendarCell {
  date: string | null;
  day: number | null;
  inMonth: boolean;
}

function anchorFromISO(iso: string): Date {
  const [year, month] = iso.split("-").map(Number);
  return new Date(year, (month ?? 1) - 1, 1);
}

function shiftMonth(date: Date, delta: number): Date {
  return new Date(date.getFullYear(), date.getMonth() + delta, 1);
}

function buildCells(anchor: Date): CalendarCell[] {
  const year = anchor.getFullYear();
  const month = anchor.getMonth();
  const first = new Date(year, month, 1);
  const offset = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = Math.ceil((offset + daysInMonth) / 7) * 7;

  return Array.from({ length: totalCells }, (_, index) => {
    const dayNumber = index - offset + 1;
    if (dayNumber < 1 || dayNumber > daysInMonth) {
      return { date: null, day: null, inMonth: false };
    }
    const date = toISO(new Date(year, month, dayNumber));
    return { date, day: dayNumber, inMonth: true };
  });
}

async function fetchOptions<T>(url: string) {
  const res = await api.get<{ data: T[] }>(url);
  return res.data.data ?? [];
}

export function CalendarPage() {
  const user = useAuthStore((state) => state.user);
  const today = todayISO();
  const [anchor, setAnchor] = useState(() => anchorFromISO(today));
  const [selectedDay, setSelectedDay] = useState(today);
  const [cliente, setCliente] = useState("");
  const [colaborador, setColaborador] = useState("");

  const canFilterTeam = user?.rol !== ROLES.CONTADOR;
  const bounds = monthBounds(toISO(anchor));

  const clientsQuery = useQuery({
    queryKey: ["clients", "options", "calendar"],
    queryFn: () => fetchOptions<Option>("/clients/options"),
    enabled: canFilterTeam,
    staleTime: 60_000,
  });

  const usersQuery = useQuery({
    queryKey: ["users", "options", "calendar"],
    queryFn: () => fetchOptions<Option>("/users/options"),
    enabled: canFilterTeam,
    staleTime: 60_000,
  });

  const query = useQuery({
    queryKey: ["calendar", bounds.desde, bounds.hasta, cliente, colaborador],
    queryFn: async () => {
      const res = await api.get<{ data: CalendarData }>("/calendar", {
        params: {
          fecha_desde: bounds.desde,
          fecha_hasta: bounds.hasta,
          cliente: cliente ? Number(cliente) : undefined,
          colaborador: colaborador ? Number(colaborador) : undefined,
        },
      });
      return res.data.data;
    },
    staleTime: 20_000,
  });

  const cells = useMemo(() => buildCells(anchor), [anchor]);
  const data = query.data;
  const eventsByDay = useMemo(() => {
    const map = new Map<string, CalendarEvent[]>();
    for (const event of data?.eventos ?? []) {
      const key = event.fecha.slice(0, 10);
      const list = map.get(key) ?? [];
      list.push(event);
      map.set(key, list);
    }
    return map;
  }, [data]);

  const selectedEvents = eventsByDay.get(selectedDay) ?? [];

  const goToMonth = (delta: number) => {
    const next = shiftMonth(anchor, delta);
    setAnchor(next);
    const year = next.getFullYear();
    const month = next.getMonth();
    const firstOfMonth = toISO(new Date(year, month, 1));
    setSelectedDay(today.startsWith(`${year}-${String(month + 1).padStart(2, "0")}`) ? today : firstOfMonth);
  };

  const goToday = () => {
    setAnchor(anchorFromISO(today));
    setSelectedDay(today);
  };

  return (
    <div className="mx-auto flex w-full max-w-[1440px] flex-col gap-4">
      <PageHeader
        eyebrow="Módulo 10 · Calendario de vencimientos"
        title="Calendario"
        description="Vencimientos de tareas por día. El alcance depende de tu rol."
        actions={
          <div className="flex items-center gap-2">
            <button type="button" className={BTN_SECONDARY} onClick={() => goToMonth(-1)} aria-label="Mes anterior">
              <ChevronLeft size={16} />
            </button>
            <button type="button" className={BTN_SECONDARY} onClick={goToday}>
              Hoy
            </button>
            <button type="button" className={BTN_SECONDARY} onClick={() => goToMonth(1)} aria-label="Mes siguiente">
              <ChevronRight size={16} />
            </button>
          </div>
        }
      />

      <section className="card flex flex-wrap items-end gap-3 p-3">
        <span className="rounded-lg bg-app px-3 py-2 font-display text-sm font-bold text-ink">
          {MONTH_NAMES[anchor.getMonth()]} {anchor.getFullYear()}
        </span>
        {canFilterTeam && (
          <>
            <label className="flex min-w-52 flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Cliente</span>
              <select
                value={cliente}
                onChange={(event) => setCliente(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              >
                <option value="">Todos los clientes</option>
                {(clientsQuery.data ?? []).map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.nombre_completo}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex min-w-52 flex-col gap-1">
              <span className="text-[10px] font-semibold uppercase tracking-wide text-muted">Colaborador</span>
              <select
                value={colaborador}
                onChange={(event) => setColaborador(event.target.value)}
                className="rounded-lg border border-line bg-surface px-3 py-2 text-sm text-ink"
              >
                <option value="">Todo el equipo</option>
                {(usersQuery.data ?? []).map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.nombre_completo}
                  </option>
                ))}
              </select>
            </label>
          </>
        )}
        <span className="ml-auto pb-2 text-xs text-muted">{data?.total ?? 0} vencimientos en el mes</span>
      </section>

      {query.isLoading && <LoadingState label="Cargando calendario…" />}
      {query.isError && <ErrorState message={getErrorMessage(query.error)} />}

      {!query.isLoading && !query.isError && (
        <section className="card overflow-hidden">
          <div className="grid grid-cols-7 border-b border-line bg-app/60">
            {WEEKDAYS.map((day) => (
              <div key={day} className="px-2 py-2 text-center text-[10px] font-semibold uppercase tracking-wide text-muted">
                {day}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7">
            {cells.map((cell, index) => {
              if (!cell.date || !cell.day) {
                return <div key={`empty-${index}`} className="min-h-24 border-b border-r border-line bg-app/20" />;
              }
              const count = data?.por_dia?.[cell.date] ?? 0;
              const isToday = cell.date === today;
              const isSelected = cell.date === selectedDay;
              const dayEvents = eventsByDay.get(cell.date) ?? [];
              return (
                <button
                  key={cell.date}
                  type="button"
                  onClick={() => setSelectedDay(cell.date as string)}
                  className={`min-h-24 border-b border-r border-line p-1.5 text-left align-top transition hover:bg-app/50 ${
                    isSelected ? "bg-gold-300/20 ring-1 ring-inset ring-gold-500/50" : ""
                  }`}
                >
                  <span
                    className={`inline-grid size-6 place-items-center rounded-full text-[11px] font-semibold ${
                      isToday ? "bg-navy-900 text-white" : "text-muted"
                    }`}
                  >
                    {cell.day}
                  </span>
                  <div className="mt-1 flex flex-col gap-0.5">
                    {dayEvents.slice(0, 2).map((event) => (
                      <span
                        key={event.id}
                        className="truncate rounded bg-navy-900/5 px-1 py-0.5 text-[9.5px] font-medium text-navy-900"
                        title={event.titulo}
                      >
                        {event.titulo}
                      </span>
                    ))}
                    {count > 2 && (
                      <span className="px-1 text-[9.5px] font-semibold text-muted">+{count - 2} más</span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </section>
      )}

      <section className="card p-4">
        <header className="flex flex-wrap items-center gap-2">
          <span className="grid size-8 place-items-center rounded-lg bg-app text-navy-800">
            <CalendarDays size={17} />
          </span>
          <h2 className="text-sm font-semibold text-ink">{formatDate(selectedDay)}</h2>
          <span className="ml-auto text-xs text-muted">{selectedEvents.length} vencimientos</span>
        </header>

        {selectedEvents.length === 0 ? (
          <EmptyState
            title="Sin vencimientos este día"
            description="Selecciona otro día del calendario."
            icon={<CalendarDays size={22} />}
          />
        ) : (
          <ul className="mt-4 flex flex-col gap-2">
            {selectedEvents.map((event) => (
              <li key={`${event.tipo}-${event.id}`}>
                <Link
                  to={`/tareas/${event.id}`}
                  className="flex flex-wrap items-center gap-2 rounded-xl border border-line bg-app/30 px-3 py-2 transition hover:border-navy-900/20 hover:bg-app/60"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-ink">{event.titulo}</p>
                    <p className="text-xs text-muted">
                      {event.cliente_nombre ?? "Sin cliente"}
                      {event.asignado_nombre ? ` · ${event.asignado_nombre}` : ""}
                    </p>
                  </div>
                  {event.hora && (
                    <span className="inline-flex items-center gap-1 text-xs text-muted">
                      <Clock3 size={13} /> {event.hora}
                    </span>
                  )}
                  {event.estado && (
                    <Badge className={ESTADO_BADGE[event.estado]}>
                      {ESTADO_LABELS[event.estado] ?? event.estado}
                    </Badge>
                  )}
                  {event.prioridad && (
                    <Badge className={PRIORIDAD_BADGE[event.prioridad]}>
                      {PRIORIDAD_LABELS[event.prioridad] ?? event.prioridad}
                    </Badge>
                  )}
                  {event.semaforo && (
                    <Badge className={SEMAFORO_BADGE[event.semaforo]}>
                      {SEMAFORO_LABELS[event.semaforo] ?? event.semaforo}
                    </Badge>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
