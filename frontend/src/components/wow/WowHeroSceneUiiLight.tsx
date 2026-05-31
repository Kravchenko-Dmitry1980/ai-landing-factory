"use client";

import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowSceneIntensity } from "@/lib/wowHeroMode";
import { UII_LIGHT } from "./uiiLight";
import { WowSceneLighting } from "./WowSceneLighting";
import { WowAmbientDecor } from "./WowAmbientDecor";

interface SceneProps {
  data: WowHeroData;
  intensity: WowSceneIntensity;
  reducedMotion: boolean;
  accent: string;
}

/**
 * UII Light ambient backdrop (Stage P.7.6).
 *
 * Sparkles and soft particles only — no portal arch, no 3D floating cards.
 * The cat mascot is rendered as an HTML/CSS image layer outside this canvas.
 */
export function WowHeroSceneUiiLight({ intensity, reducedMotion, accent }: SceneProps) {
  const sceneAccent = accent || UII_LIGHT.accent;
  const full = intensity === "full";

  return (
    <>
      <color attach="background" args={[UII_LIGHT.bg]} />
      <fog attach="fog" args={[UII_LIGHT.bg, 14, 30]} />
      <WowSceneLighting accent={sceneAccent} />
      <WowAmbientDecor accent={sceneAccent} reducedMotion={reducedMotion} full={full} />
    </>
  );
}
