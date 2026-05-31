"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import { UII_LIGHT } from "./uiiLight";

interface Props {
  accent: string;
  reducedMotion: boolean;
}

/**
 * Smartphone / device platform pedestal (Stage P.7.2).
 *
 * A glossy tilted phone acting as the base "stage" under the assistant, with
 * layered glowing UI plates floating just above its screen — the digital-stand
 * / product-reveal motif of the УИИ visual language. Plates drift subtly.
 */
export function WowPhoneStage({ accent, reducedMotion }: Props) {
  const plates = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (reducedMotion || !plates.current) return;
    const t = clock.elapsedTime;
    plates.current.children.forEach((child, i) => {
      child.position.y = 0.08 + Math.sin(t * 1.3 + i * 1.1) * 0.04;
    });
  });

  return (
    <group position={[1.55, -1.75, 0.3]} rotation={[-0.62, -0.2, 0]}>
      {/* Phone body */}
      <RoundedBox args={[2.6, 5.0, 0.28]} radius={0.4} smoothness={6} castShadow>
        <meshStandardMaterial color={UII_LIGHT.shell} roughness={0.18} metalness={0.3} />
      </RoundedBox>
      {/* Screen */}
      <RoundedBox args={[2.3, 4.6, 0.06]} radius={0.3} smoothness={5} position={[0, 0, 0.16]}>
        <meshStandardMaterial
          color="#eef2ff"
          roughness={0.1}
          metalness={0.1}
          emissive={UII_LIGHT.lavender}
          emissiveIntensity={0.3}
        />
      </RoundedBox>

      {/* Floating interface plates above the screen */}
      <group ref={plates} position={[0, 0, 0.2]}>
        {[
          { y: 1.4, w: 1.9, h: 0.5, c: accent, e: 0.55 },
          { y: 0.55, w: 1.5, h: 0.42, c: UII_LIGHT.cyan, e: 0.7 },
          { y: -0.35, w: 1.8, h: 0.42, c: UII_LIGHT.purple, e: 0.5 },
          { y: -1.25, w: 1.3, h: 0.4, c: UII_LIGHT.cyan, e: 0.6 },
        ].map((p, i) => (
          <RoundedBox key={i} args={[p.w, p.h, 0.08]} radius={0.12} smoothness={4} position={[i % 2 ? 0.2 : -0.2, p.y, i * 0.05]}>
            <meshStandardMaterial
              color={p.c}
              emissive={p.c}
              emissiveIntensity={p.e}
              roughness={0.25}
              metalness={0.3}
              transparent
              opacity={0.92}
            />
          </RoundedBox>
        ))}
      </group>
    </group>
  );
}
