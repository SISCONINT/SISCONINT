import { Link, useSearchParams } from "react-router-dom";
import { ActivateAccountForm } from "../components/ActivateAccountForm";

export function ActivateAccountPage() {
  const [params] = useSearchParams();
  const token = params.get("token");

  return (
    <div className="mx-auto w-full max-w-md rounded-2xl bg-surface p-6 shadow-[0_20px_50px_rgb(16_24_40/12%)] sm:p-8">
      <h1 className="font-display text-2xl font-bold text-ink">Activa tu cuenta</h1>
      <p className="mb-6 mt-1 text-sm text-muted">Define la contraseña con la que entrarás a SISCONINT.</p>

      {token ? (
        <ActivateAccountForm token={token} />
      ) : (
        <div role="alert" className="rounded-lg bg-red-50 px-3 py-3 text-sm font-medium text-danger">
          El enlace no es válido. Pide a un administrador que te envíe uno nuevo.
          <Link to="/login" className="mt-3 block text-xs text-gold-700 underline">Ir a iniciar sesión</Link>
        </div>
      )}
    </div>
  );
}