import type JsPdf from "jspdf";
import { formatDate, formatDateTime, formatMoney, formatMinutes } from "@/shared/utils/utils";
import type { ReportData } from "../types";

/**
 * Genera el reporte ejecutivo en PDF (A4 vertical) con la identidad de la
 * empresa: banda azul marino, acentos dorados, logo y gráficas vectoriales
 * (dona de estados y barras comparativas). No depende de capturas de pantalla,
 * por lo que el documento siempre sale nítido.
 */

type RGB = [number, number, number];

const COLORS = {
  navy: [11, 20, 69] as RGB,
  navyDeep: [6, 11, 46] as RGB,
  navySoft: [27, 40, 102] as RGB,
  gold: [201, 162, 39] as RGB,
  goldBright: [245, 213, 71] as RGB,
  ink: [17, 24, 39] as RGB,
  muted: [107, 114, 128] as RGB,
  line: [226, 229, 239] as RGB,
  surface: [255, 255, 255] as RGB,
  app: [244, 245, 248] as RGB,
  onDark: [201, 207, 230] as RGB,
  danger: [200, 30, 30] as RGB,
};

const STATUS_ROWS = [
  { key: "POR_HACER", label: "Por hacer", color: [148, 163, 184] as RGB },
  { key: "EN_PROGRESO", label: "En progreso", color: [14, 165, 233] as RGB },
  { key: "EN_REVISION", label: "En revisión", color: [245, 158, 11] as RGB },
  { key: "COMPLETADO", label: "Completado", color: [16, 185, 129] as RGB },
] as const;

const PAGE = {
  width: 210,
  height: 297,
  margin: 14,
  contentWidth: 210 - 14 * 2,
  footerLine: 282,
  bottom: 275,
};

const LOGO_FILE = "logo-tellez-ponce.png";
const LOGO_RATIO = 762 / 558;
const MARK_FILE = "logo-tellez-ponce-mark.png";
const MARK_RATIO = 505 / 350;

interface ListRow {
  id: number | string;
  label: string;
  minutos: number;
  extra?: string;
}

/** Descarga el logo como data URL para incrustarlo en el PDF. */
async function loadImageDataUrl(file: string): Promise<string | null> {
  try {
    const base = import.meta.env.BASE_URL || "/";
    const res = await fetch(`${base}${file}`);
    if (!res.ok) return null;
    const blob = await res.blob();
    return await new Promise<string>((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    });
  } catch {
    return null;
  }
}

function percent(part: number, total: number): number {
  if (!total) return 0;
  return Math.round((part / total) * 100);
}

class ReportPdf {
  private readonly doc: JsPdf;
  private logo: string | null = null;
  private mark: string | null = null;
  private data!: ReportData;
  private y = 0;

  constructor(doc: JsPdf) {
    this.doc = doc;
  }

  async render(data: ReportData): Promise<void> {
    this.data = data;
    [this.logo, this.mark] = await Promise.all([
      loadImageDataUrl(LOGO_FILE),
      loadImageDataUrl(MARK_FILE),
    ]);

    this.drawCoverHeader();
    this.drawPeriodStrip();

    this.y = this.y + 4;
    this.drawKpis();
    this.drawComparison();
    this.drawTaskStatus();
    this.drawListCard("Horas por colaborador", this.teamRows());
    this.drawListCard("Horas por cliente", this.clientRows());
    this.drawListCard("Distribución por categoría", this.categoryRows(), true);
    this.drawNotes();
    this.drawFooters();
  }

  // ---------------------------------------------------------------------------
  // Estructura de páginas
  // ---------------------------------------------------------------------------

  private drawCoverHeader(): void {
    const doc = this.doc;
    const { width, margin } = PAGE;

    doc.setFillColor(...COLORS.navy);
    doc.rect(0, 0, width, 44, "F");

    // Halo decorativo en la esquina superior derecha.
    doc.setFillColor(...COLORS.navySoft);
    doc.circle(width + 6, -8, 40, "F");
    doc.setFillColor(...COLORS.navy);
    doc.circle(width + 14, -2, 32, "F");

    if (this.logo) {
      const h = 23;
      doc.addImage(this.logo, "PNG", margin, 10, h * LOGO_RATIO, h);
    }

    const textX = margin + 37;
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.surface);
    doc.setFontSize(19);
    doc.text("REPORTE EJECUTIVO", textX, 21);

    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.onDark);
    doc.setFontSize(8.5);
    doc.text("Horas, carga de trabajo y estado de tareas", textX, 27);

    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.goldBright);
    doc.setFontSize(7.2);
    doc.text("TÉLLEZ PONCE & ASOCIADOS S.C.", textX, 34);

    const right = PAGE.width - margin;
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.surface);
    doc.setFontSize(8.4);
    doc.text(this.data.periodo.etiqueta.toUpperCase(), right, 17, { align: "right" });

    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.onDark);
    doc.setFontSize(7.4);
    doc.text(
      `${formatDate(this.data.periodo.desde)} — ${formatDate(this.data.periodo.hasta)}`,
      right,
      22.5,
      { align: "right" },
    );
    doc.text(`Generado: ${formatDateTime(this.data.generado_en)}`, right, 28, { align: "right" });
    doc.text("Documento confidencial", right, 33.5, { align: "right" });

    // Filo dorado de la banda.
    doc.setFillColor(...COLORS.gold);
    doc.rect(0, 44, width, 1.6, "F");
    doc.setFillColor(...COLORS.goldBright);
    doc.rect(0, 44, width, 0.5, "F");
  }

  private drawPeriodStrip(): void {
    const doc = this.doc;
    const { margin } = PAGE;
    this.y = 49;

    const pills = [`Periodo: ${this.data.periodo.etiqueta}`];
    if (this.data.filtros?.cliente_nombre) {
      pills.push(`Cliente: ${this.data.filtros.cliente_nombre}`);
    }
    if (this.data.filtros?.colaborador_nombre) {
      pills.push(`Colaborador: ${this.data.filtros.colaborador_nombre}`);
    }

    let x = margin;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    for (const text of pills) {
      const w = doc.getTextWidth(text) + 5;
      if (x + w > PAGE.width - margin) break;
      doc.setFillColor(...COLORS.app);
      doc.setDrawColor(...COLORS.line);
      doc.setLineWidth(0.2);
      doc.roundedRect(x, this.y, w, 6.2, 1.6, 1.6, "FD");
      doc.setTextColor(...COLORS.muted);
      doc.text(text, x + 2.5, this.y + 4.1);
      x += w + 2;
    }
    this.y += 6.2;
  }

  private drawFooters(): void {
    const doc = this.doc;
    const total = doc.getNumberOfPages();
    for (let page = 1; page <= total; page += 1) {
      doc.setPage(page);
      doc.setDrawColor(...COLORS.line);
      doc.setLineWidth(0.3);
      doc.line(PAGE.margin, PAGE.footerLine, PAGE.width - PAGE.margin, PAGE.footerLine);
      doc.setFillColor(...COLORS.gold);
      doc.rect(PAGE.margin, PAGE.footerLine - 0.6, 12, 0.6, "F");

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.8);
      doc.setTextColor(...COLORS.muted);
      doc.text(
        "Téllez Ponce & Asociados S.C. · Información fiduciaria de uso interno.",
        PAGE.margin,
        PAGE.footerLine + 4.2,
      );
      doc.setFont("helvetica", "bold");
      doc.setTextColor(...COLORS.navy);
      doc.text(`Página ${page} de ${total}`, PAGE.width - PAGE.margin, PAGE.footerLine + 4.2, {
        align: "right",
      });
    }
  }

  private newPage(): void {
    const doc = this.doc;
    doc.addPage();

    doc.setFillColor(...COLORS.navy);
    doc.rect(0, 0, PAGE.width, 17, "F");
    if (this.mark) {
      const h = 10;
      doc.addImage(this.mark, "PNG", PAGE.margin, 3.5, h * MARK_RATIO, h);
    }
    doc.setFont("helvetica", "bold");
    doc.setTextColor(...COLORS.surface);
    doc.setFontSize(8.4);
    doc.text("REPORTE EJECUTIVO", PAGE.margin + 18, 10.5);

    doc.setFont("helvetica", "normal");
    doc.setTextColor(...COLORS.onDark);
    doc.setFontSize(7);
    doc.text(
      `${formatDate(this.data.periodo.desde)} — ${formatDate(this.data.periodo.hasta)}`,
      PAGE.width - PAGE.margin,
      10.5,
      { align: "right" },
    );
    doc.setFillColor(...COLORS.gold);
    doc.rect(0, 17, PAGE.width, 0.9, "F");

    this.y = 23;
  }

  private ensureSpace(height: number): void {
    if (this.y + height > PAGE.bottom) this.newPage();
  }

  // ---------------------------------------------------------------------------
  // Utilidades de dibujo
  // ---------------------------------------------------------------------------

  private card(x: number, y: number, w: number, h: number): void {
    const doc = this.doc;
    doc.setFillColor(...COLORS.surface);
    doc.setDrawColor(...COLORS.line);
    doc.setLineWidth(0.3);
    doc.roundedRect(x, y, w, h, 2.6, 2.6, "FD");
  }

  private cardTitle(title: string, x: number, y: number, note?: string): void {
    const doc = this.doc;
    doc.setFillColor(...COLORS.gold);
    doc.roundedRect(x, y - 2.6, 1.3, 4.4, 0.6, 0.6, "F");

    doc.setFont("helvetica", "bold");
    doc.setFontSize(9.4);
    doc.setTextColor(...COLORS.ink);
    doc.text(title, x + 4, y + 0.6);

    if (note) {
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(...COLORS.muted);
      doc.text(note, x + PAGE.contentWidth - 10, y + 0.6, { align: "right" });
    }
  }

  private fitFontSize(text: string, maxWidth: number, size: number, min = 5): number {
    const doc = this.doc;
    let current = size;
    doc.setFontSize(current);
    while (current > min && doc.getTextWidth(text) > maxWidth) {
      current -= 0.15;
      doc.setFontSize(current);
    }
    return current;
  }

  private emptyNote(text: string, x: number, y: number, w: number): void {
    const doc = this.doc;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7.6);
    doc.setTextColor(...COLORS.muted);
    doc.text(text, x + w / 2, y, { align: "center" });
  }

  /** Dibuja un polígono relleno a partir de puntos absolutos en mm. */
  private polygon(points: Array<[number, number]>, color: RGB): void {
    if (points.length < 3) return;
    const doc = this.doc;
    doc.setFillColor(...color);
    doc.setDrawColor(...color);
    doc.setLineWidth(0.05);
    const [startX, startY] = points[0];
    const deltas = points
      .slice(1)
      .map(([x, y], index) => [x - points[index][0], y - points[index][1]]);
    doc.lines(deltas, startX, startY, [1, 1], "F", true);
  }

  /** Dona de estados: sectores vectoriales + hueco blanco. */
  private donut(
    cx: number,
    cy: number,
    radius: number,
    slices: Array<{ value: number; color: RGB }>,
  ): void {
    const doc = this.doc;
    const total = slices.reduce((acc, slice) => acc + Math.max(0, slice.value), 0);

    if (total === 0) {
      doc.setDrawColor(...COLORS.line);
      doc.setLineWidth(8);
      doc.circle(cx, cy, radius - 4, "S");
      return;
    }

    let angle = -Math.PI / 2;
    for (const slice of slices) {
      const value = Math.max(0, slice.value);
      if (value === 0) continue;
      const sweep = (value / total) * Math.PI * 2;
      const steps = Math.max(2, Math.ceil(sweep / 0.05));
      const points: Array<[number, number]> = [[cx, cy]];
      for (let step = 0; step <= steps; step += 1) {
        const current = angle + (sweep * step) / steps;
        points.push([cx + Math.cos(current) * radius, cy + Math.sin(current) * radius]);
      }
      this.polygon(points, slice.color);
      angle += sweep;
    }

    // Hueco central.
    doc.setFillColor(...COLORS.surface);
    doc.circle(cx, cy, radius * 0.6, "F");
  }

  private bar(
    x: number,
    y: number,
    w: number,
    h: number,
    ratio: number,
    color: RGB,
    accent = true,
  ): void {
    const doc = this.doc;
    doc.setFillColor(...COLORS.app);
    doc.roundedRect(x, y, w, h, h / 2, h / 2, "F");

    const width = Math.max(2, w * Math.min(1, Math.max(0, ratio)));
    doc.setFillColor(...color);
    doc.roundedRect(x, y, width, h, h / 2, h / 2, "F");

    if (accent && width > 2.4) {
      doc.setFillColor(...COLORS.goldBright);
      doc.roundedRect(x + width - 1.6, y, 1.6, h, h / 2, h / 2, "F");
    }
  }

  // ---------------------------------------------------------------------------
  // Secciones del reporte
  // ---------------------------------------------------------------------------

  private drawKpis(): void {
    const doc = this.doc;
    const { tarjetas, tareas_completadas } = this.data;
    const costo = tarjetas.costo_estimado;
    const variation = tarjetas.horas_totales.variacion_porcentaje;

    const cards: Array<{ label: string; value: string; hint: string; tone?: RGB }> = [
      {
        label: "Horas registradas",
        value: `${tarjetas.horas_totales.horas.toFixed(1)} h`,
        hint:
          variation === null
            ? "Sin periodo anterior comparable"
            : `${variation > 0 ? "+" : ""}${variation}% vs. periodo anterior`,
      },
      {
        label: "Tareas activas",
        value: String(tarjetas.tareas_activas),
        hint: "Sin contar completadas",
      },
      {
        label: "Tareas vencidas",
        value: String(tarjetas.tareas_vencidas),
        hint: "Requieren atención",
        tone: tarjetas.tareas_vencidas > 0 ? COLORS.danger : undefined,
      },
      {
        label: "Completadas",
        value: String(tareas_completadas),
        hint: "Cerradas dentro del periodo",
      },
      {
        label: "Costo estimado",
        value: costo?.disponible ? formatMoney(costo.monto) : "No disponible",
        hint: costo?.disponible ? "Horas × tarifa configurada" : costo?.mensaje || "Sin tarifa configurada",
        tone: costo && !costo.disponible ? COLORS.gold : undefined,
      },
    ];

    const gap = 3.2;
    const width = (PAGE.contentWidth - gap * (cards.length - 1)) / cards.length;
    const height = 25;

    this.ensureSpace(height + 4);

    cards.forEach((card, index) => {
      const x = PAGE.margin + index * (width + gap);
      const y = this.y;
      this.card(x, y, width, height);

      doc.setFillColor(...(card.tone ?? COLORS.gold));
      doc.roundedRect(x, y, width, 1.6, 0.8, 0.8, "F");

      doc.setFont("helvetica", "normal");
      doc.setTextColor(...COLORS.muted);
      this.fitFontSize(card.label, width - 7, 6.8, 5.4);
      doc.text(card.label, x + 3.5, y + 8);

      doc.setFont("helvetica", "bold");
      doc.setTextColor(...COLORS.navy);
      this.fitFontSize(card.value, width - 7, 13.5, 8.5);
      doc.text(card.value, x + 3.5, y + 16.2);

      doc.setFont("helvetica", "normal");
      doc.setTextColor(...COLORS.muted);
      this.fitFontSize(card.hint, width - 7, 5.6, 4.6);
      doc.text(card.hint, x + 3.5, y + 21.4);
    });

    this.y += height + 5;
  }

  private drawComparison(): void {
    const doc = this.doc;
    const { horas_totales } = this.data.tarjetas;
    const anterior = horas_totales.horas_periodo_anterior ?? 0;
    const actual = horas_totales.horas;
    const height = 47;

    this.ensureSpace(height + 4);

    const x = PAGE.margin;
    const y = this.y;
    const w = PAGE.contentWidth;
    this.card(x, y, w, height);
    this.cardTitle("Comparativo de horas", x + 5, y + 9);

    const baseY = y + 36;
    const max = Math.max(anterior, actual, 1);
    const barW = 15;
    const barMaxH = 20;

    const bars: Array<{ value: number; color: RGB; label: string; x: number }> = [
      { value: anterior, color: COLORS.navySoft, label: "Periodo anterior", x: x + 14 },
      { value: actual, color: COLORS.gold, label: "Periodo actual", x: x + 37 },
    ];

    bars.forEach((bar) => {
      const barH = Math.max(1.5, (bar.value / max) * barMaxH);
      doc.setFillColor(...COLORS.app);
      doc.roundedRect(bar.x, baseY - barMaxH, barW, barMaxH, 1.4, 1.4, "F");
      doc.setFillColor(...bar.color);
      doc.roundedRect(bar.x, baseY - barH, barW, barH, 1.4, 1.4, "F");

      doc.setFont("helvetica", "bold");
      doc.setFontSize(7.6);
      doc.setTextColor(...COLORS.navy);
      doc.text(`${bar.value.toFixed(1)} h`, bar.x + barW / 2, baseY - barMaxH - 2, {
        align: "center",
      });

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.4);
      doc.setTextColor(...COLORS.muted);
      doc.text(bar.label, bar.x + barW / 2, baseY + 3.6, { align: "center" });
    });

    doc.setDrawColor(...COLORS.line);
    doc.setLineWidth(0.4);
    doc.line(x + 12, baseY + 0.8, x + 58, baseY + 0.8);

    // Bloque derecho con la variación.
    doc.setFillColor(...COLORS.app);
    doc.roundedRect(x + 68, y + 13, w - 76, height - 18, 2, 2, "F");

    const variation = horas_totales.variacion_porcentaje;
    doc.setFont("helvetica", "bold");
    doc.setFontSize(18);
    doc.setTextColor(...(variation !== null && variation < 0 ? COLORS.danger : COLORS.navy));
    doc.text(variation === null ? "—" : `${variation > 0 ? "+" : ""}${variation}%`, x + 76, y + 26);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    doc.setTextColor(...COLORS.muted);
    doc.text("Variación contra el periodo anterior", x + 76, y + 31);

    doc.setFont("helvetica", "bold");
    doc.setFontSize(8);
    doc.setTextColor(...COLORS.ink);
    const description =
      variation === null
        ? "Aún no hay un periodo comparable para calcular la variación."
        : variation < 0
          ? "El volumen de horas disminuyó respecto al periodo anterior."
          : "El volumen de horas creció respecto al periodo anterior.";
    doc.text(doc.splitTextToSize(description, w - 82), x + 76, y + 36.5);

    doc.setFont("helvetica", "normal");
    doc.setFontSize(6.6);
    doc.setTextColor(...COLORS.muted);
    doc.text(
      `Horas del periodo anterior: ${anterior.toFixed(1)} h · Actual: ${actual.toFixed(1)} h`,
      x + 76,
      y + 41.5,
    );

    this.y += height + 5;
  }

  private drawTaskStatus(): void {
    const doc = this.doc;
    const estado = this.data.estado_tareas;
    const total = estado.total ?? 0;
    const height = 63;

    this.ensureSpace(height + 4);

    const x = PAGE.margin;
    const y = this.y;
    const w = PAGE.contentWidth;

    this.card(x, y, w, height);
    this.cardTitle("Estado de las tareas", x + 5, y + 9, `${total} tareas en el periodo`);

    const cx = x + 32;
    const cy = y + 35;
    const radius = 18;

    this.donut(
      cx,
      cy,
      radius,
      STATUS_ROWS.map((row) => ({
        value: estado[row.key] ?? 0,
        color: row.color,
      })),
    );

    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(...COLORS.navy);
    doc.text(String(total), cx, cy + 1.4, { align: "center" });
    doc.setFont("helvetica", "normal");
    doc.setFontSize(5.8);
    doc.setTextColor(...COLORS.muted);
    doc.text("TAREAS", cx, cy + 5, { align: "center" });

    const columns = [
      { x: x + 60, top: y + 17 },
      { x: x + 125, top: y + 17 },
    ];

    STATUS_ROWS.forEach((row, index) => {
      const column = columns[Math.floor(index / 2)];
      const rowY = column.top + (index % 2) * 17;
      const value = estado[row.key] ?? 0;

      doc.setFillColor(...row.color);
      doc.circle(column.x + 1.6, rowY - 1.4, 1.5, "F");

      doc.setFont("helvetica", "normal");
      doc.setFontSize(7.4);
      doc.setTextColor(...COLORS.muted);
      doc.text(row.label, column.x + 5.5, rowY);

      doc.setFont("helvetica", "bold");
      doc.setFontSize(11);
      doc.setTextColor(...COLORS.ink);
      doc.text(String(value), column.x + 5.5, rowY + 5.2);

      doc.setFont("helvetica", "normal");
      doc.setFontSize(6.6);
      doc.setTextColor(...COLORS.muted);
      doc.text(`${percent(value, total)}% del total`, column.x + 15, rowY + 5.2);
    });

    if ((estado.vencidas ?? 0) > 0) {
      doc.setFillColor(253, 240, 240);
      doc.roundedRect(x + 5, y + height - 12, w - 10, 7.5, 1.4, 1.4, "F");
      doc.setFont("helvetica", "bold");
      doc.setFontSize(6.8);
      doc.setTextColor(...COLORS.danger);
      doc.text(
        `${estado.vencidas} tareas vencidas sin completar: requieren seguimiento del equipo.`,
        x + 8,
        y + height - 7,
      );
    }

    this.y += height + 5;
  }

  private drawListCard(title: string, rows: ListRow[], showPercent = false): void {
    const doc = this.doc;
    const rowHeight = 8;
    const headerHeight = 13;
    const x = PAGE.margin;
    const w = PAGE.contentWidth;
    const max = Math.max(1, ...rows.map((row) => row.minutos));

    if (rows.length === 0) {
      this.ensureSpace(headerHeight + 16);
      const y = this.y;
      this.card(x, y, w, headerHeight + 16);
      this.cardTitle(title, x + 5, y + 9);
      this.emptyNote("Sin horas registradas en el periodo.", x, y + 21, w);
      this.y += headerHeight + 20;
      return;
    }

    let index = 0;
    let continuation = false;

    while (index < rows.length) {
      this.ensureSpace(headerHeight + rowHeight + 3);
      const available = Math.floor((PAGE.bottom - this.y - headerHeight - 2) / rowHeight);
      const take = Math.max(1, Math.min(available, rows.length - index, 9));
      const height = headerHeight + take * rowHeight + 3;

      this.ensureSpace(height);
      const y = this.y;
      this.card(x, y, w, height);
      this.cardTitle(
        continuation ? `${title} (continuación)` : title,
        x + 5,
        y + 9,
        `${rows.length} conceptos · máx. ${formatMinutes(max)}`,
      );

      const labelX = x + 6;
      const labelW = 58;
      const barX = x + 70;
      const barW = w - 70 - 34;

      for (let i = 0; i < take; i += 1) {
        const row = rows[index + i];
        const rowY = y + headerHeight + i * rowHeight + 3.4;

        doc.setFont("helvetica", "normal");
        doc.setTextColor(...COLORS.ink);
        this.fitFontSize(row.label, labelW, 7.4, 6);
        doc.text(row.label, labelX, rowY + 2.4);

        this.bar(barX, rowY, barW, 3.4, row.minutos / max, COLORS.navy);

        doc.setFont("helvetica", "bold");
        doc.setFontSize(7.2);
        doc.setTextColor(...COLORS.navy);
        const valueText =
          showPercent && row.extra
            ? `${row.extra} · ${formatMinutes(row.minutos)}`
            : formatMinutes(row.minutos);
        doc.text(valueText, x + w - 6, rowY + 2.6, { align: "right" });
      }

      this.y += height + 4;
      index += take;
      continuation = true;
    }
  }

  /** Criterios y alcance del reporte al pie del documento. */
  private drawNotes(): void {
    const doc = this.doc;
    const notes: string[] = [
      "Las horas corresponden a los registros de tiempo capturados por el equipo dentro del periodo seleccionado.",
      "El costo estimado resulta de multiplicar las horas registradas por la tarifa vigente de cada colaborador.",
      "El estado de las tareas refleja la situación al momento de generar el documento.",
    ];

    const filtros = this.data.filtros;
    if (filtros?.cliente_nombre || filtros?.colaborador_nombre) {
      const aplicados: string[] = [];
      if (filtros.cliente_nombre) aplicados.push(`el cliente ${filtros.cliente_nombre}`);
      if (filtros.colaborador_nombre) aplicados.push(`el colaborador ${filtros.colaborador_nombre}`);
      notes.push(`Las cifras consideran únicamente ${aplicados.join(" y ")}.`);
    }

    const width = PAGE.contentWidth - 14;
    doc.setFont("helvetica", "normal");
    doc.setFontSize(7);
    const blocks = notes.map((note) => doc.splitTextToSize(note, width));
    const lineCount = blocks.reduce((total, block) => total + block.length, 0);
    const height = 16 + lineCount * 3.8 + notes.length;

    this.ensureSpace(height + 4);

    const x = PAGE.margin;
    const y = this.y;
    this.card(x, y, PAGE.contentWidth, height);
    this.cardTitle("Notas y criterios del reporte", x + 5, y + 9);

    let cursor = y + 15;
    blocks.forEach((block) => {
      doc.setFillColor(...COLORS.gold);
      doc.circle(x + 7, cursor - 1, 0.8, "F");
      doc.setFont("helvetica", "normal");
      doc.setFontSize(7);
      doc.setTextColor(...COLORS.muted);
      doc.text(block, x + 10, cursor);
      cursor += block.length * 3.8 + 1.2;
    });

    this.y = y + height + 4;
  }

  private teamRows(): ListRow[] {    return (this.data.tiempo_por_empleado ?? []).map((row) => ({
      id: row.colaborador_id,
      label: row.nombre,
      minutos: row.minutos,
    }));
  }

  private clientRows(): ListRow[] {
    return (this.data.tiempo_por_cliente ?? []).map((row) => ({
      id: row.cliente_id,
      label: row.nombre,
      minutos: row.minutos,
    }));
  }

  private categoryRows(): ListRow[] {
    return (this.data.distribucion_por_categoria ?? []).map((row) => ({
      id: row.categoria_id,
      label: row.nombre,
      minutos: row.minutos,
      extra: `${row.porcentaje}%`,
    }));
  }
}

/** Nombre del archivo PDF con el periodo del reporte. */
export function reportPdfFileName(data: ReportData): string {
  return `reporte-ejecutivo-${data.periodo.desde}-a-${data.periodo.hasta}.pdf`;
}

/** Construye el documento PDF del reporte sin descargarlo. */
export async function buildReportPdf(data: ReportData): Promise<{ doc: JsPdf; fileName: string }> {
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
    compress: true,
  });

  const report = new ReportPdf(doc);
  await report.render(data);
  return { doc, fileName: reportPdfFileName(data) };
}

/** Genera y descarga el reporte ejecutivo en PDF. */
export async function exportReportPdf(data: ReportData): Promise<void> {
  const { doc, fileName } = await buildReportPdf(data);
  doc.save(fileName);
}
