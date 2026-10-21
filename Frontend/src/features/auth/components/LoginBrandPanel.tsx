import { Lock, ShieldCheck, ScanSearch, ShieldHalf } from "lucide-react";

const FEATURES = [
  { icon: ShieldHalf, title: "Acceso Exclusivo y Restringido", text: "Personal autorizado, socios directores y clientes fiduciarios acreditados." },
  { icon: ScanSearch, title: "Trazabilidad Fiscal Activa", text: "Monitoreo continuo de accesos con estricto sellado de tiempo criptográfico." },
];

export function LoginBrandPanel() {
  return (
    <section className="relative hidden flex-col justify-between bg-linear-to-b from-navy-900 to-[#0d1750] text-white lg:flex">
      <div className="flex flex-col items-center px-10 pt-10 text-center">
        <div className="rounded-2xl bg-navy-800/60 p-2.5">
          <div className="grid size-44 place-items-center rounded-xl bg-navy-950 p-4">
            {/* Coloca el logo en /public/logo-tellez-ponce.png */}
            <img src="/logo-tellez-ponce.png" alt="Téllez Ponce & Asociados" className="max-h-full" />
          </div>
        </div>

        <span className="mt-4 inline-flex items-center gap-1.5 rounded-full bg-navy-800 px-3 py-1 text-[10px] font-bold tracking-wider text-gold-500">
          <ShieldCheck size={12} /> PLATAFORMA CERTIFICADA SAT V4.0
        </span>

        <h2 className="mt-5 font-display text-2xl font-bold">SISCONINT</h2>
        <p className="mt-1 text-[11px] tracking-[0.18em] text-on-dark-muted">
          SISTEMA DE GESTIÓN Y CONTROL INTERNO V2.4
        </p>
        <p className="mt-5 max-w-xs text-sm italic text-on-dark">
          “Rigor fiduciario, certeza contable y excelencia tributaria al servicio de su patrimonio.”
        </p>
      </div>

      <ul className="mx-8 my-6 flex flex-col gap-4 rounded-xl bg-white/5 p-4">
        {FEATURES.map(({ icon: Icon, title, text }) => (
          <li key={title} className="flex gap-3">
            <span className="grid size-8 shrink-0 place-items-center rounded-full bg-white/10 text-gold-500">
              <Icon size={15} />
            </span>
            <div>
              <h3 className="text-sm font-semibold">{title}</h3>
              <p className="text-xs text-on-dark-muted">{text}</p>
            </div>
          </li>
        ))}
      </ul>

      <div className="bg-navy-800/70 px-6 py-4 text-[10px] text-on-dark-muted">
        <div className="mb-1.5 flex items-center justify-between font-semibold text-gold-500">
          <span className="inline-flex items-center gap-1"><Lock size={11} /> Cifrado Fiduciario SSL 256-bit</span>
          <span className="inline-flex items-center gap-1"><ShieldCheck size={11} /> ISO/IEC 27001</span>
        </div>
        Aviso de confidencialidad estricta para socios y auditores. Cualquier intento de intrusión será auditado y remitido a las autoridades correspondientes.
      </div>
    </section>
  );
}