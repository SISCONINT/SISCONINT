import { useState } from "react";
import { useForm } from "react-hook-form";
import { Mail, Pencil, Plus, X } from "lucide-react";
import { TextField } from "@/shared/components/TextField";
import { FormField, plainInputClass } from "@/shared/components/FormField";
import { BTN_PRIMARY, BTN_SECONDARY } from "@/shared/components/buttons";
import { ApiError } from "@/shared/api/types";
import { useCreateTemplate, useTemplates, useUpdateTemplate } from "../api/useTemplates";
import type { PlantillaCorreo, PlantillaFormValues } from "../types";

function TemplateFormFields({
  register,
  errors,
  showClave,
}: {
  register: ReturnType<typeof useForm<PlantillaFormValues>>["register"];
  errors: ReturnType<typeof useForm<PlantillaFormValues>>["formState"]["errors"];
  showClave: boolean;
}) {
  return (
    <>
      {showClave && (
        <TextField
          label="Clave"
          required
          maxLength={50}
          hint="Identificador único, ej. ALTA_CLIENTE"
          registration={register("clave", { required: true })}
          error={errors.clave as never}
        />
      )}
      <TextField label="Nombre" required maxLength={150} registration={register("nombre", { required: true })} error={errors.nombre as never} />
      <TextField label="Asunto del correo" required maxLength={200} registration={register("asunto", { required: true })} error={errors.asunto as never} />
      <FormField label="Cuerpo" htmlFor="cuerpo" required error={errors.cuerpo?.message} hint="Puede incluir placeholders como {nombre}">
        <textarea id="cuerpo" rows={6} className={plainInputClass} {...register("cuerpo", { required: "Campo obligatorio" })} />
      </FormField>
      <label className="flex items-center gap-2 text-sm text-ink">
        <input type="checkbox" className="size-4 rounded border-line accent-navy-900" {...register("activa")} />
        Plantilla activa
      </label>
    </>
  );
}

function NewTemplateForm({ onClose }: { onClose: () => void }) {
  const mutation = useCreateTemplate();
  const { register, handleSubmit, formState: { errors } } = useForm<PlantillaFormValues>({
    defaultValues: { clave: "", nombre: "", asunto: "", cuerpo: "", activa: true },
  });

  const onSubmit = (values: PlantillaFormValues) => mutation.mutate(values, { onSuccess: onClose });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ink">Nueva plantilla</h2>
        <button type="button" onClick={onClose} className="text-muted hover:text-ink" aria-label="Cerrar"><X size={18} /></button>
      </div>
      {mutation.error && (
        <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-danger">
          {mutation.error instanceof ApiError ? mutation.error.message : "Ocurrió un error inesperado."}
        </p>
      )}
      <TemplateFormFields register={register} errors={errors} showClave />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={onClose} className={BTN_SECONDARY}>Cancelar</button>
        <button type="submit" disabled={mutation.isPending} className={BTN_PRIMARY}>{mutation.isPending ? "Guardando…" : "Crear plantilla"}</button>
      </div>
    </form>
  );
}

function TemplateCard({ plantilla }: { plantilla: PlantillaCorreo }) {
  const [editing, setEditing] = useState(false);
  const mutation = useUpdateTemplate(plantilla.id);
  const { register, handleSubmit, formState: { errors } } = useForm<PlantillaFormValues>({
    defaultValues: { clave: plantilla.clave, nombre: plantilla.nombre, asunto: plantilla.asunto, cuerpo: plantilla.cuerpo, activa: plantilla.activa },
  });

  if (!editing) {
    return (
      <div className="card flex items-start justify-between gap-3 p-4">
        <div className="min-w-0">
          <p className="flex items-center gap-2 font-semibold text-ink">
            {plantilla.nombre}
            {!plantilla.activa && <span className="rounded bg-field px-1.5 py-0.5 text-[10px] font-semibold text-muted">Inactiva</span>}
          </p>
          <p className="text-[12px] text-muted">Clave: {plantilla.clave}</p>
          <p className="mt-1 text-sm text-ink/80">Asunto: {plantilla.asunto}</p>
        </div>
        <button type="button" onClick={() => setEditing(true)} className="shrink-0 text-muted hover:text-ink" aria-label="Editar plantilla">
          <Pencil size={16} />
        </button>
      </div>
    );
  }

  const onSubmit = (values: PlantillaFormValues) =>
    mutation.mutate({ nombre: values.nombre, asunto: values.asunto, cuerpo: values.cuerpo, activa: values.activa }, { onSuccess: () => setEditing(false) });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-ink">Editar plantilla</h2>
        <button type="button" onClick={() => setEditing(false)} className="text-muted hover:text-ink" aria-label="Cerrar"><X size={18} /></button>
      </div>
      <TemplateFormFields register={register} errors={errors} showClave={false} />
      <div className="flex justify-end gap-2">
        <button type="button" onClick={() => setEditing(false)} className={BTN_SECONDARY}>Cancelar</button>
        <button type="submit" disabled={mutation.isPending} className={BTN_PRIMARY}>{mutation.isPending ? "Guardando…" : "Guardar cambios"}</button>
      </div>
    </form>
  );
}

export function TemplatesPage() {
  const { data, isLoading } = useTemplates();
  const [showNew, setShowNew] = useState(false);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-4">
      <header className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <nav aria-label="Ruta de navegación" className="mb-1 flex items-center gap-1.5 text-[11px] text-muted">
            <span>Administración</span>
            <span aria-hidden="true">/</span>
            <span className="font-semibold text-navy-800">Plantillas de correo</span>
          </nav>
          <div className="flex items-center gap-2">
            <Mail size={20} className="text-gold-700" />
            <h1 className="font-display text-2xl font-bold text-ink">Plantillas de correo</h1>
          </div>
          <p className="mt-1.5 text-sm text-muted">Asunto y cuerpo de los correos automáticos del despacho.</p>
        </div>
        <button type="button" onClick={() => setShowNew((s) => !s)} className={BTN_PRIMARY}>
          <Plus size={16} /> Nueva plantilla
        </button>
      </header>

      {showNew && <NewTemplateForm onClose={() => setShowNew(false)} />}

      {isLoading ? (
        <p className="text-sm text-muted">Cargando plantillas…</p>
      ) : (data?.length ?? 0) === 0 ? (
        <div className="card p-10 text-center text-sm text-muted">Sin plantillas registradas.</div>
      ) : (
        <div className="flex flex-col gap-3">
          {data!.map((p) => <TemplateCard key={p.id} plantilla={p} />)}
        </div>
      )}
    </div>
  );
}
