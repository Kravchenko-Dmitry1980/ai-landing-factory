"use client";

import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowHeroMode } from "@/lib/wowHeroMode";
import { WowMetricStrip } from "./WowMetricStrip";

interface Props {
  data: WowHeroData;
  mode: WowHeroMode;
  /** Anchor id to scroll to when the primary CTA is pressed. */
  contentAnchor?: string;
}

/**
 * HTML overlay layered above the 3D canvas (Stage P.7.1).
 *
 * Per modern-web-guidance, interactive HTML content over a WebGL scene is best
 * composed as a CSS overlay (HTML-in-Canvas is not Baseline). This keeps text
 * readable, CTAs clickable, and content exposed to assistive tech.
 */
export function WowHeroOverlay({ data, mode, contentAnchor = "wow-landing-content" }: Props) {
  return (
    <div className="wow-hero-overlay">
      <div className="wow-hero-overlay-top">
        <span className="wow-hero-eyebrow">
          <span className="wow-hero-pulse" aria-hidden="true" />
          AI-витрина · {mode === "wow3d" ? "3D-экспонат" : "premium"}
        </span>

        <h1 className="wow-hero-title">{data.title}</h1>
        <p className="wow-hero-subtitle">{data.subtitle}</p>

        {data.chips.length > 0 && (
          <ul className="wow-hero-chips" aria-label="Контекст проекта">
            {data.chips.map((chip) => (
              <li key={chip.label} className="wow-hero-chip">
                <span className="wow-hero-chip-label">{chip.label}</span>
                <span className="wow-hero-chip-value">{chip.value}</span>
              </li>
            ))}
          </ul>
        )}

        <div className="wow-hero-cta">
          <a className="wow-cta-primary" href={`#${contentAnchor}`}>
            Смотреть лендинг
          </a>
          <a className="wow-cta-secondary" href="#wow-metrics">
            Показатели
          </a>
        </div>
      </div>

      <div className="wow-hero-overlay-bottom">
        <div id="wow-metrics" className="wow-hero-metrics-wrap">
          <WowMetricStrip metrics={data.metrics} />
        </div>

        {data.pipeline.length > 0 && (
          <ol className="wow-pipeline-rail" aria-label="Конвейер данных">
            {data.pipeline.map((stage, i) => (
              <li key={stage.id} className="wow-pipeline-stage">
                <span className="wow-pipeline-index">{i + 1}</span>
                <span className="wow-pipeline-title">{stage.title}</span>
                {stage.tags.length > 0 && (
                  <span className="wow-pipeline-tag">{stage.tags[0]}</span>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
