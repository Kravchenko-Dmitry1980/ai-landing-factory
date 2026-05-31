"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Sparkles } from "@react-three/drei";
import * as THREE from "three";
import { UII_LIGHT } from "./uiiLight";

interface Props {
  accent: string;
  reducedMotion: boolean;
  full: boolean;
}

/**
 * Ambient light decor for the UII Light scene (Stage P.7.2).
 *
 * Soft drifting sparkles + faint concentric ground rings on a light pedestal —
 * a clean, premium "exhibition floor" feel (no dark sci-fi grid, no neon).
 */
export function WowAmbientDecor({ accent, reducedMotion, full }: Props) {
  const rings = useRef<THREE.Group>(null);
  const ringGeometries = useMemo(() => [2.2, 3.1, 4.0], []);

  useFrame(({ clock }) => {
    if (reducedMotion || !rings.current) return;
    rings.current.rotation.z = clock.elapsedTime * 0.04;
  });

  return (
    <group>
      <Sparkles
        count={full ? 60 : 30}
        scale={[12, 7, 6]}
        position={[1.4, 0.5, 0]}
        size={3}
        speed={reducedMotion ? 0 : 0.3}
        opacity={0.55}
        color={accent}
      />
      <group ref={rings} position={[1.6, -2.32, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        {ringGeometries.map((r) => (
          <mesh key={r}>
            <ringGeometry args={[r - 0.012, r, 96]} />
            <meshBasicMaterial color={UII_LIGHT.purple} transparent opacity={0.16} side={THREE.DoubleSide} />
          </mesh>
        ))}
      </group>
    </group>
  );
}
