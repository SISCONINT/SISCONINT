import { Outlet } from "react-router-dom";
import {Sidebar} from "./Sidebar"

export function MainLayout() {
  return (
    <div className="flex min-h-dvh">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-x-auto p-4 sm:p-6 lg:p-8">
        {/* Aquí irá después el Topbar (búsqueda, timer, campana, usuario) */}
        <Outlet />
      </main>
    </div>
  );
}