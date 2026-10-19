import { createBrowserRouter, Navigate } from "react-router-dom";
import { MainLayout } from "./layouts/MainLayout";
import { AuthLayout } from "./layouts/AuthLayout";
import { LoginPage } from "../features/auth";
import { RequireAuth, GuestOnly } from "../shared/auth/RequireAuth";
import { RequireRole } from "../shared/auth/RequireRole";
import { NAV_SECTIONS } from "../shared/auth/permissions";

const Placeholder = ({ title }: { title: string }) => (
  <div className="card p-6"><h1 className="text-xl font-semibold">{title}</h1></div>
);

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
                  <Placeholder title={i.label} />
                </RequireRole>
              ),
            })),
          ),
        ],
      },
    ],
  },
]);