"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import { Float, RoundedBox } from "@react-three/drei";
import * as THREE from "three";
import type { FloatingCardLayout } from "./uiiLight";
import { UII_LIGHT } from "./uiiLight";

interface Props {
  cards: FloatingCardLayout[];
  reducedMotion: boolean;
}

function Card({ card, reducedMotion }: { card: FloatingCardLayout; reducedMotion: boolean }) {
  const glow = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (reducedMotion || !glow.current) return;
    const mat = glow.current.material as THREE.MeshStandardMaterial;
    mat.emissiveIntensity = 0.6 + Math.sin(clock.elapsedTime * 2 + card.phase) * 0.3;
  });

  return (
    <Float
      enabled={!reducedMotion}
      speed={1.6}
      rotationIntensity={0.25}
      floatIntensity={0.7}
      position={card.position}
    >
      <group rotation={card.rotation} scale={card.scale}>
        {/* Glass card body */}
        <RoundedBox args={[1.25, 0.78, 0.06]} radius={0.1} smoothness={4}>
          <meshPhysicalMaterial
            color={UII_LIGHT.shell}
            roughness={0.12}
            metalness={0.1}
            transmission={0.55}
            thickness={0.4}
            transparent
            opacity={0.9}
          />
        </RoundedBox>
        {/* Accent header bar */}
        <mesh ref={glow} position={[-0.28, 0.24, 0.04]}>
          <boxGeometry args={[0.5, 0.12, 0.02]} />
          <meshStandardMaterial color={card.color} emissive={card.color} emissiveIntensity={0.7} toneMapped={false} />
        </mesh>
        {/* Mini "content" lines */}
        {[0.02, -0.14, -0.28].map((y, i) => (
          <mesh key={y} position={[-0.1 + i * 0.02, y, 0.04]}>
            <boxGeometry args={[0.78 - i * 0.18, 0.05, 0.01]} />
            <meshStandardMaterial color={UII_LIGHT.lavender} roughness={0.4} />
          </mesh>
        ))}
      </group>
    </Float>
  );
}

/**
 * Floating data / metric cards (Stage P.7.2).
 *
 * Glassy holographic panels hovering around the assistant — one per project
 * module/node — to make the scene read as a data-driven AI exhibit rather than
 * generic decoration. Textual numbers live in the HTML overlay (crisp + a11y).
 */
export function WowFloatingCards({ cards, reducedMotion }: Props) {
  return (
    <group>
      {cards.map((card, i) => (
        <Card key={i} card={card} reducedMotion={reducedMotion} />
      ))}
    </group>
  );
}
