import { Outlet } from "react-router-dom";
import { Lock, ShieldCheck } from "lucide-react";

export function AuthLayout() {
  return (
    <div className="flex min-h-screen flex-col bg-app">
      <header className="mx-auto flex w-full max-w-[1240px] items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-lg bg-navy-900 text-gold-500">
            <ShieldCheck size={20} />
          </span>
          <div className="leading-tight">
            <div className="font-display text-lg font-bold text-ink">SISCONINT</div>
            <div className="text-[10px] font-medium tracking-wide text-muted">TÉLLEZ PONCE & ASOCIADOS S.C.</div>
          </div>
        </div>
        <span className="hidden items-center gap-2 rounded-full bg-white px-3.5 py-1.5 text-[10px] font-semibold tracking-wider text-ink shadow-card sm:inline-flex">
          <span className="size-2 rounded-full bg-gold-700" /> CANAL CIFRADO SAT V4.0
        </span>
      </header>

      <main className="mx-auto flex w-full max-w-[1240px] flex-1 items-center px-4 pb-6 sm:px-6">
        <Outlet />
      </main>

      <footer className="border-t border-line bg-white px-4 py-3 text-[11px] text-muted sm:px-6">
        <div className="mx-auto flex max-w-[1240px] flex-wrap items-center justify-between gap-2">
          <span className="inline-flex items-center gap-2">
            <Lock size={12} /> Entorno fiduciario reservado. El acceso no autorizado está tipificado conforme al CFF y Ley General de Protección de Datos Personales.
          </span>
          <span className="font-semibold tracking-wide">
            ISO/IEC 27001 CERTIFIED · © 2025 TÉLLEZ PONCE & ASOCIADOS
          </span>
        </div>
      </footer>
    </div>
  );
}