"use client";

import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowSceneIntensity } from "@/lib/wowHeroMode";
import { WowHeroSceneUiiLight } from "./WowHeroSceneUiiLight";

interface SceneProps {
  data: WowHeroData;
  intensity: WowSceneIntensity;
  reducedMotion: boolean;
  accent: string;
}

/**
 * WOW 3D hero scene (rendered inside an R3F <Canvas> when used).
 *
 * Stage P.7.6 keeps the scene ambient-only (sparkles). The cat mascot is an
 * HTML/CSS PNG layer; portal arch and 3D floating cards are removed.
 */
export function WowHeroScene({ data, intensity, reducedMotion, accent }: SceneProps) {
  return (
    <WowHeroSceneUiiLight
      data={data}
      intensity={intensity}
      reducedMotion={reducedMotion}
      accent={accent}
    />
  );
}
