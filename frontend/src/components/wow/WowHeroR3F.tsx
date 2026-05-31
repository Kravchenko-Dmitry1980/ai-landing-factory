"use client";

import { Suspense } from "react";
import { Canvas } from "@react-three/fiber";
import type { WowHeroData } from "@/lib/wowHeroMapping";
import type { WowSceneIntensity } from "@/lib/wowHeroMode";
import { WowHeroScene } from "./WowHeroScene";

interface Props {
  data: WowHeroData;
  intensity: WowSceneIntensity;
  reducedMotion: boolean;
  accent: string;
}

/**
 * R3F <Canvas> wrapper (Stage P.7.1).
 *
 * Loaded only on the client via next/dynamic (ssr: false) so three.js stays out
 * of the server bundle and the standard preview path is never touched.
 */
export default function WowHeroR3F({ data, intensity, reducedMotion, accent }: Props) {
  return (
    <Canvas
      className="wow-hero-canvas"
      dpr={[1, 1.8]}
      camera={{ position: [0, 0.6, 9], fov: 50 }}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ antialias: true, powerPreference: "high-performance", alpha: false }}
    >
      <Suspense fallback={null}>
        <WowHeroScene
          data={data}
          intensity={intensity}
          reducedMotion={reducedMotion}
          accent={accent}
        />
      </Suspense>
    </Canvas>
  );
}
