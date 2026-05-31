"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Sparkles } from "@react-three/drei";
import type * as THREE from "three";

interface Props {
  accent: string;
  reducedMotion: boolean;
  full: boolean;
}

/**
 * Ambient sparkles for optional R3F backdrop (Stage P.7.6).
 *
 * No ground rings or portal geometry — keeps the scene airy and non-competing
 * with the HTML/CSS cat mascot layer.
 */
export function WowAmbientDecor({ accent, reducedMotion, full }: Props) {
  const group = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (reducedMotion || !group.current) return;
    group.current.rotation.y = clock.elapsedTime * 0.02;
  });

  return (
    <group ref={group}>
      <Sparkles
        count={full ? 40 : 24}
        scale={[12, 7, 6]}
        position={[1.4, 0.5, 0]}
        size={2.5}
        speed={reducedMotion ? 0 : 0.25}
        opacity={0.4}
        color={accent}
      />
    </group>
  );
}
