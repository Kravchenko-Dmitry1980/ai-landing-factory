"use client";

import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowSceneIntensity } from "@/lib/wowHeroMode";
import { UII_LIGHT, layoutFloatingCards, makeRng } from "./uiiLight";
import { WowSceneLighting } from "./WowSceneLighting";
import { WowAssistantModel } from "./WowAssistantModel";
import { WowPhoneStage } from "./WowPhoneStage";
import { WowPortalArch } from "./WowPortalArch";
import { WowFloatingCards } from "./WowFloatingCards";
import { WowAmbientDecor } from "./WowAmbientDecor";

interface SceneProps {
  data: WowHeroData;
  intensity: WowSceneIntensity;
  reducedMotion: boolean;
  accent: string;
}

function seedFromData(data: WowHeroData): number {
  let h = 2166136261;
  const str = `${data.title}|${data.nodes.length}`;
  for (let i = 0; i < str.length; i += 1) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

/** Subtle cursor parallax wrapper (disabled under reduced motion). */
function ParallaxRig({
  children,
  reducedMotion,
}: {
  children: React.ReactNode;
  reducedMotion: boolean;
}) {
  const group = useRef<THREE.Group>(null);
  const { pointer } = useThree();
  useFrame(() => {
    if (!group.current || reducedMotion) return;
    const targetY = pointer.x * 0.18;
    const targetX = -pointer.y * 0.1;
    group.current.rotation.y += (targetY - group.current.rotation.y) * 0.05;
    group.current.rotation.x += (targetX - group.current.rotation.x) * 0.05;
  });
  return <group ref={group}>{children}</group>;
}

/**
 * UII Light 3D WOW hero scene (Stage P.7.2).
 *
 * A light, exhibition-grade "AI Learning Portal": a glossy AI assistant standing
 * on a smartphone/device stage, framed by a translucent glass portal arch, with
 * project-derived floating data cards and soft ambient decor. Replaces the old
 * dark sci-fi sphere/cube constellation. Fully procedural — no GLTF, no CDN.
 */
export function WowHeroSceneUiiLight({ data, intensity, reducedMotion, accent }: SceneProps) {
  const sceneAccent = accent || UII_LIGHT.accent;
  const rng = useMemo(() => makeRng(seedFromData(data)), [data]);
  const cards = useMemo(() => layoutFloatingCards(data.nodes, rng), [data.nodes, rng]);
  const full = intensity === "full";

  return (
    <>
      <color attach="background" args={[UII_LIGHT.bg]} />
      <fog attach="fog" args={[UII_LIGHT.bg, 14, 30]} />

      <WowSceneLighting accent={sceneAccent} />

      <ParallaxRig reducedMotion={reducedMotion}>
        <WowPortalArch accent={sceneAccent} reducedMotion={reducedMotion} />
        <WowAssistantModel accent={sceneAccent} reducedMotion={reducedMotion} />
        <WowPhoneStage accent={sceneAccent} reducedMotion={reducedMotion} />
        <WowFloatingCards cards={cards} reducedMotion={reducedMotion} />
        <WowAmbientDecor accent={sceneAccent} reducedMotion={reducedMotion} full={full} />
      </ParallaxRig>
    </>
  );
}
