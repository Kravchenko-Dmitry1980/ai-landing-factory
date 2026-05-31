"use client";

import { useState } from "react";
import {
  createEmptyProject,
  exportShowcase,
  isSafeShowcaseUrl,
  validateShowcaseConfig,
  type ShowcaseConfigInput,
  type ShowcaseLayout,
  type ShowcaseMode,
  type ShowcaseProjectInput,
  type ShowcaseTheme,
} from "@/lib/showcase";

const LAYOUTS: { value: ShowcaseLayout; label: string }[] = [
  { value: "gallery_arc", label: "Дуга-галерея" },
  { value: "grid_hall", label: "Сетка-холл" },
  { value: "circle_booths", label: "Круг стендов" },
];

const THEMES: { value: ShowcaseTheme; label: string }[] = [
  { value: "university", label: "University" },
  { value: "tech", label: "Tech" },
  { value: "dark", label: "Dark" },
];

const MODES: { value: ShowcaseMode; label: string }[] = [
  { value: "web3d", label: "Web 3D" },
  { value: "vr_ready", label: "VR Ready" },
];

const inputClass =
  "w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

export function ShowcaseBuilder() {
  const [config, setConfig] = useState<ShowcaseConfigInput>(() => ({
    title: "Витрина проектов",
    subtitle: "",
    organization: "",
    layout: "gallery_arc",
    mode: "web3d",
    theme: "university",
    projects: [
      {
        ...createEmptyProject(),
        title: "",
        description: "",
        demo_url: "",
      },
    ],
  }));
  const [errors, setErrors] = useState<string[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);

  function updateConfig(patch: Partial<ShowcaseConfigInput>) {
    setConfig((prev) => ({ ...prev, ...patch }));
  }

  function updateProject(index: number, patch: Partial<ShowcaseProjectInput>) {
    setConfig((prev) => {
      const projects = prev.projects.map((p, i) =>
        i === index ? { ...p, ...patch } : p,
      );
      return { ...prev, projects };
    });
  }

  function addProject() {
    setConfig((prev) => ({
      ...prev,
      projects: [...prev.projects, createEmptyProject()],
    }));
  }

  function removeProject(index: number) {
    setConfig((prev) => ({
      ...prev,
      projects: prev.projects.filter((_, i) => i !== index),
    }));
  }

  async function handleExport() {
    const validation = validateShowcaseConfig(config);
    setErrors(validation.errors);
    setWarnings([]);
    setStatus(null);
    if (!validation.ok) return;

    setBusy(true);
    try {
      const result = await exportShowcase(config);
      setWarnings(result.warnings ?? []);
      const blob = new Blob([result.html], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = "showcase.html";
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
      setStatus(
        `Экспортировано: ${result.project_count} проект(ов), режим ${result.mode}.`,
      );
    } catch (err) {
      setErrors([err instanceof Error ? err.message : "Ошибка экспорта."]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="space-y-4 rounded-lg border p-4">
        <h2 className="text-lg font-semibold">Параметры витрины</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Название</span>
            <input
              className={inputClass}
              value={config.title}
              onChange={(e) => updateConfig({ title: e.target.value })}
            />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Подзаголовок</span>
            <input
              className={inputClass}
              value={config.subtitle ?? ""}
              onChange={(e) => updateConfig({ subtitle: e.target.value })}
            />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Организация</span>
            <input
              className={inputClass}
              value={config.organization ?? ""}
              onChange={(e) => updateConfig({ organization: e.target.value })}
            />
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Раскладка</span>
            <select
              className={inputClass}
              value={config.layout}
              onChange={(e) =>
                updateConfig({ layout: e.target.value as ShowcaseLayout })
              }
            >
              {LAYOUTS.map((l) => (
                <option key={l.value} value={l.value}>
                  {l.label}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Тема</span>
            <select
              className={inputClass}
              value={config.theme}
              onChange={(e) =>
                updateConfig({ theme: e.target.value as ShowcaseTheme })
              }
            >
              {THEMES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="space-y-1 text-sm">
            <span className="text-muted-foreground">Режим</span>
            <select
              className={inputClass}
              value={config.mode}
              onChange={(e) =>
                updateConfig({ mode: e.target.value as ShowcaseMode })
              }
            >
              {MODES.map((m) => (
                <option key={m.value} value={m.value}>
                  {m.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Проекты</h2>
          <button
            type="button"
            onClick={addProject}
            className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
          >
            + Добавить проект
          </button>
        </div>

        {config.projects.map((project, index) => {
          const demoUnsafe = !isSafeShowcaseUrl(project.demo_url);
          const landingUnsafe = !isSafeShowcaseUrl(project.landing_url);
          return (
            <div key={project.id} className="space-y-3 rounded-lg border p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-muted-foreground">
                  Проект {index + 1}
                </span>
                {config.projects.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeProject(index)}
                    className="text-sm text-red-600 hover:underline"
                  >
                    Удалить
                  </button>
                )}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="space-y-1 text-sm">
                  <span className="text-muted-foreground">Название</span>
                  <input
                    className={inputClass}
                    value={project.title}
                    onChange={(e) =>
                      updateProject(index, { title: e.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="text-muted-foreground">Категория</span>
                  <input
                    className={inputClass}
                    value={project.category ?? ""}
                    onChange={(e) =>
                      updateProject(index, { category: e.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm sm:col-span-2">
                  <span className="text-muted-foreground">Описание</span>
                  <textarea
                    className={inputClass}
                    rows={2}
                    value={project.description}
                    onChange={(e) =>
                      updateProject(index, { description: e.target.value })
                    }
                  />
                </label>
                <label className="space-y-1 text-sm">
                  <span className="text-muted-foreground">Demo URL</span>
                  <input
                    className={inputClass}
                    value={project.demo_url ?? ""}
                    onChange={(e) =>
                      updateProject(index, { demo_url: e.target.value })
                    }
                    placeholder="https://aistudio.google.com/..."
                  />
                  {demoUnsafe && (
                    <span className="text-xs text-red-600">
                      Недопустимый URL (только http/https или путь).
                    </span>
                  )}
                </label>
                <label className="space-y-1 text-sm">
                  <span className="text-muted-foreground">Landing URL</span>
                  <input
                    className={inputClass}
                    value={project.landing_url ?? ""}
                    onChange={(e) =>
                      updateProject(index, { landing_url: e.target.value })
                    }
                    placeholder="https://... или /landings/id"
                  />
                  {landingUnsafe && (
                    <span className="text-xs text-red-600">
                      Недопустимый URL (только http/https или путь).
                    </span>
                  )}
                </label>
              </div>
            </div>
          );
        })}
      </section>

      {errors.length > 0 && (
        <ul className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}

      {warnings.length > 0 && (
        <ul className="rounded-md border border-amber-300 bg-amber-50 p-3 text-sm text-amber-700">
          {warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      {status && (
        <p className="rounded-md border border-green-300 bg-green-50 p-3 text-sm text-green-700">
          {status}
        </p>
      )}

      <button
        type="button"
        onClick={handleExport}
        disabled={busy}
        className="rounded-md bg-foreground px-4 py-2 text-sm font-semibold text-background disabled:opacity-50"
      >
        {busy ? "Экспорт..." : "Экспортировать VR/AR витрину"}
      </button>
    </div>
  );
}
