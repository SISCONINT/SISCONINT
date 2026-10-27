import { createBrowserRouter, Navigate } from "react-router-dom";
import { MainLayout } from "./layouts/MainLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { LoginPage } from "@/features/auth";
import { RequireAuth, GuestOnly } from "@/shared/auth/RequireAuth";
import { RequireRole } from "@/shared/auth/RequireRole";
import { NAV_SECTIONS } from "@/shared/auth/permissions";
import { ROLES } from "@/shared/constants/roles";
import { ComingSoon } from "@/shared/components/EmptyState";
import { Placeholder } from "@/shared/components/Placeholder";
import { CatalogPage } from "@/features/catalog";
import { DashboardPage } from "@/features/dashboard";
import { UserCreatePage, UserDetailPage, UsersListPage } from "@/features/users";
import { ClientCreatePage, ClientDetailPage, ClientsListPage } from "@/features/clients";
import { KanbanBoardPage, TaskCreatePage, TaskDetailPage, TaskListPage } from "@/features/tasks";

const { DUENO, ADMINISTRADOR } = ROLES;

/** Páginas ya conectadas al backend real; el resto sigue como Placeholder hasta tener API. */
const REAL_PAGES: Record<string, React.ReactNode> = {
  "/dashboard": <DashboardPage />,
  "/tablero": <KanbanBoardPage />,
  "/tareas": <TaskListPage />,
  "/clientes": <ClientsListPage />,
  "/colaboradores": <UsersListPage />,
  "/catalogo": <CatalogPage />,
};

/** Módulos sin API todavía: se deja la maqueta como "próximamente" en vez del placeholder genérico. */
const COMING_SOON: Record<string, { title: string; description?: string }> = {
  "/calendario": { title: "Calendario operativo" },
  "/obligaciones": { title: "Obligaciones periódicas" },
  "/minutas": { title: "Minutas" },
  "/tiempos": { title: "Registro de tiempos" },
  "/alertas": { title: "Alertas fiscales" },
  "/reportes": { title: "Reportes ejecutivos" },
  "/tarifas": { title: "Tarifas" },
  "/plantillas": { title: "Plantillas de correo" },
};

export const router = createBrowserRouter([
  {
    element: <GuestOnly />,
    children: [{ element: <AuthLayout />, children: [{ path: "/login", element: <LoginPage /> }] }],
  },
  {
    element: <RequireAuth />,
    children: [
      {
        path: "/",
        element: <MainLayout />,
        children: [
          { index: true, element: <Navigate to="/dashboard" replace /> },

          ...NAV_SECTIONS.flatMap((s) =>
            s.items.map((i) => ({
              path: i.path.slice(1),
              element: (
                <RequireRole roles={i.roles}>
                  {REAL_PAGES[i.path] ?? (COMING_SOON[i.path] ? <ComingSoon {...COMING_SOON[i.path]} /> : <Placeholder title={i.label} />)}
                </RequireRole>
              ),
            })),
          ),

          // Rutas adicionales de los módulos ya conectados (alta, detalle, edición).
          { path: "tareas/nuevo", element: <TaskCreatePage /> },
          { path: "tareas/:id", element: <TaskDetailPage /> },
          {
            path: "clientes/nuevo",
            element: (
              <RequireRole roles={[DUENO, ADMINISTRADOR]}>
                <ClientCreatePage />
              </RequireRole>
            ),
          },
          { path: "clientes/:id", element: <ClientDetailPage /> },
          {
            path: "colaboradores/nuevo",
            element: (
              <RequireRole roles={[DUENO, ADMINISTRADOR]}>
                <UserCreatePage />
              </RequireRole>
            ),
          },
          {
            path: "colaboradores/:id",
            element: (
              <RequireRole roles={[DUENO, ADMINISTRADOR]}>
                <UserDetailPage />
              </RequireRole>
            ),
          },
        ],
      },
    ],
  },
]);
