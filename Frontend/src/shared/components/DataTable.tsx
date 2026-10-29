import type { ReactNode } from "react";

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  getRowKey: (row: T) => string | number;
  isLoading?: boolean;
  dimmed?: boolean; // true mientras se recarga con datos viejos en pantalla
  emptyMessage?: string;
}

export function DataTable<T>({
  columns, rows, getRowKey, isLoading, dimmed, emptyMessage = "Sin resultados",
}: Props<T>) {
  return (
    <div className="overflow-x-auto">
      <table className={`w-full text-left text-sm transition-opacity ${dimmed ? "opacity-60" : ""}`}>
        <thead>
          <tr className="border-b border-line text-[11px] uppercase tracking-wider text-muted">
            {columns.map((c) => (
              <th key={c.header} scope="col" className="px-4 py-3 font-semibold">{c.header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {isLoading ? (
            <tr><td colSpan={columns.length} className="px-4 py-10 text-center text-muted">Cargando…</td></tr>
          ) : rows.length === 0 ? (
            <tr><td colSpan={columns.length} className="px-4 py-10 text-center text-muted">{emptyMessage}</td></tr>
          ) : (
            rows.map((row) => (
              <tr key={getRowKey(row)} className="border-b border-line last:border-0 hover:bg-app">
                {columns.map((c) => (
                  <td key={c.header} className="px-4 py-3">{c.cell(row)}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}