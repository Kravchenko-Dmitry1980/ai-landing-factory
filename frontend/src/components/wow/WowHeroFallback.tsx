"use client";

import type { WowHeroData } from "@/lib/wowHeroMapping";
import { NODE_KIND_COLOR } from "@/lib/wowHeroMapping";
import type { WowHeroMode } from "@/lib/wowHeroMode";
import { WowHeroOverlay } from "./WowHeroOverlay";

interface Props {
  data: WowHeroData;
  mode: WowHeroMode;
  /** Why the static fallback is shown — surfaced as a small badge for QA. */
  reason?: "no-webgl" | "reduced-motion" | "loading";
}

/**
 * Static, WebGL-free WOW hero (Stage P.7.1).
 *
 * Used when WebGL is unavailable, the user prefers reduced motion, or while the
 * 3D scene is still loading. It keeps the premium composition (holographic
 * backdrop, node constellation, full overlay) so the hero never collapses into
 * a blank rectangle.
 */
export function WowHeroFallback({ data, mode, reason }: Props) {
  const nodes = data.nodes.slice(0, 8);
  return (
    <div className="wow-hero-stage wow-hero-stage--static" data-reason={reason ?? ""}>
      <div className="wow-hero-backdrop" aria-hidden="true">
        <div className="wow-hero-aurora" />
        <div className="wow-hero-grid-floor" />
        <div className="wow-hero-core" />
        <ul className="wow-hero-constellation">
          {nodes.map((node, i) => {
            const angle = (i / Math.max(nodes.length, 1)) * Math.PI * 2;
            const radius = 38;
            const left = 50 + Math.cos(angle) * radius;
            const top = 50 + Math.sin(angle) * radius * 0.62;
            return (
              <li
                key={node.id}
                className="wow-hero-node"
                style={{
                  left: `${left}%`,
                  top: `${top}%`,
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  ["--wow-node-color" as any]: NODE_KIND_COLOR[node.kind],
                }}
              >
                <span className="wow-hero-node-dot" />
                <span className="wow-hero-node-label">{node.label}</span>
              </li>
            );
          })}
        </ul>
      </div>
      <WowHeroOverlay data={data} mode={mode} />
    </div>
  );
}
