/**
 * R3F WOW hero scene for the Interactive WOW Bundle (Stage P.7.2).
 *
 * A full-screen background scene: a central glowing AI core, orbiting module
 * nodes (colored by kind), animated data pulses (beams), a particle star field
 * and a spatial grid floor, with subtle mouse/camera parallax. The scene is
 * derived from real project data (module nodes), never random decoration.
 *
 * Imports only `three` + `@react-three/fiber` (no drei) to keep the offline
 * bundle small and free of any external font/CDN fetch.
 */

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import * as THREE from "three";
import { NODE_KIND_COLOR, type WowSceneNode } from "./WowBundleData";

interface SceneProps {
  nodes: WowSceneNode[];
  accent: string;
  reducedMotion: boolean;
}

const ORBIT_RADIUS = 4.2;

function nodePositions(count: number): THREE.Vector3[] {
  const out: THREE.Vector3[] = [];
  for (let i = 0; i < count; i += 1) {
    const angle = (i / Math.max(count, 1)) * Math.PI * 2;
    const y = Math.sin(i * 1.7) * 0.9;
    out.push(
      new THREE.Vector3(
        Math.cos(angle) * ORBIT_RADIUS,
        y,
        Math.sin(angle) * ORBIT_RADIUS,
      ),
    );
  }
  return out;
}

function Core({ accent, reducedMotion }: { accent: string; reducedMotion: boolean }) {
  const inner = useRef<THREE.Mesh>(null);
  const wire = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (reducedMotion) return;
    const t = state.clock.elapsedTime;
    const pulse = 1 + Math.sin(t * 1.4) * 0.06;
    if (inner.current) inner.current.scale.setScalar(pulse);
    if (wire.current) {
      wire.current.rotation.y = t * 0.25;
      wire.current.rotation.x = t * 0.12;
    }
  });

  return (
    <group>
      <mesh ref={inner}>
        <icosahedronGeometry args={[1.05, 1]} />
        <meshStandardMaterial
          color={accent}
          emissive={accent}
          emissiveIntensity={1.4}
          roughness={0.25}
          metalness={0.6}
        />
      </mesh>
      <mesh ref={wire} scale={1.5}>
        <icosahedronGeometry args={[1.05, 1]} />
        <meshBasicMaterial color={accent} wireframe transparent opacity={0.35} />
      </mesh>
      <pointLight color={accent} intensity={3.2} distance={18} position={[0, 0, 0]} />
    </group>
  );
}

function Node({
  node,
  position,
  reducedMotion,
}: {
  node: WowSceneNode;
  position: THREE.Vector3;
  reducedMotion: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null);
  const color = NODE_KIND_COLOR[node.kind];

  useFrame((state) => {
    if (reducedMotion || !ref.current) return;
    const t = state.clock.elapsedTime;
    ref.current.position.y = position.y + Math.sin(t * 1.1 + position.x) * 0.25;
  });

  return (
    <mesh ref={ref} position={position}>
      <sphereGeometry args={[0.42, 24, 24]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.7}
        roughness={0.3}
        metalness={0.4}
      />
    </mesh>
  );
}

function Beam({
  position,
  accent,
  phase,
  reducedMotion,
}: {
  position: THREE.Vector3;
  accent: string;
  phase: number;
  reducedMotion: boolean;
}) {
  const ref = useRef<THREE.Mesh>(null);

  useFrame((state) => {
    if (!ref.current) return;
    const t = reducedMotion ? 0.5 : (state.clock.elapsedTime * 0.45 + phase) % 1;
    ref.current.position.set(
      position.x * (1 - t),
      position.y * (1 - t),
      position.z * (1 - t),
    );
    const mat = ref.current.material as THREE.MeshBasicMaterial;
    mat.opacity = reducedMotion ? 0.6 : 0.3 + Math.sin(t * Math.PI) * 0.6;
  });

  return (
    <mesh ref={ref}>
      <sphereGeometry args={[0.12, 12, 12]} />
      <meshBasicMaterial color={accent} transparent opacity={0.7} />
    </mesh>
  );
}

function StarField({ reducedMotion }: { reducedMotion: boolean }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const count = 700;
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      const r = 16 + Math.random() * 26;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      arr[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      arr[i * 3 + 1] = r * Math.cos(phi) * 0.6;
      arr[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta);
    }
    return arr;
  }, []);

  useFrame((state) => {
    if (reducedMotion || !ref.current) return;
    ref.current.rotation.y = state.clock.elapsedTime * 0.01;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.08} color="#9fb0ff" transparent opacity={0.7} sizeAttenuation />
    </points>
  );
}

function Scene({ nodes, accent, reducedMotion }: SceneProps) {
  const group = useRef<THREE.Group>(null);
  const positions = useMemo(() => nodePositions(nodes.length), [nodes.length]);
  const { camera } = useThree();

  useFrame((state) => {
    if (group.current && !reducedMotion) {
      group.current.rotation.y = state.clock.elapsedTime * 0.08;
    }
    if (!reducedMotion) {
      const targetX = state.pointer.x * 1.6;
      const targetY = 0.6 + state.pointer.y * 1.0;
      camera.position.x += (targetX - camera.position.x) * 0.04;
      camera.position.y += (targetY - camera.position.y) * 0.04;
      camera.lookAt(0, 0, 0);
    }
  });

  return (
    <>
      <color attach="background" args={["#05060f"]} />
      <fog attach="fog" args={["#05060f", 12, 40]} />
      <ambientLight intensity={0.35} />
      <directionalLight position={[6, 8, 4]} intensity={0.6} />
      <StarField reducedMotion={reducedMotion} />
      <gridHelper
        args={[60, 60, accent, "#1a1d3a"]}
        position={[0, -4.5, 0]}
      />
      <Core accent={accent} reducedMotion={reducedMotion} />
      <group ref={group}>
        {nodes.map((node, i) => (
          <group key={node.id}>
            <Node node={node} position={positions[i]} reducedMotion={reducedMotion} />
            <Beam
              position={positions[i]}
              accent={accent}
              phase={i / Math.max(nodes.length, 1)}
              reducedMotion={reducedMotion}
            />
          </group>
        ))}
      </group>
    </>
  );
}

export default function WowBundleRenderer({ nodes, accent, reducedMotion }: SceneProps) {
  return (
    <Canvas
      className="wow-bundle-canvas"
      dpr={[1, 1.8]}
      camera={{ position: [0, 0.6, 11], fov: 52 }}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <Scene nodes={nodes} accent={accent} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
