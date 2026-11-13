import { createBrowserRouter, Navigate } from "react-router-dom";
import { MainLayout } from "./layouts/MainLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { LoginPage, ActivateAccountPage } from "@/features/auth";
import { CreateUserPage, EditUserPage, UsersListPage } from "@/features/users";
import { ClientsListPage, CreateClientPage, ClientFilePage } from "@/features/clients";
import { CatalogPage } from "@/features/catalog";
import { TaskDetailPage, TasksPage } from "@/features/tasks";
import { KanbanBoardPage } from "@/features/kanban";
import { TimeEntriesPage } from "@/features/time";
import { AlertsPage } from "@/features/alerts";
import { NotificationsPage } from "@/features/notifications";
import { DashboardPage } from "@/features/dashboard/dashboard";
import { CalendarPage } from "@/features/calendar/calendar";
import { ObligationsPage } from "@/features/obligations/obligations";
import { MinutesPage } from "@/features/minutes/minutes";
import { RatesPage } from "@/features/rates/rates";
import { ReportsPage } from "@/features/reports";
import { TemplatesPage } from "@/features/templates";
import { ROLES } from "@/shared/constants/roles";
import { PagePlaceholder } from "@/shared/components/components";
import { RequireAuth, GuestOnly } from "@/shared/auth/RequireAuth";
import { RequireRole } from "@/shared/auth/RequireRole";
import { NAV_SECTIONS } from "@/shared/auth/permissions";

const ADMIN_ROLES = [ROLES.DUENO, ROLES.ADMINISTRADOR];
const GERENCIA_ROLES = [ROLES.DUENO, ROLES.ADMINISTRADOR, ROLES.COORDINADOR];
const IMPLEMENTED_PATHS = [
  "/dashboard",
  "/colaboradores",
  "/clientes",
  "/catalogo",
  "/tareas",
  "/tablero",
  "/tiempos",
  "/alertas",
  "/notificaciones",
  "/calendario",
  "/obligaciones",
  "/minutas",
  "/tarifas",
  "/reportes",
  "/plantillas",
];

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
          {
            path: "dashboard",
            element: <DashboardPage />,
          },
          {
            path: "colaboradores",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <UsersListPage />
              </RequireRole>
            ),
          },
          {
            path: "colaboradores/nuevo",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <CreateUserPage />
              </RequireRole>
            ),
          },
          {
            path: "colaboradores/:id",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <EditUserPage />
              </RequireRole>
            ),
          },
          {
            path: "clientes",
            element: <ClientsListPage />,
          },
          {
            path: "clientes/nuevo",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <CreateClientPage />
              </RequireRole>
            ),
          },
          {
            path: "clientes/:id",
            element: <ClientFilePage />,
          },
          {
            path: "catalogo",
            element: <CatalogPage />,
          },
          {
            path: "tareas",
            element: <TasksPage />,
          },
          {
            path: "tareas/:id",
            element: <TaskDetailPage />,
          },
          {
            path: "tablero",
            element: <KanbanBoardPage />,
          },
          {
            path: "calendario",
            element: <CalendarPage />,
          },
          {
            path: "obligaciones",
            element: <ObligationsPage />,
          },
          {
            path: "minutas",
            element: <MinutesPage />,
          },
          {
            path: "tiempos",
            element: <TimeEntriesPage />,
          },
          {
            path: "tarifas",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <RatesPage />
              </RequireRole>
            ),
          },
          {
            path: "reportes",
            element: (
              <RequireRole roles={GERENCIA_ROLES}>
                <ReportsPage />
              </RequireRole>
            ),
          },
          {
            path: "plantillas",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <TemplatesPage />
              </RequireRole>
            ),
          },
          {
            path: "alertas",
            element: (
              <RequireRole roles={GERENCIA_ROLES}>
                <AlertsPage />
              </RequireRole>
            ),
          },
          {
            path: "notificaciones",
            element: <NotificationsPage />,
          },
          {
            path: "configuracion",
            element: (
              <PagePlaceholder
                title="Configuración"
                description="La configuración general del despacho estará disponible en una próxima versión."
              />
            ),
          },
          {
            path: "soporte",
            element: (
              <PagePlaceholder
                title="Soporte y Mesa de Ayuda"
                description="Para soporte técnico contacta al administrador del sistema."
              />
            ),
          },
          ...NAV_SECTIONS.flatMap((s) =>
            s.items
              .filter((i) => !IMPLEMENTED_PATHS.includes(i.path))
              .map((i) => ({
                path: i.path.slice(1),
                element: (
                  <RequireRole roles={i.roles}>
                    <PagePlaceholder title={i.label} />
                  </RequireRole>
                ),
              })),
          ),
        ],
      },
    ],
  },
  {
    element: <AuthLayout />,
    children: [{ path: "/activar", element: <ActivateAccountPage /> }],
  },
]);
