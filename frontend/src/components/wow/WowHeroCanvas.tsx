"use client";

import { useEffect, useMemo, useState } from "react";
import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
} from "@/lib/types";
import { buildWowHeroData } from "@/lib/wowHeroMapping";
import type { WowHeroMode } from "@/lib/wowHeroMode";
import { WowHeroBackdrop } from "./WowHeroBackdrop";
import { WowHeroOverlay } from "./WowHeroOverlay";
import { WowHeroFallback } from "./WowHeroFallback";
import { WowHeroMascot } from "./WowHeroMascot";
import "./wow-hero.css";

interface Props {
  landing: GeneratedLanding;
  contract: LandingContract | null;
  semantic: GeneratedSemanticLanding | null;
  mode: WowHeroMode;
  /** Accent color (hex) resolved from the active theme. */
  accent?: string;
}

/**
 * Top-level WOW hero (Stage P.7.6).
 *
 * Pure 2D landing with a cat mascot PNG on the right. No R3F portal rings or
 * heavy 3D scene — the hero text stays crisp and the mascot never overlaps copy.
 */
export function WowHeroCanvas({ landing, contract, semantic, mode }: Props) {
  const data = useMemo(
    () => buildWowHeroData(landing, contract, semantic),
    [landing, contract, semantic],
  );

  const [ready, setReady] = useState(false);

  useEffect(() => {
    setReady(true);
  }, []);

  if (!ready) {
    return <WowHeroFallback data={data} mode={mode} reason="loading" />;
  }

  return (
    <section
      className="wow-hero-stage wow-hero-stage--live"
      data-mode={mode}
      aria-label="WOW hero"
    >
      <WowHeroBackdrop />
      <WowHeroOverlay data={data} mode={mode} />
      <WowHeroMascot />
    </section>
  );
}
