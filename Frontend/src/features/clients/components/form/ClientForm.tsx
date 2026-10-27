import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm, type FieldErrors, type Path } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { ArrowLeft, ArrowRight, Loader2, Save, TriangleAlert } from "lucide-react";
import { ApiError } from "@/shared/api/types";
import { useAccountants, useCreateClient } from "../../api/useClients";
import {
  CLIENT_FIELD_PATHS,
  EMPTY_CLIENT_FORM,
  clientSchema,
  toCreatePayload,
  type ClientFormValues,
} from "../../schemas/client.schema";
import { BTN_GHOST, BTN_PRIMARY, BTN_SECONDARY } from "../../constants";
import { FormStepper, type StepMeta } from "./FormStepper";
import { StepDatosGenerales } from "./StepDatosGenerales";
import { StepDomicilio } from "./StepDomicilio";
import { StepRegimenes } from "./StepRegimenes";
import { StepTrabajadores } from "./StepTrabajadores";
import { StepContactos } from "./StepContactos";

interface StepDefinition extends StepMeta {
  fields: Path<ClientFormValues>[];
}

const STEPS: StepDefinition[] = [
  {
    title: "Datos Generales",
    subtitle: "Identificación fiscal",
    fields: [
      "tipo_persona",
      "rfc",
      "nombre_completo",
      "razon_social",
      "giro",
      "forma_pago",
      "contador_asignado_id",
      "telefono",
      "correo",
    ],
  },
  {
    title: "Domicilio Fiscal",
    subtitle: "Ubicación SAT",
    fields: [
      "codigo_postal",
      "calle",
      "no_exterior",
      "no_interior",
      "colonia",
      "ciudad",
      "estado",
    ],
  },
  {
    title: "Regímenes Fiscales",
    subtitle: "Obligaciones SAT",
    fields: ["regimenes"],
  },
  {
    title: "Trabajadores y Nómina",
    subtitle: "Esquema laboral",
    fields: ["tiene_trabajadores", "tipo_nomina"],
  },
  {
    title: "Contactos y Permisos",
    subtitle: "Representación legal",
    fields: [
      "contacto_principal.nombre_completo",
      "contacto_principal.telefono",
      "contacto_principal.correo",
      "contacto_principal.cargo",
      "contacto_pagos.nombre_completo",
      "contacto_pagos.telefono",
      "contacto_pagos.correo",
      "contacto_pagos.cargo",
    ],
  },
];

function collectErrorPaths(errors: unknown, prefix = ""): string[] {
  if (!errors || typeof errors !== "object") return [];

  return Object.entries(errors as Record<string, unknown>).flatMap(([key, value]) => {
    if (!value) return [];
    const path = prefix ? `${prefix}.${key}` : key;

    if (typeof value === "object" && value !== null && "message" in value) {
      return [path];
    }
    if (typeof value === "object") {
      return collectErrorPaths(value, path);
    }
    return [];
  });
}

function stepForPath(path: string): number {
  const index = STEPS.findIndex((step) =>
    step.fields.some(
      (field) =>
        field === path || path.startsWith(`${field}.`) || field.startsWith(`${path}.`),
    ),
  );
  return index === -1 ? 0 : index;
}

export function ClientForm() {
  const navigate = useNavigate();
  const mutation = useCreateClient();
  const accountantsQuery = useAccountants(true);

  const [step, setStep] = useState(0);
  const [maxVisited, setMaxVisited] = useState(0);
  const [feedback, setFeedback] = useState<string | null>(null);

  const form = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: EMPTY_CLIENT_FORM,
    mode: "onTouched",
  });

  const { trigger, handleSubmit, setError } = form;

  const scrollTop = () => window.scrollTo({ top: 0, behavior: "smooth" });

  const goToStep = (index: number) => {
    setStep(index);
    scrollTop();
  };

  const handleNext = async () => {
    setFeedback(null);
    const valid = await trigger(STEPS[step].fields, { shouldFocus: true });
    if (!valid) return;

    const next = Math.min(step + 1, STEPS.length - 1);
    setStep(next);
    setMaxVisited((visited) => Math.max(visited, next));
    scrollTop();
  };

  const handleBack = () => {
    setFeedback(null);
    setStep((current) => Math.max(0, current - 1));
    scrollTop();
  };

  const handleInvalid = (formErrors: FieldErrors<ClientFormValues>) => {
    const firstPath = collectErrorPaths(formErrors)[0];
    if (firstPath) goToStep(stepForPath(firstPath));
    setFeedback("Revisa los campos marcados en rojo antes de registrar al contribuyente.");
    scrollTop();
  };

  const onSubmit = (values: ClientFormValues) => {
    setFeedback(null);

    mutation.mutate(toCreatePayload(values), {
      onSuccess: (cliente) => {
        navigate(`/clientes/${cliente.id}`, {
          state: { cliente, recienCreado: true },
          replace: true,
        });
      },
      onError: (error) => {
        const apiError = error instanceof ApiError ? error : null;

        if (apiError?.fields) {
          Object.entries(apiError.fields).forEach(([field, messages]) => {
            if (CLIENT_FIELD_PATHS.has(field)) {
              setError(field as Path<ClientFormValues>, {
                type: "server",
                message: messages[0],
              });
            }
          });

          const firstField = Object.keys(apiError.fields).find((field) =>
            CLIENT_FIELD_PATHS.has(field),
          );
          if (firstField) goToStep(stepForPath(firstField));
          setFeedback("Revisa los campos marcados en rojo.");
        } else {
          setFeedback(apiError?.message ?? "Ocurrió un error inesperado. Intenta de nuevo.");
        }

        scrollTop();
      },
    });
  };

  return (
    <div className="flex flex-col gap-4">
      <FormStepper
        steps={STEPS}
        current={step}
        maxVisited={maxVisited}
        onSelect={goToStep}
      />

      {feedback && (
        <div
          role="alert"
          className="flex items-start gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm font-medium text-danger"
        >
          <TriangleAlert size={18} className="mt-0.5 shrink-0" />
          {feedback}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit, handleInvalid)} noValidate className="flex flex-col gap-4">
        {step === 0 && (
          <StepDatosGenerales
            form={form}
            accountants={accountantsQuery.data ?? []}
            accountantsLoading={accountantsQuery.isLoading}
            accountantsError={accountantsQuery.isError}
          />
        )}
        {step === 1 && <StepDomicilio form={form} />}
        {step === 2 && <StepRegimenes form={form} />}
        {step === 3 && <StepTrabajadores form={form} />}
        {step === 4 && <StepContactos form={form} />}

        <div className="card flex flex-col-reverse gap-2 p-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2">
            <Link to="/clientes" className={BTN_GHOST}>
              Cancelar
            </Link>
            <span className="hidden text-[11px] text-muted sm:inline">
              Paso {step + 1} de {STEPS.length}
            </span>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row">
            {step > 0 && (
              <button type="button" onClick={handleBack} className={BTN_SECONDARY}>
                <ArrowLeft size={15} />
                Anterior
              </button>
            )}

            {step < STEPS.length - 1 ? (
              <button type="button" onClick={handleNext} className={BTN_PRIMARY}>
                Continuar
                <ArrowRight size={16} />
              </button>
            ) : (
              <button type="submit" disabled={mutation.isPending} className={BTN_PRIMARY}>
                {mutation.isPending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Save size={16} />
                )}
                {mutation.isPending ? "Registrando…" : "Registrar contribuyente"}
              </button>
            )}
          </div>
        </div>
      </form>
    </div>
  );
}
