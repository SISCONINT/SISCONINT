import { UserForm } from "../components/UserForm";

export function CreateUserPage() {
  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-5">
      <header>
        <h1 className="font-display text-2xl font-bold text-ink">Registrar colaborador</h1>
        <p className="mt-1 text-sm text-muted">
          El colaborador recibirá un correo con un enlace para definir su contraseña.
        </p>
      </header>
      <UserForm />
    </div>
  );
}