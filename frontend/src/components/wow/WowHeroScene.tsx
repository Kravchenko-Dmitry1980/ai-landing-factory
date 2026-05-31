"use client";

import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import { Float, Line } from "@react-three/drei";
import * as THREE from "three";
import type { WowHeroData, WowHeroNode } from "@/lib/wowHeroMapping";
import { NODE_KIND_COLOR } from "@/lib/wowHeroMapping";
import type { WowSceneIntensity } from "@/lib/wowHeroMode";

interface SceneProps {
  data: WowHeroData;
  intensity: WowSceneIntensity;
  reducedMotion: boolean;
  accent: string;
}

/** Deterministic PRNG (mulberry32) so the scene layout is stable per project. */
function makeRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function seedFromData(data: WowHeroData): number {
  let h = 2166136261;
  const str = `${data.title}|${data.nodes.length}|${data.pipeline.length}`;
  for (let i = 0; i < str.length; i += 1) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

interface NodeLayout {
  node: WowHeroNode;
  position: [number, number, number];
}

function layoutNodes(data: WowHeroData, rng: () => number): NodeLayout[] {
  const count = data.nodes.length;
  const rx = 3.6;
  const ry = 2.1;
  return data.nodes.map((node, i) => {
    const angle = (i / Math.max(count, 1)) * Math.PI * 2 + rng() * 0.25;
    const depth = (rng() - 0.5) * 2.2;
    const lift = Math.sin(angle * 1.5) * 0.6 + (rng() - 0.5) * 0.6;
    return {
      node,
      position: [Math.cos(angle) * rx, lift + Math.sin(angle) * ry * 0.35, Math.sin(angle) * 1.6 + depth],
    };
  });
}

function CoreCluster({ accent, reducedMotion }: { accent: string; reducedMotion: boolean }) {
  const inner = useRef<THREE.Mesh>(null);
  const wire = useRef<THREE.Mesh>(null);
  useFrame((_, delta) => {
    if (reducedMotion) return;
    if (wire.current) {
      wire.current.rotation.y += delta * 0.25;
      wire.current.rotation.x += delta * 0.12;
    }
    if (inner.current) inner.current.rotation.y -= delta * 0.18;
  });
  return (
    <group>
      <mesh ref={inner}>
        <icosahedronGeometry args={[0.9, 1]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={1.4}
          roughness={0.25}
          metalness={0.6}
        />
      </mesh>
      <mesh ref={wire} scale={1.7}>
        <icosahedronGeometry args={[0.9, 1]} />
        <meshBasicMaterial color={accent} wireframe transparent opacity={0.28} />
      </mesh>
      <pointLight position={[0, 0, 0]} color={accent} intensity={2.4} distance={12} />
    </group>
  );
}

function NodeMesh({ layout, reducedMotion }: { layout: NodeLayout; reducedMotion: boolean }) {
  const color = NODE_KIND_COLOR[layout.node.kind];
  return (
    <Float
      enabled={!reducedMotion}
      speed={1.4}
      rotationIntensity={0.5}
      floatIntensity={0.9}
      position={layout.position}
    >
      <mesh castShadow>
        <boxGeometry args={[0.62, 0.62, 0.62]} />
        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={0.7}
          roughness={0.3}
          metalness={0.5}
          transparent
          opacity={0.92}
        />
      </mesh>
      <mesh scale={1.18}>
        <boxGeometry args={[0.62, 0.62, 0.62]} />
        <meshBasicMaterial color={color} wireframe transparent opacity={0.35} />
      </mesh>
    </Float>
  );
}

function DataBeam({
  target,
  accent,
  offset,
  reducedMotion,
}: {
  target: [number, number, number];
  accent: string;
  offset: number;
  reducedMotion: boolean;
}) {
  const pulse = useRef<THREE.Mesh>(null);
  const dir = useMemo(() => new THREE.Vector3(...target), [target]);
  useFrame(({ clock }) => {
    if (!pulse.current) return;
    const t = reducedMotion ? 0.5 : ((clock.elapsedTime * 0.35 + offset) % 1);
    pulse.current.position.set(dir.x * t, dir.y * t, dir.z * t);
  });
  return (
    <group>
      <Line
        points={[[0, 0, 0], target]}
        color={accent}
        lineWidth={1}
        transparent
        opacity={0.22}
      />
      <mesh ref={pulse}>
        <sphereGeometry args={[0.07, 10, 10]} />
        <meshBasicMaterial color={accent} transparent opacity={0.9} />
      </mesh>
    </group>
  );
}

function ParticleField({ count, accent }: { count: number; accent: string }) {
  const positions = useMemo(() => {
    const rng = makeRng(1337);
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      arr[i * 3] = (rng() - 0.5) * 18;
      arr[i * 3 + 1] = (rng() - 0.5) * 10;
      arr[i * 3 + 2] = (rng() - 0.5) * 12 - 3;
    }
    return arr;
  }, [count]);
  const ref = useRef<THREE.Points>(null);
  useFrame((_, delta) => {
    if (ref.current) ref.current.rotation.y += delta * 0.02;
  });
  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} />
      </bufferGeometry>
      <pointsMaterial color={accent} size={0.045} sizeAttenuation transparent opacity={0.6} />
    </points>
  );
}

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
    const targetY = pointer.x * 0.4;
    const targetX = -pointer.y * 0.25;
    group.current.rotation.y += (targetY - group.current.rotation.y) * 0.05;
    group.current.rotation.x += (targetX - group.current.rotation.x) * 0.05;
  });
  return <group ref={group}>{children}</group>;
}

/** The full WOW 3D hero scene (rendered inside an R3F <Canvas>). */
export function WowHeroScene({ data, intensity, reducedMotion, accent }: SceneProps) {
  const rng = useMemo(() => makeRng(seedFromData(data)), [data]);
  const layouts = useMemo(() => layoutNodes(data, rng), [data, rng]);
  const particleCount = intensity === "full" ? 260 : 90;

  return (
    <>
      <color attach="background" args={["#070b18"]} />
      <fog attach="fog" args={["#070b18", 9, 22]} />
      <ambientLight intensity={0.45} />
      <directionalLight position={[5, 6, 8]} intensity={0.8} color="#bcd0ff" />
      <pointLight position={[-6, -3, -4]} intensity={1.1} color="#7c3aed" distance={20} />

      <ParallaxRig reducedMotion={reducedMotion}>
        <CoreCluster accent={accent} reducedMotion={reducedMotion} />
        {layouts.map((layout, i) => (
          <group key={layout.node.id}>
            <DataBeam
              target={layout.position}
              accent={accent}
              offset={i / Math.max(layouts.length, 1)}
              reducedMotion={reducedMotion}
            />
            <NodeMesh layout={layout} reducedMotion={reducedMotion} />
          </group>
        ))}
        <ParticleField count={particleCount} accent="#7aa2ff" />
        <gridHelper
          args={[30, 30, "#1e2a4a", "#141d33"]}
          position={[0, -3.4, 0]}
          rotation={[0, 0, 0]}
        />
      </ParallaxRig>
    </>
  );
}
