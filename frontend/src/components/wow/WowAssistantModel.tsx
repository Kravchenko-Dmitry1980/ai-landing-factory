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
 * Stylized friendly AI assistant (Stage P.7.2).
 *
 * A glossy, low-poly desk robot built entirely from rounded boxes / spheres /
 * cylinders — no external GLTF, no CDN. Soft white shells, an emissive cyan
 * face screen with two eyes, and an antenna with a glowing tip. It gently bobs
 * and breathes; motion is disabled under reduced-motion.
 */
export function WowAssistantModel({ accent, reducedMotion }: Props) {
  const group = useRef<THREE.Group>(null);
  const eyeL = useRef<THREE.Mesh>(null);
  const eyeR = useRef<THREE.Mesh>(null);
  const tip = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (reducedMotion) return;
    const t = clock.elapsedTime;
    if (group.current) {
      group.current.position.y = Math.sin(t * 1.1) * 0.12;
      group.current.rotation.y = Math.sin(t * 0.4) * 0.18;
      group.current.rotation.z = Math.sin(t * 0.7) * 0.015;
    }
    // Occasional blink: squash the eyes briefly.
    const blink = Math.max(0, Math.sin(t * 1.7 - 1.2)) ** 18;
    const sy = 1 - blink * 0.85;
    if (eyeL.current) eyeL.current.scale.y = sy;
    if (eyeR.current) eyeR.current.scale.y = sy;
    if (tip.current) {
      const mat = tip.current.material as THREE.MeshStandardMaterial;
      mat.emissiveIntensity = 1.4 + Math.sin(t * 3) * 0.6;
    }
  });

  const shell = (emissive = 0.04) => (
    <meshStandardMaterial
      color={UII_LIGHT.shell}
      roughness={0.22}
      metalness={0.12}
      emissive={UII_LIGHT.lavender}
      emissiveIntensity={emissive}
    />
  );

  return (
    <group ref={group} position={[1.6, 0.25, 0]}>
      {/* Body */}
      <RoundedBox args={[1.25, 1.15, 0.78]} radius={0.26} smoothness={5} position={[0, -0.85, 0]} castShadow>
        {shell(0.06)}
      </RoundedBox>
      {/* Chest accent panel */}
      <RoundedBox args={[0.66, 0.46, 0.06]} radius={0.1} smoothness={4} position={[0, -0.78, 0.41]}>
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.5} roughness={0.3} metalness={0.4} />
      </RoundedBox>

      {/* Neck */}
      <mesh position={[0, -0.18, 0]}>
        <cylinderGeometry args={[0.16, 0.2, 0.2, 24]} />
        <meshStandardMaterial color={UII_LIGHT.shell2} roughness={0.3} metalness={0.2} />
      </mesh>

      {/* Head */}
      <RoundedBox args={[1.32, 1.0, 0.82]} radius={0.34} smoothness={6} position={[0, 0.5, 0]} castShadow>
        {shell(0.05)}
      </RoundedBox>

      {/* Face screen */}
      <RoundedBox args={[0.98, 0.62, 0.08]} radius={0.18} smoothness={5} position={[0, 0.52, 0.42]}>
        <meshStandardMaterial color={UII_LIGHT.ink} roughness={0.15} metalness={0.5} emissive="#16203a" emissiveIntensity={0.5} />
      </RoundedBox>
      {/* Eyes */}
      <mesh ref={eyeL} position={[-0.22, 0.55, 0.48]}>
        <capsuleGeometry args={[0.07, 0.12, 6, 16]} />
        <meshStandardMaterial color={UII_LIGHT.cyan} emissive={UII_LIGHT.cyan} emissiveIntensity={2.2} toneMapped={false} />
      </mesh>
      <mesh ref={eyeR} position={[0.22, 0.55, 0.48]}>
        <capsuleGeometry args={[0.07, 0.12, 6, 16]} />
        <meshStandardMaterial color={UII_LIGHT.cyan} emissive={UII_LIGHT.cyan} emissiveIntensity={2.2} toneMapped={false} />
      </mesh>
      {/* Smile */}
      <mesh position={[0, 0.34, 0.47]} rotation={[0, 0, 0]}>
        <torusGeometry args={[0.12, 0.018, 12, 24, Math.PI]} />
        <meshStandardMaterial color={UII_LIGHT.cyan} emissive={UII_LIGHT.cyan} emissiveIntensity={1.4} toneMapped={false} />
      </mesh>

      {/* Ears */}
      {[-0.74, 0.74].map((x) => (
        <mesh key={x} position={[x, 0.5, 0]}>
          <cylinderGeometry args={[0.12, 0.12, 0.16, 20]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.4} roughness={0.3} metalness={0.4} />
        </mesh>
      ))}

      {/* Antenna */}
      <mesh position={[0, 1.08, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.34, 12]} />
        <meshStandardMaterial color={UII_LIGHT.shell2} roughness={0.3} metalness={0.4} />
      </mesh>
      <mesh ref={tip} position={[0, 1.32, 0]}>
        <sphereGeometry args={[0.1, 20, 20]} />
        <meshStandardMaterial color={UII_LIGHT.cyan} emissive={UII_LIGHT.cyan} emissiveIntensity={1.8} toneMapped={false} />
      </mesh>

      {/* Arms */}
      {[-0.82, 0.82].map((x) => (
        <RoundedBox
          key={x}
          args={[0.22, 0.5, 0.24]}
          radius={0.1}
          smoothness={4}
          position={[x, -0.78, 0.12]}
          rotation={[0, 0, x > 0 ? -0.3 : 0.3]}
        >
          {shell(0.04)}
        </RoundedBox>
      ))}
    </group>
  );
}
