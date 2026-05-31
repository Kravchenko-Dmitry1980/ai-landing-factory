"use client";

import type { WowHeroMetric } from "@/lib/wowHeroMapping";

interface Props {
  metrics: WowHeroMetric[];
  compact?: boolean;
}

/**
 * Holographic metric cards for the WOW hero overlay (Stage P.7.1).
 *
 * Pure HTML/CSS so numbers stay crisp and screen-reader accessible, layered on
 * top of the 3D canvas.
 */
export function WowMetricStrip({ metrics, compact = false }: Props) {
  if (!metrics.length) return null;
  return (
    <ul
      className="wow-metric-strip"
      data-compact={compact ? "true" : "false"}
      aria-label="Ключевые показатели проекта"
    >
      {metrics.map((m) => (
        <li key={m.label} className="wow-metric-card">
          <span className="wow-metric-value">{m.value}</span>
          <span className="wow-metric-label">{m.label}</span>
          {m.hint && !compact && <span className="wow-metric-hint">{m.hint}</span>}
        </li>
      ))}
    </ul>
  );
}
