import { Outlet } from "react-router-dom";
import {Sidebar} from "./Sidebar"

export function MainLayout() {
  return (
    <div className="app-shell">
      <Sidebar />
      <main className="app-main">
        {/* Aquí irá después el Topbar (búsqueda, timer, campana, usuario) */}
        <Outlet />
      </main>
    </div>
  );
}