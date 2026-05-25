"use client";

import type { LayoutPresetId } from "@/design/layout_presets";
import { LAYOUT_PRESETS } from "@/design/layout_presets";
import type { StyleProfileId } from "@/design/style_profiles";
import { STYLE_PROFILES } from "@/design/style_profiles";
import { saveRenderConfig } from "@/rendering/contract_adapter";
import type { RenderConfig, RenderPlan } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
  renderMs: number;
  config: RenderConfig;
  projectId: string;
  onConfigChange?: (config: RenderConfig) => void;
}

export function DevRenderPanel({
  plan,
  renderMs,
  config,
  projectId,
  onConfigChange,
}: Props) {
  function update(partial: Partial<RenderConfig>) {
    const next = { ...config, ...partial };
    saveRenderConfig(projectId, next);
    onConfigChange?.(next);
  }

  return (
    <aside
      className="fixed bottom-4 right-4 z-50 max-h-[70vh] w-80 overflow-auto rounded-lg border border-[var(--alf-border)] bg-[var(--alf-bg)] p-4 text-xs shadow-md print:hidden"
      aria-label="Developer render panel"
    >
      <p className="font-semibold text-[var(--alf-text)]">Stage D — Dev panel</p>
      <p className="mt-1 text-[var(--alf-text-muted)]">Render: {renderMs}ms</p>

      <label className="mt-3 block">
        <span className="text-[var(--alf-text-muted)]">Style profile</span>
        <select
          className="mt-1 w-full rounded border border-[var(--alf-border)] bg-[var(--alf-surface)] p-1.5"
          value={config.profileId}
          onChange={(e) =>
            update({ profileId: e.target.value as StyleProfileId })
          }
        >
          {Object.keys(STYLE_PROFILES).map((id) => (
            <option key={id} value={id}>
              {id}
            </option>
          ))}
        </select>
      </label>

      <label className="mt-3 block">
        <span className="text-[var(--alf-text-muted)]">Layout preset</span>
        <select
          className="mt-1 w-full rounded border border-[var(--alf-border)] bg-[var(--alf-surface)] p-1.5"
          value={config.layoutId}
          onChange={(e) =>
            update({ layoutId: e.target.value as LayoutPresetId })
          }
        >
          {Object.keys(LAYOUT_PRESETS).map((id) => (
            <option key={id} value={id}>
              {LAYOUT_PRESETS[id as LayoutPresetId].label}
            </option>
          ))}
        </select>
      </label>

      <div className="mt-3">
        <p className="font-medium text-[var(--alf-text)]">Section tree</p>
        <ul className="mt-1 space-y-0.5 text-[var(--alf-text-muted)]">
          {plan.sections.map((s) => (
            <li key={s.id}>
              {s.type} ← {s.sourceKeys.join(", ") || "meta"}
            </li>
          ))}
        </ul>
      </div>

      <div className="mt-3">
        <p className="font-medium text-[var(--alf-text)]">Hallmark warnings</p>
        {plan.hallmarkViolations.length === 0 ? (
          <p className="text-emerald-700">None</p>
        ) : (
          <ul className="mt-1 space-y-1">
            {plan.hallmarkViolations.map((v) => (
              <li key={v.ruleId} className="text-amber-800">
                [{v.severity}] {v.ruleId}
              </li>
            ))}
          </ul>
        )}
      </div>
    </aside>
  );
}
