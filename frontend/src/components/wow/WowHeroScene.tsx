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
 * WOW 3D hero scene (rendered inside an R3F <Canvas>).
 *
 * Stage P.7.2 replaces the original dark sci-fi constellation with the light,
 * exhibition-grade "UII Light" composition (AI assistant + device stage + glass
 * portal arch + floating data cards). This module stays as the stable entry
 * point used by {@link WowHeroR3F}; the visual language lives in
 * {@link WowHeroSceneUiiLight}. `reducedMotion` is threaded through to disable
 * all animation when the user prefers it.
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
