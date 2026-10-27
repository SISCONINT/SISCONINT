import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/shared/components/PageHeader";
import { useCreateUser } from "../api/useUsers";
import { UserForm } from "../components/UserForm";

export function UserCreatePage() {
  const navigate = useNavigate();
  const { mutate, isPending, error } = useCreateUser();

  return (
    <div>
      <PageHeader
        title="Nuevo colaborador"
        crumbs={[{ label: "Colaboradores", to: "/colaboradores" }, { label: "Nuevo" }]}
      />
      <div className="card p-5">
        <UserForm
          submitLabel="Registrar colaborador"
          pending={isPending}
          serverError={error}
          onCancel={() => navigate("/colaboradores")}
          onSubmit={(values) =>
            mutate(values, {
              onSuccess: (created) => navigate(`/colaboradores/${created.id}`),
            })
          }
        />
      </div>
    </div>
  );
}
