import type { ReportData } from "../types";

export const REPORT_CSV_HEADERS: Record<string, string> = {
  seccion: "Sección",
  concepto: "Concepto",
  horas: "Horas",
  minutos: "Minutos",
  porcentaje: "Porcentaje",
  detalle: "Detalle",
};

export type ReportCsvRow = Record<string, string | number>;

export function buildReportCsvRows(data: ReportData): ReportCsvRow[] {
  const rows: ReportCsvRow[] = [];
  const base = { porcentaje: "", detalle: "" };

  rows.push(
    {
      seccion: "Resumen",
      concepto: "Horas registradas",
      horas: data.tarjetas.horas_totales.horas,
      minutos: data.tarjetas.horas_totales.minutos,
      ...base,
    },
    {
      seccion: "Resumen",
      concepto: "Tareas activas",
      horas: "",
      minutos: data.tarjetas.tareas_activas,
      ...base,
    },
    {
      seccion: "Resumen",
      concepto: "Tareas vencidas",
      horas: "",
      minutos: data.tarjetas.tareas_vencidas,
      ...base,
    },
    {
      seccion: "Resumen",
      concepto: "Tareas completadas",
      horas: "",
      minutos: data.tareas_completadas,
      ...base,
    },
  );

  if (data.tarjetas.costo_estimado?.disponible) {
    rows.push({
      seccion: "Resumen",
      concepto: "Costo estimado",
      horas: "",
      minutos: "",
      porcentaje: "",
      detalle: `${data.tarjetas.costo_estimado.monto ?? 0} MXN`,
    });
  }

  for (const row of data.tiempo_por_empleado ?? []) {
    rows.push({
      seccion: "Horas por colaborador",
      concepto: row.nombre,
      horas: row.horas,
      minutos: row.minutos,
      porcentaje: "",
      detalle: "",
    });
  }

  for (const row of data.tiempo_por_cliente ?? []) {
    rows.push({
      seccion: "Horas por cliente",
      concepto: row.nombre,
      horas: row.horas,
      minutos: row.minutos,
      porcentaje: "",
      detalle: "",
    });
  }

  for (const row of data.distribucion_por_categoria ?? []) {
    rows.push({
      seccion: "Distribución por categoría",
      concepto: row.nombre,
      horas: row.horas,
      minutos: row.minutos,
      porcentaje: row.porcentaje,
      detalle: "",
    });
  }

  const estados = data.estado_tareas;
  const estadoRows: Array<[string, number]> = [
    ["Por hacer", estados.POR_HACER ?? 0],
    ["En progreso", estados.EN_PROGRESO ?? 0],
    ["En revisión", estados.EN_REVISION ?? 0],
    ["Completado", estados.COMPLETADO ?? 0],
  ];

  for (const [label, value] of estadoRows) {
    rows.push({
      seccion: "Estado de tareas",
      concepto: label,
      horas: "",
      minutos: value,
      porcentaje: "",
      detalle: "",
    });
  }

  return rows;
}

export function reportFileName(data: ReportData): string {
  return `reporte-ejecutivo-${data.periodo.desde}-a-${data.periodo.hasta}.csv`;
}
