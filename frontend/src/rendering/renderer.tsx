"use client";

import { useEffect, useMemo, useState } from "react";
import { themeStyleObject } from "@/design/themes";
import { logHallmarkViolations } from "@/design/hallmark_rules";
import type { GeneratedLanding, GeneratedSemanticLanding, LandingContract } from "@/lib/types";
import { buildRenderPlan, loadRenderConfig } from "./contract_adapter";
import type { RenderConfig } from "./types";
import { createSectionTree } from "./section_factory";
import type { RenderPlan } from "./types";
import { DevRenderPanel } from "@/components/dev/DevRenderPanel";
import { FidelityDebugPanel } from "@/components/fidelity/FidelityDebugPanel";

interface Props {
  landing: GeneratedLanding;
  contract: LandingContract | null;
  projectId: string;
  semantic?: GeneratedSemanticLanding | null;
  config?: RenderConfig;
  onConfigChange?: (config: RenderConfig) => void;
  showDevPanel?: boolean;
  showFidelityDebug?: boolean;
}

export function InteractiveRenderer({
  landing,
  contract,
  projectId,
  semantic,
  config: configProp,
  onConfigChange,
  showDevPanel = false,
  showFidelityDebug = false,
}: Props) {
  const [renderMs, setRenderMs] = useState(0);
  const config =
    configProp ??
    loadRenderConfig(projectId, landing, contract);

  const plan: RenderPlan = useMemo(() => {
    const t0 = performance.now();
    const p = buildRenderPlan(landing, contract, config, semantic);
    setRenderMs(Math.round(performance.now() - t0));
    return p;
  }, [landing, contract, config, semantic]);

  useEffect(() => {
    logHallmarkViolations(plan.hallmarkViolations);
  }, [plan]);

  const sections = useMemo(() => createSectionTree(plan), [plan]);
  const gridClass =
    plan.layout.gridLogic === "dashboard-grid"
      ? ""
      : plan.layout.gridLogic === "two-column"
        ? ""
        : "";

  return (
    <div
      className={`alf-landing min-h-screen bg-[var(--alf-bg)] text-[var(--alf-text)] print:bg-white ${gridClass}`}
      style={themeStyleObject(plan.profile.tokens)}
      data-profile={plan.profileId}
      data-layout={plan.layoutId}
    >
      {showFidelityDebug && (
        <div className="mx-auto max-w-6xl px-4 pt-6 md:px-8">
          <FidelityDebugPanel diagnostics={plan.fidelityDiagnostics} />
        </div>
      )}
      <article className="pb-16 print:shadow-none">{sections}</article>
      {showDevPanel && (
        <DevRenderPanel
          plan={plan}
          renderMs={renderMs}
          config={config}
          projectId={projectId}
          onConfigChange={onConfigChange}
        />
      )}
    </div>
  );
}
