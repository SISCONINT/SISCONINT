import { Outlet } from "react-router-dom";
import {Sidebar} from "./Sidebar"

export function MainLayout() {
  return (
    <div className="flex min-h-screen bg-app">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto p-5 sm:p-6 lg:p-8">
        {/* Aquí irá después el Topbar (búsqueda, timer, campana, usuario) */}
        <Outlet />
      </main>
    </div>
  );
}