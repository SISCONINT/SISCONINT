import { Headphones } from "lucide-react";
import { LoginForm } from "../components/LoginForm";
import { LoginBrandPanel } from "../components/LoginBrandPanel";

export function LoginPage() {
  return (
    <div className="grid w-full overflow-hidden rounded-2xl bg-surface shadow-[0_20px_50px_rgb(16_24_40/12%)] lg:grid-cols-[5fr_7fr]">
      <LoginBrandPanel />

      <section className="flex flex-col">
        <div className="flex-1 px-6 py-8 sm:px-10">
          <div className="mb-1 flex items-center justify-between">
            <span className="text-[10px] font-semibold tracking-wider text-ink">TÉLLEZ PONCE & ASOCIADOS S.C.</span>
            <span className="rounded bg-field px-2 py-0.5 text-[10px] font-medium text-muted">Portal Seguro</span>
          </div>
          <h1 className="font-display text-3xl font-bold text-ink">Bienvenido a SISCONINT</h1>
          <p className="mb-8 mt-1 text-sm text-muted">
            Ingrese sus credenciales corporativas autorizadas para acceder a la plataforma.
          </p>
          <LoginForm />
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 bg-app px-6 py-3.5 text-xs text-muted sm:px-10">
          <span className="inline-flex items-center gap-2">
            <Headphones size={14} />
            Mesa de Ayuda TI: <b className="text-ink">ext. 4022</b> (Lunes a Viernes 08:00 - 19:00 hrs)
          </span>
          <span>Manual Fiduciario · SISCONINT v2.4</span>
        </div>
      </section>
    </div>
  );
}