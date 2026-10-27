import { useLocation, useNavigate } from "react-router-dom";
import { PageHeader } from "@/shared/components/PageHeader";
import { useCreateTask } from "../api/useTasks";
import { TaskForm } from "../components/TaskForm";

export function TaskCreatePage() {
  const navigate = useNavigate();
  const location = useLocation();
  const clienteIdFromState = (location.state as { clienteId?: number } | null)?.clienteId;
  const { mutate, isPending, error } = useCreateTask();

  return (
    <div>
      <PageHeader title="Nueva tarea" crumbs={[{ label: "Tareas", to: "/tareas" }, { label: "Nueva" }]} />
      <div className="card p-5">
        <TaskForm
          defaultValues={clienteIdFromState ? { cliente_id: clienteIdFromState } : undefined}
          submitLabel="Guardar tarea"
          pending={isPending}
          serverError={error}
          onCancel={() => navigate(-1)}
          onSubmit={(values) =>
            mutate(values, {
              onSuccess: (created) => navigate(`/tareas/${created.id}`),
            })
          }
        />
      </div>
    </div>
  );
}
