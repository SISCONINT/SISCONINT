import { NavLink } from "react-router-dom";
import { Landmark, Settings, LifeBuoy, LogOut } from "lucide-react";
import clsx from "clsx";
import { useAuthStore } from "../../shared/auth/authStore";
import { getNavForRole } from "../../shared/auth/permissions";
import { ROLE_LABELS } from "../../shared/constants/roles";
import { useLogout } from "../../features/auth/api/useLogout";

const linkClass = ({ isActive }: { isActive: boolean }) =>
  clsx(
    "flex items-center justify-center gap-2.5 rounded-md px-2.5 py-2 text-[13px] transition-colors lg:justify-start",
    isActive
      ? "bg-navy-700 font-semibold text-gold-500"
      : "font-medium text-on-dark hover:bg-navy-800 hover:text-white",
  );

export function Sidebar() {
  const user = useAuthStore((s) => s.user);
  const { mutate, isPending, isError } = useLogout();

  if (!user) return null;
  const sections = getNavForRole(user.rol);

  return (
    <aside
      aria-label="Menú principal"
      className="sticky top-0 flex h-screen shrink-0 flex-col gap-4 overflow-y-auto bg-navy-900 px-3 py-4 text-on-dark"
    >
      {/* Marca */}
      <div className="flex items-center justify-center gap-2.5 px-1.5 py-1 lg:justify-start">
        <span className="grid size-9 shrink-0 place-items-center rounded-md bg-navy-700 text-gold-500">
          <Landmark size={20} />
        </span>
        <div className="hidden leading-tight lg:block">
          <div className="text-base font-semibold text-white">Téllez Ponce</div>
          <div className="text-[9px] font-bold tracking-wide text-gold-500">
            & ASOCIADOS • SISCONINT
          </div>
        </div>
      </div>

      {/* Rol activo */}
      <div className="hidden items-center justify-between rounded-lg bg-navy-800 px-3 py-2.5 lg:flex">
        <div>
          <span className="block text-[9px] tracking-wider text-on-dark-muted">ROL ACTIVO</span>
          <span className="text-[13px] font-semibold text-white">{ROLE_LABELS[user.rol]}</span>
        </div>
        <span className="rounded-full bg-gold-500 px-2 py-0.5 text-[10px] font-bold text-navy-900">
          RBAC
        </span>
      </div>

      {/* Navegación */}
      <nav className="flex flex-1 flex-col gap-3.5">
        {sections.map((section) => (
          <div key={section.title}>
            <h2 className="hidden px-2.5 pb-1.5 text-[10px] font-semibold tracking-widest text-on-dark-muted lg:block">
              {section.title}
            </h2>
            <ul className="flex flex-col gap-0.5">
              {section.items.map(({ path, label, icon: Icon }) => (
                <li key={path}>
                  <NavLink to={path} className={linkClass} title={label}>
                    <Icon size={17} className="shrink-0" />
                    <span className="hidden lg:inline">{label}</span>
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      {/* Pie */}
      <div className="flex flex-col gap-0.5 border-t border-navy-700 pt-3">
        <NavLink to="/configuracion" className={linkClass} title="Configuración">
          <Settings size={17} className="shrink-0" />
          <span className="hidden lg:inline">Configuración</span>
        </NavLink>
        <NavLink to="/soporte" className={linkClass} title="Soporte y Mesa de Ayuda">
          <LifeBuoy size={17} className="shrink-0" />
          <span className="hidden lg:inline">Soporte y Mesa de Ayuda</span>
        </NavLink>
        <span className="hidden px-2.5 pt-2 text-[10px] text-on-dark-muted lg:block">
          v{import.meta.env.VITE_APP_VERSION ?? "0.1.0"}
        </span>

        <button 
        type="button" 
        title="Cerrar sesion"
        className={clsx(linkClass({ isActive: false }), "w-full disabled:opacity-60")} 
        disabled={isPending} 
        onClick={()=> mutate()}>
          <LogOut size={17} className="shrink-0" />
          <span className="hidden lg:inline">
            {isPending ? "Saliendo…" : "Cerrar sesión"}
          </span>
        </button>

        {isError && (
          <p role="alert" 
          className="hidden px-2.5 text-[11px] font-medium text-red-300 lg:block"
          >
            No se pudo cerrar la sesión. Intenta de nuevo.
          </p>
        )}
      </div>
    </aside>
  );
}