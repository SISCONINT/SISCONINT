import type { ReactNode } from "react";
import { X } from "lucide-react";

interface Props {
  open: boolean;
  title: string;
  subtitle?: string;
  onClose: () => void;
  children: ReactNode;
  wide?: boolean;
}

/** Panel lateral usado para formularios (crear/editar) sin navegar a otra página. */
export function Drawer({ open, title, subtitle, onClose, children, wide }: Props) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-40 flex justify-end bg-navy-950/40">
      <button
        type="button"
        aria-label="Cerrar panel"
        onClick={onClose}
        className="absolute inset-0 cursor-default"
      />
      <div
        className={`relative flex h-full w-full ${wide ? "max-w-2xl" : "max-w-lg"} flex-col overflow-y-auto bg-surface shadow-[0_0_40px_rgb(16_24_40/25%)]`}
      >
        <div className="sticky top-0 z-10 flex items-start justify-between gap-3 border-b border-line bg-surface px-6 py-4">
          <div>
            <h2 className="font-display text-lg font-bold text-ink">{title}</h2>
            {subtitle && <p className="mt-0.5 text-sm text-muted">{subtitle}</p>}
          </div>
          <button type="button" onClick={onClose} className="text-muted hover:text-ink" aria-label="Cerrar">
            <X size={20} />
          </button>
        </div>
        <div className="flex-1 px-6 py-5">{children}</div>
      </div>
    </div>
  );
}
