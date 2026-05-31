"use client";

import { useState } from "react";
import {
  isSafeShowcaseUrl,
  validateProjectRequest,
  type ShowcaseProjectRequest,
} from "@/lib/showcase";

const inputClass =
  "w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

const EMPTY: ShowcaseProjectRequest = {
  title: "",
  description: "",
  demo_url: "",
  landing_url: "",
  category: "",
};

export function ShowcaseProjectForm({
  initial,
  submitLabel,
  onSubmit,
  onCancel,
  busy,
}: {
  initial?: ShowcaseProjectRequest;
  submitLabel: string;
  onSubmit: (request: ShowcaseProjectRequest) => void;
  onCancel?: () => void;
  busy?: boolean;
}) {
  const [draft, setDraft] = useState<ShowcaseProjectRequest>(
    initial ?? EMPTY,
  );
  const [errors, setErrors] = useState<string[]>([]);

  function update(patch: Partial<ShowcaseProjectRequest>) {
    setDraft((prev) => ({ ...prev, ...patch }));
  }

  function handleSubmit() {
    const validation = validateProjectRequest(draft);
    setErrors(validation.errors);
    if (!validation.ok) return;
    onSubmit({
      ...draft,
      tags: draft.tags?.filter((t) => t.trim()),
    });
  }

  const demoUnsafe = !isSafeShowcaseUrl(draft.demo_url);
  const landingUnsafe = !isSafeShowcaseUrl(draft.landing_url);

  return (
    <div className="space-y-3 rounded-lg border border-dashed p-4">
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Название</span>
          <input
            className={inputClass}
            value={draft.title}
            onChange={(e) => update({ title: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Категория</span>
          <input
            className={inputClass}
            value={draft.category ?? ""}
            onChange={(e) => update({ category: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm sm:col-span-2">
          <span className="text-muted-foreground">Описание</span>
          <textarea
            className={inputClass}
            rows={2}
            value={draft.description ?? ""}
            onChange={(e) => update({ description: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Ссылка на демо</span>
          <input
            className={inputClass}
            value={draft.demo_url ?? ""}
            placeholder="https://aistudio.google.com/..."
            onChange={(e) => update({ demo_url: e.target.value })}
          />
          {demoUnsafe && (
            <span className="text-xs text-red-600">
              Недопустимый URL (только http/https или путь).
            </span>
          )}
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Ссылка на ленд</span>
          <input
            className={inputClass}
            value={draft.landing_url ?? ""}
            placeholder="https://... или /preview/id"
            onChange={(e) => update({ landing_url: e.target.value })}
          />
          {landingUnsafe && (
            <span className="text-xs text-red-600">
              Недопустимый URL (только http/https или путь).
            </span>
          )}
        </label>
      </div>

      {errors.length > 0 && (
        <ul className="rounded-md border border-red-300 bg-red-50 p-2 text-xs text-red-700">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}

      <p className="text-xs text-muted-foreground">
        Demo-ссылку можно добавить позже.
      </p>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={busy}
          className="rounded-md bg-foreground px-3 py-1.5 text-sm font-semibold text-background disabled:opacity-50"
        >
          {submitLabel}
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            disabled={busy}
            className="rounded-md border px-3 py-1.5 text-sm disabled:opacity-50"
          >
            Отмена
          </button>
        )}
      </div>
    </div>
  );
}
