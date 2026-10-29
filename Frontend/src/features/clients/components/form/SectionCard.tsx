import type { ReactNode } from "react";

interface Props {
  number: string;
  title: string;
  description: string;
  aside?: ReactNode;
  children: ReactNode;
}

export function SectionCard({ number, title, description, aside, children }: Props) {
  return (
    <section className="card p-4 sm:p-6">
      <header className="mb-5 flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div className="flex items-start gap-3">
          <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-navy-900 font-display text-sm font-bold text-gold-500">
            {number}
          </span>
          <div>
            <h2 className="font-display text-lg font-bold leading-tight text-ink">{title}</h2>
            <p className="mt-0.5 max-w-2xl text-xs leading-relaxed text-muted">{description}</p>
          </div>
        </div>
        {aside}
      </header>
      {children}
    </section>
  );
}
