/**
 * Datos de ejemplo para los widgets del dashboard que todavía no tienen API en el
 * backend (horas por colaborador, horas por cliente, costo devengado, distribución por
 * categoría, cumplimiento de plazos). En cuanto exista el módulo de Control de tiempos,
 * estos bloques se reemplazan por datos reales igual que ya se hizo con las tareas.
 */

export const HORAS_POR_EMPLEADO = [
  { nombre: "C.P. Carlos Méndez", rol: "Auditor Senior", horas: 178.5, porcentaje: 111 },
  { nombre: "Lic. Mariana Soto", rol: "Especialista Fiscal", horas: 165.0, porcentaje: 103 },
  { nombre: "Lic. Andrea Treviño", rol: "Contabilidad e Impuestos", horas: 152.0, porcentaje: 95 },
  { nombre: "C.P. Roberto Téllez", rol: "Socio Director", horas: 140.5, porcentaje: 87 },
  { nombre: "C.P. Fernando Ruiz", rol: "Nómina y CFDI", horas: 128.0, porcentaje: 80 },
  { nombre: "Lic. Jorge Ramos", rol: "Asistente Contable", horas: 112.5, porcentaje: 70 },
];

export const HORAS_POR_CLIENTE = [
  { nombre: "Grupo Industrial del Norte S.A. de C.V.", horas: 214.0, monto: 256800 },
  { nombre: "Constructora y Pavimentos Anáhuac S.A.", horas: 186.5, monto: 223800 },
  { nombre: "Distribuidora Médica del Bajío S. de R.L.", horas: 142.0, monto: 170400 },
  { nombre: "Alimentos Balanceados del Centro", horas: 120.5, monto: 144600 },
  { nombre: "Logística Transfronteriza Mexicana", horas: 98.0, monto: 117600 },
];

export const DISTRIBUCION_CATEGORIA = [
  { nombre: "Consultoría y Estrategia Fiscal", horas: 474.5, porcentaje: 38, color: "#0b1445" },
  { nombre: "Cumplimiento y Declaraciones SAT", horas: 349.5, porcentaje: 28, color: "#f5d547" },
  { nombre: "Auditoría y Dictamen Fiscal", horas: 224.5, porcentaje: 18, color: "#1b2866" },
  { nombre: "Contabilidad General y Balanza", horas: 137.5, porcentaje: 11, color: "#c9cfe6" },
  { nombre: "Gestión Administrativa y Minutas", horas: 62.5, porcentaje: 5, color: "#6b7280" },
];

export const MIS_HORAS_POR_CLIENTE = [
  { nombre: "Grupo Industrial del Norte S.A. de C.V.", horas: 58.5, porcentaje: 35 },
  { nombre: "Constructora y Pavimentos Anáhuac S.A.", horas: 42.0, porcentaje: 25 },
  { nombre: "Distribuidora Médica del Bajío S. de R.L.", horas: 31.0, porcentaje: 18 },
  { nombre: "Alimentos Balanceados del Centro", horas: 22.0, porcentaje: 13 },
  { nombre: "Logística Transfronteriza Mexicana", horas: 15.0, porcentaje: 9 },
];

export const MIS_HORAS_POR_CATEGORIA = [
  { nombre: "Consultoría y Estrategia Fiscal", horas: 59.0, porcentaje: 35, color: "#0b1445" },
  { nombre: "Cumplimiento y Declaraciones SAT", horas: 50.5, porcentaje: 30, color: "#f5d547" },
  { nombre: "Auditoría y Dictamen Fiscal", horas: 33.7, porcentaje: 20, color: "#1b2866" },
  { nombre: "Contabilidad General y Balanzas", horas: 25.3, porcentaje: 15, color: "#c9cfe6" },
];

export const CUMPLIMIENTO_PLAZOS = { porcentaje: 94.8, aTiempo: 38, total: 40 };
export const MIS_HORAS_REGISTRADAS = { horas: 168.5, meta: 160, facturables: 148.0, internas: 20.5 };
export const COSTO_DEVENGADO = { monto: 1498200, metaMonto: 1380000, tarifaPromedio: 1200 };
