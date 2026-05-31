"use client";

import type {
  ShowcaseConfig,
  ShowcaseLayout,
  ShowcaseTheme,
  ShowcaseUpdateRequest,
} from "@/lib/showcase";

export const LAYOUT_OPTIONS: { value: ShowcaseLayout; label: string }[] = [
  { value: "gallery_arc", label: "Дуга галереи" },
  { value: "grid_hall", label: "Зал-сетка" },
  { value: "circle_booths", label: "Круговые стенды" },
];

export const THEME_OPTIONS: { value: ShowcaseTheme; label: string }[] = [
  { value: "university", label: "Университет" },
  { value: "tech", label: "Технологичная" },
  { value: "dark", label: "Тёмная" },
];

const inputClass =
  "w-full rounded-md border border-input bg-background px-3 py-2 text-sm";

export function ShowcaseSettingsPanel({
  config,
  onChange,
  disabled,
}: {
  config: ShowcaseConfig;
  onChange: (patch: ShowcaseUpdateRequest) => void;
  disabled?: boolean;
}) {
  return (
    <section className="space-y-4 rounded-lg border p-4">
      <h2 className="text-lg font-semibold">Параметры витрины</h2>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Название витрины</span>
          <input
            className={inputClass}
            value={config.title}
            disabled={disabled}
            onChange={(e) => onChange({ title: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Подзаголовок</span>
          <input
            className={inputClass}
            value={config.subtitle ?? ""}
            disabled={disabled}
            onChange={(e) => onChange({ subtitle: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Организация</span>
          <input
            className={inputClass}
            value={config.organization ?? ""}
            disabled={disabled}
            onChange={(e) => onChange({ organization: e.target.value })}
          />
        </label>
        <label className="space-y-1 text-sm">
          <span className="text-muted-foreground">Макет сцены</span>
          <select
            className={inputClass}
            value={config.layout}
            disabled={disabled}
            onChange={(e) =>
              onChange({ layout: e.target.value as ShowcaseLayout })
            }
          >
            {LAYOUT_OPTIONS.map((l) => (
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
            disabled={disabled}
            onChange={(e) => onChange({ theme: e.target.value as ShowcaseTheme })}
          >
            {THEME_OPTIONS.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </section>
  );
}
