import { api } from "@/shared/api/client";
import type { ReportData, ReportFilters } from "../types";

export async function fetchReportSummary(filters: ReportFilters): Promise<ReportData> {
  const res = await api.get<{ data: ReportData }>("/reports/summary", {
    params: filters,
  });
  return res.data.data;
}

export async function fetchReportOptions<T>(url: string): Promise<T[]> {
  const res = await api.get<{ data: T[] }>(url);
  return res.data.data ?? [];
}
