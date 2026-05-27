"use client";

import { useEffect, useMemo, useState } from "react";
import { heroModeClass, motionClass, cardStyleClass } from "@/design/applyThemeTokens";
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

  const motionCls = motionClass(plan.themeTokens.motion);
  const heroWrapperClass = heroModeClass(plan.themeTokens.hero_mode);
  const cardsCls = cardStyleClass(plan.profile.cardStyle);

  return (
    <div
      className={`alf-landing alf-interactive ${heroWrapperClass} ${cardsCls} min-h-screen scroll-smooth bg-[var(--alf-bg)] text-[var(--alf-text)] print:bg-white ${gridClass} ${motionCls}`}
      style={themeStyleObject(plan.cssVars)}
      data-profile={plan.profileId}
      data-layout={plan.layoutId}
      data-card-style={plan.profile.cardStyle}
      data-hero-mode={plan.themeTokens.hero_mode ?? "classic"}
    >
      <style>{`
        .alf-interactive .alf-card-lift {
          transition: transform var(--alf-motion-duration, 0.25s) ease,
            box-shadow var(--alf-motion-duration, 0.25s) ease;
        }
        .alf-interactive .alf-card-lift:hover {
          transform: translateY(-4px);
          box-shadow: 0 12px 28px rgba(15, 23, 42, 0.08);
        }
        .alf-cards--flat .alf-card-lift {
          box-shadow: none;
          border-color: var(--alf-border);
        }
        .alf-cards--flat .alf-card-lift:hover {
          transform: none;
          box-shadow: none;
        }
        .alf-cards--outlined .alf-card-lift {
          border-width: 2px;
          box-shadow: none;
        }
        .alf-cards--glass .alf-card-lift {
          background: color-mix(in srgb, var(--alf-surface) 85%, transparent);
          backdrop-filter: blur(8px);
        }
        .alf-cards--soft .alf-card-lift {
          box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
        }
        .alf-interactive .alf-stack-tag {
          transition: background var(--alf-motion-duration, 0.25s) ease;
        }
        .alf-interactive .alf-stack-tag:hover {
          background: var(--alf-accent-muted);
        }
        .alf-hero--gradient header,
        .alf-hero--gradient .alf-hero-inner {
          background: linear-gradient(135deg, var(--alf-accent-muted) 0%, transparent 55%);
        }
        .alf-hero--bold header,
        .alf-hero--bold .alf-hero-inner {
          padding-top: 2rem;
          padding-bottom: 2rem;
        }
        .alf-hero--bold .alf-hero-inner h1 {
          letter-spacing: -0.02em;
        }
        .alf-hero--future-3d .alf-hero-inner {
          position: relative;
          isolation: isolate;
        }
        .alf-hero--future-3d .alf-hero-inner::before {
          content: "";
          position: absolute;
          inset: -12% -8% auto;
          height: 70%;
          background: linear-gradient(120deg, var(--alf-accent-muted), transparent 70%);
          transform: perspective(800px) rotateX(8deg);
          opacity: 0.85;
          z-index: -1;
          border-radius: var(--alf-radius, 8px);
        }
        /* future 3D hook — replace with WebGL/Three when enabled */
      `}</style>
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
