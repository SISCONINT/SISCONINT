import { useNavigate } from "react-router-dom";
import { PageHeader } from "@/shared/components/PageHeader";
import { useCreateClient } from "../api/useClients";
import { ClientForm } from "../components/ClientForm";

export function ClientCreatePage() {
  const navigate = useNavigate();
  const { mutate, isPending, error } = useCreateClient();

  return (
    <div>
      <PageHeader title="Nuevo cliente" crumbs={[{ label: "Clientes", to: "/clientes" }, { label: "Nuevo" }]} />
      <div className="card p-5">
        <ClientForm
          submitLabel="Registrar cliente"
          pending={isPending}
          serverError={error}
          onCancel={() => navigate("/clientes")}
          onSubmit={(values) =>
            mutate(values, {
              onSuccess: () => navigate("/clientes"),
            })
          }
        />
      </div>
    </div>
  );
}
