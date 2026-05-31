"use client";

import { ContactShadows } from "@react-three/drei";
import { UII_LIGHT } from "./uiiLight";

/**
 * Soft studio lighting for the UII Light 3D hero (Stage P.7.2).
 *
 * A bright, exhibition-style key light + cool fill + warm accent rim, plus a
 * grounded contact shadow so the assistant/device reads as a real exhibit on a
 * light pedestal (never a dark sci-fi void).
 */
export function WowSceneLighting({ accent }: { accent: string }) {
  return (
    <>
      <hemisphereLight args={["#ffffff", "#dfe4f6", 0.9]} />
      <ambientLight intensity={0.55} />
      <directionalLight
        position={[4.5, 7, 6]}
        intensity={1.15}
        color="#ffffff"
        castShadow
      />
      <directionalLight position={[-6, 2, -3]} intensity={0.5} color={UII_LIGHT.cyan} />
      <pointLight position={[2.5, 1.5, 3]} intensity={0.8} color={accent} distance={16} />
      <pointLight position={[-3, -1, 2]} intensity={0.45} color={UII_LIGHT.lavender} distance={14} />
      <ContactShadows
        position={[1.6, -2.35, 0]}
        opacity={0.32}
        scale={14}
        blur={2.6}
        far={5}
        resolution={512}
        color="#5b53a8"
      />
    </>
  );
}
