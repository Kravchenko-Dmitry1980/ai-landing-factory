"use client";

import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowHeroMode } from "@/lib/wowHeroMode";
import { WowHeroBackdrop } from "./WowHeroBackdrop";
import { WowHeroOverlay } from "./WowHeroOverlay";
import { WowHeroMascot } from "./WowHeroMascot";

interface Props {
  data: WowHeroData;
  mode: WowHeroMode;
  /** Why the static fallback is shown — surfaced as a small badge for QA. */
  reason?: "no-webgl" | "reduced-motion" | "loading";
}

/**
 * Static WOW hero fallback (Stage P.7.6).
 *
 * Same light 2D composition as the live hero — used while hydrating or when
 * JavaScript is unavailable. No WebGL constellation or portal decor.
 */
export function WowHeroFallback({ data, mode, reason }: Props) {
  return (
    <div className="wow-hero-stage wow-hero-stage--static" data-reason={reason ?? ""}>
      <WowHeroBackdrop />
      <WowHeroOverlay data={data} mode={mode} />
      <WowHeroMascot />
    </div>
  );
}
