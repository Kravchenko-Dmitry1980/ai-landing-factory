"use client";

import { useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
} from "@/lib/types";
import { buildWowHeroData } from "@/lib/wowHeroMapping";
import {
  isWebGLAvailable,
  prefersReducedMotion,
  sceneIntensity,
  type WowHeroMode,
} from "@/lib/wowHeroMode";
import { WowHeroOverlay } from "./WowHeroOverlay";
import { WowHeroFallback } from "./WowHeroFallback";
import "./wow-hero.css";

const WowHeroR3F = dynamic(() => import("./WowHeroR3F"), {
  ssr: false,
  loading: () => null,
});

interface Props {
  landing: GeneratedLanding;
  contract: LandingContract | null;
  semantic: GeneratedSemanticLanding | null;
  mode: WowHeroMode;
  /** Accent color (hex) resolved from the active theme. */
  accent?: string;
}

type Capability = "pending" | "webgl" | "fallback";

/**
 * Top-level WOW hero (Stage P.7.1).
 *
 * Resolves project data into a deterministic scene, then either mounts the R3F
 * 3D canvas (with an accessible HTML overlay) or a static premium fallback when
 * WebGL is unavailable. SSR renders the static fallback so the hero text is
 * always present for LCP / no-JS / assistive tech.
 */
export function WowHeroCanvas({ landing, contract, semantic, mode, accent = "#7c8bff" }: Props) {
  const data = useMemo(
    () => buildWowHeroData(landing, contract, semantic),
    [landing, contract, semantic],
  );
  const intensity = sceneIntensity(mode);

  const [capability, setCapability] = useState<Capability>("pending");
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    setReducedMotion(prefersReducedMotion());
    setCapability(isWebGLAvailable() ? "webgl" : "fallback");
  }, []);

  if (capability === "pending") {
    return <WowHeroFallback data={data} mode={mode} reason="loading" />;
  }

  if (capability === "fallback") {
    return <WowHeroFallback data={data} mode={mode} reason="no-webgl" />;
  }

  return (
    <section
      className="wow-hero-stage wow-hero-stage--live"
      data-mode={mode}
      data-reduced-motion={reducedMotion ? "true" : "false"}
      aria-label="WOW 3D hero"
    >
      <div className="wow-hero-canvas-layer" aria-hidden="true">
        <WowHeroR3F
          data={data}
          intensity={intensity}
          reducedMotion={reducedMotion}
          accent={accent}
        />
      </div>
      <WowHeroOverlay data={data} mode={mode} />
    </section>
  );
}
