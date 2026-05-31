"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { MeshTransmissionMaterial } from "@react-three/drei";
import * as THREE from "three";
import { UII_LIGHT } from "./uiiLight";

interface Props {
  accent: string;
  reducedMotion: boolean;
}

/**
 * Portal / arch / gateway behind the assistant (Stage P.7.2).
 *
 * A large translucent glass arch (the "AI portal" of the УИИ visual language)
 * with a slim glowing accent ring, framing the hero composition like an
 * exhibition gateway. Slowly counter-rotates for a premium, living feel.
 */
export function WowPortalArch({ accent, reducedMotion }: Props) {
  const glass = useRef<THREE.Mesh>(null);
  const ring = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (reducedMotion) return;
    const t = clock.elapsedTime;
    if (glass.current) glass.current.rotation.z = Math.sin(t * 0.15) * 0.08;
    if (ring.current) ring.current.rotation.z = -t * 0.12;
  });

  return (
    <group position={[1.6, 0.1, -1.7]}>
      {/* Glass arch */}
      <mesh ref={glass}>
        <torusGeometry args={[3.0, 0.42, 32, 80]} />
        <MeshTransmissionMaterial
          thickness={0.6}
          roughness={0.08}
          transmission={1}
          ior={1.25}
          chromaticAberration={0.04}
          backside
          color={UII_LIGHT.lavender}
          background={new THREE.Color(UII_LIGHT.bg)}
          samples={6}
        />
      </mesh>
      {/* Inner glowing accent ring */}
      <mesh ref={ring} position={[0, 0, 0.1]}>
        <torusGeometry args={[2.5, 0.04, 16, 96]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={1.6} toneMapped={false} />
      </mesh>
      {/* Soft halo disc behind everything */}
      <mesh position={[0, 0, -0.6]}>
        <circleGeometry args={[2.7, 64]} />
        <meshBasicMaterial color={UII_LIGHT.lavender} transparent opacity={0.18} />
      </mesh>
    </group>
  );
}
