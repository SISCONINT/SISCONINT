import { createBrowserRouter, Navigate } from "react-router-dom";
import { MainLayout } from "./layouts/MainLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { LoginPage, ActivateAccountPage } from "@/features/auth";
import { CreateUserPage, EditUserPage, UsersListPage } from "@/features/users"
import { ROLES } from "@/shared/constants/roles"
import { RequireAuth, GuestOnly } from "@/shared/auth/RequireAuth";
import { RequireRole } from "@/shared/auth/RequireRole";
import { NAV_SECTIONS } from "@/shared/auth/permissions";

const Placeholder = ({ title }: { title: string }) => (
  <div className="card p-6"><h1 className="text-xl font-semibold">{title}</h1></div>
);

const ADMIN_ROLES = [ROLES.DUENO, ROLES.ADMINISTRADOR];
const IMPLEMENTED_PATHS = ["/colaboradores"];

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
              <RequireRole roles={[ROLES.DUENO, ROLES.ADMINISTRADOR]}>
                <CreateUserPage />
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
              <RequireRole roles={[ROLES.DUENO, ROLES.ADMINISTRADOR]}>
                <CreateClientPage />
              </RequireRole>
            ),
          },
          {
            path: "clientes/:id",
            element: <ClientFilePage />,
          },
          ...NAV_SECTIONS.flatMap((s) =>
            s.items
              .filter((i) => i.path !== "/clientes")
            path: "colaboradores/:id",
            element: (
              <RequireRole roles={ADMIN_ROLES}>
                <EditUserPage />
              </RequireRole>
            ),
          },
          ...NAV_SECTIONS.flatMap((s) =>
            s.items
              .filter((i) => !IMPLEMENTED_PATHS.includes(i.path))
              .map((i) => ({
                path: i.path.slice(1),
                element: (
                  <RequireRole roles={i.roles}>
                    <Placeholder title={i.label} />
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