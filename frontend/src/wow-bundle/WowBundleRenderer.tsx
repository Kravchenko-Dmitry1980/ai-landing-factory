/**
 * UII Light 3D WOW hero scene for the Interactive WOW Bundle (Stage P.7.2).
 *
 * A light, exhibition-grade "AI Learning Portal": a glossy stylized AI assistant
 * standing on a smartphone/device stage, framed by a glowing portal arch, with
 * project-derived floating data cards and soft ambient sparkles on a light
 * pedestal. Replaces the previous dark sci-fi core/orbit/starfield scene.
 *
 * Imports only `three` + `@react-three/fiber` (no drei) so the offline bundle
 * stays small and free of any external font/CDN fetch.
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

const PALETTE = {
  bg: "#f4f6fd",
  shell: "#ffffff",
  shell2: "#eef1fb",
  ink: "#1b1f3b",
  cyan: "#5dd6ff",
  lavender: "#d9ccff",
  purple: "#a78bfa",
};

const STAGE_X = 2.4;

function Assistant({ accent, reducedMotion }: { accent: string; reducedMotion: boolean }) {
  const group = useRef<THREE.Group>(null);
  const tip = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (reducedMotion) return;
    const t = clock.elapsedTime;
    if (group.current) {
      group.current.position.y = 0.3 + Math.sin(t * 1.1) * 0.14;
      group.current.rotation.y = Math.sin(t * 0.4) * 0.2;
    }
    if (tip.current) {
      (tip.current.material as THREE.MeshStandardMaterial).emissiveIntensity =
        1.4 + Math.sin(t * 3) * 0.6;
    }
  });

  return (
    <group ref={group} position={[STAGE_X, 0.3, 0]}>
      {/* Body */}
      <mesh position={[0, -1.0, 0]} castShadow>
        <boxGeometry args={[1.4, 1.3, 0.9]} />
        <meshStandardMaterial color={PALETTE.shell} roughness={0.22} metalness={0.12} />
      </mesh>
      {/* Chest panel */}
      <mesh position={[0, -0.95, 0.47]}>
        <boxGeometry args={[0.7, 0.5, 0.06]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.5} roughness={0.3} metalness={0.4} />
      </mesh>
      {/* Head */}
      <mesh position={[0, 0.45, 0]} castShadow>
        <boxGeometry args={[1.5, 1.15, 0.95]} />
        <meshStandardMaterial color={PALETTE.shell} roughness={0.22} metalness={0.12} />
      </mesh>
      {/* Face screen */}
      <mesh position={[0, 0.47, 0.49]}>
        <boxGeometry args={[1.1, 0.7, 0.06]} />
        <meshStandardMaterial color={PALETTE.ink} roughness={0.15} metalness={0.5} emissive="#16203a" emissiveIntensity={0.5} />
      </mesh>
      {/* Eyes */}
      {[-0.26, 0.26].map((x) => (
        <mesh key={x} position={[x, 0.5, 0.54]}>
          <sphereGeometry args={[0.1, 20, 20]} />
          <meshStandardMaterial color={PALETTE.cyan} emissive={PALETTE.cyan} emissiveIntensity={2.2} toneMapped={false} />
        </mesh>
      ))}
      {/* Ears */}
      {[-0.84, 0.84].map((x) => (
        <mesh key={x} position={[x, 0.45, 0]} rotation={[Math.PI / 2, 0, 0]}>
          <cylinderGeometry args={[0.14, 0.14, 0.18, 20]} />
          <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={0.4} roughness={0.3} metalness={0.4} />
        </mesh>
      ))}
      {/* Antenna */}
      <mesh position={[0, 1.1, 0]}>
        <cylinderGeometry args={[0.03, 0.03, 0.36, 12]} />
        <meshStandardMaterial color={PALETTE.shell2} roughness={0.3} metalness={0.4} />
      </mesh>
      <mesh ref={tip} position={[0, 1.36, 0]}>
        <sphereGeometry args={[0.12, 20, 20]} />
        <meshStandardMaterial color={PALETTE.cyan} emissive={PALETTE.cyan} emissiveIntensity={1.8} toneMapped={false} />
      </mesh>
    </group>
  );
}

function PhoneStage({ accent, reducedMotion }: { accent: string; reducedMotion: boolean }) {
  const plates = useRef<THREE.Group>(null);
  useFrame(({ clock }) => {
    if (reducedMotion || !plates.current) return;
    const t = clock.elapsedTime;
    plates.current.children.forEach((c, i) => {
      c.position.y = (c.userData.baseY as number) + Math.sin(t * 1.3 + i) * 0.05;
    });
  });

  const plateDefs = [
    { y: 1.4, w: 1.9, c: accent },
    { y: 0.5, w: 1.5, c: PALETTE.cyan },
    { y: -0.4, w: 1.8, c: PALETTE.purple },
    { y: -1.3, w: 1.3, c: PALETTE.cyan },
  ];

  return (
    <group position={[STAGE_X, -2.0, 0.3]} rotation={[-0.6, -0.18, 0]}>
      <mesh castShadow>
        <boxGeometry args={[2.8, 5.4, 0.3]} />
        <meshStandardMaterial color={PALETTE.shell} roughness={0.18} metalness={0.3} />
      </mesh>
      <mesh position={[0, 0, 0.17]}>
        <boxGeometry args={[2.5, 5.0, 0.05]} />
        <meshStandardMaterial color="#eef2ff" roughness={0.1} emissive={PALETTE.lavender} emissiveIntensity={0.3} />
      </mesh>
      <group ref={plates} position={[0, 0, 0.24]}>
        {plateDefs.map((p, i) => (
          <mesh key={i} position={[i % 2 ? 0.2 : -0.2, p.y, 0]} userData={{ baseY: p.y }}>
            <boxGeometry args={[p.w, 0.46, 0.06]} />
            <meshStandardMaterial color={p.c} emissive={p.c} emissiveIntensity={0.6} roughness={0.25} metalness={0.3} transparent opacity={0.92} />
          </mesh>
        ))}
      </group>
    </group>
  );
}

function PortalArch({ accent, reducedMotion }: { accent: string; reducedMotion: boolean }) {
  const ring = useRef<THREE.Mesh>(null);
  const glass = useRef<THREE.Mesh>(null);
  useFrame(({ clock }) => {
    if (reducedMotion) return;
    const t = clock.elapsedTime;
    if (ring.current) ring.current.rotation.z = -t * 0.12;
    if (glass.current) glass.current.rotation.z = Math.sin(t * 0.15) * 0.08;
  });
  return (
    <group position={[STAGE_X, 0.2, -2.0]}>
      <mesh ref={glass}>
        <torusGeometry args={[3.4, 0.46, 24, 64]} />
        <meshStandardMaterial color={PALETTE.lavender} roughness={0.12} metalness={0.2} transparent opacity={0.55} />
      </mesh>
      <mesh ref={ring} position={[0, 0, 0.1]}>
        <torusGeometry args={[2.8, 0.05, 16, 80]} />
        <meshStandardMaterial color={accent} emissive={accent} emissiveIntensity={1.6} toneMapped={false} />
      </mesh>
      <mesh position={[0, 0, -0.6]}>
        <circleGeometry args={[3.0, 64]} />
        <meshBasicMaterial color={PALETTE.lavender} transparent opacity={0.18} />
      </mesh>
    </group>
  );
}

function FloatingCards({ nodes, reducedMotion }: { nodes: WowSceneNode[]; reducedMotion: boolean }) {
  const group = useRef<THREE.Group>(null);
  const slots = useMemo<Array<[number, number, number]>>(
    () => [
      [-2.4, 1.7, 0.8],
      [-3.4, 0.0, 1.2],
      [-2.6, -1.6, 1.4],
      [-1.4, 2.6, 0.2],
      [6.6, 1.6, 0.6],
      [7.2, -0.2, 1.0],
      [6.2, -1.7, 1.2],
      [5.6, 2.6, 0.0],
    ],
    [],
  );

  useFrame(({ clock }) => {
    if (reducedMotion || !group.current) return;
    const t = clock.elapsedTime;
    group.current.children.forEach((c, i) => {
      c.position.y = (c.userData.baseY as number) + Math.sin(t * 1.4 + i * 0.7) * 0.18;
      c.rotation.z = Math.sin(t * 0.8 + i) * 0.05;
    });
  });

  return (
    <group ref={group}>
      {nodes.slice(0, slots.length).map((node, i) => {
        const [x, y, z] = slots[i];
        const color = NODE_KIND_COLOR[node.kind];
        return (
          <group key={node.id} position={[x, y, z]} rotation={[0, x > STAGE_X ? -0.35 : 0.35, 0]} userData={{ baseY: y }}>
            <mesh>
              <boxGeometry args={[1.3, 0.82, 0.06]} />
              <meshStandardMaterial color={PALETTE.shell} roughness={0.15} metalness={0.1} transparent opacity={0.9} />
            </mesh>
            <mesh position={[-0.28, 0.24, 0.05]}>
              <boxGeometry args={[0.52, 0.13, 0.02]} />
              <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.7} toneMapped={false} />
            </mesh>
            {[0.0, -0.16, -0.3].map((ly, li) => (
              <mesh key={ly} position={[-0.1 + li * 0.02, ly, 0.05]}>
                <boxGeometry args={[0.8 - li * 0.18, 0.06, 0.01]} />
                <meshStandardMaterial color={PALETTE.lavender} roughness={0.4} />
              </mesh>
            ))}
          </group>
        );
      })}
    </group>
  );
}

function Sparkles({ count, accent, reducedMotion }: { count: number; accent: string; reducedMotion: boolean }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      arr[i * 3] = STAGE_X + (Math.random() - 0.5) * 14;
      arr[i * 3 + 1] = (Math.random() - 0.4) * 9;
      arr[i * 3 + 2] = (Math.random() - 0.5) * 6;
    }
    return arr;
  }, [count]);

  useFrame(({ clock }) => {
    if (reducedMotion || !ref.current) return;
    ref.current.rotation.y = clock.elapsedTime * 0.03;
  });

  return (
    <points ref={ref}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[positions, 3]} count={positions.length / 3} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.09} color={accent} transparent opacity={0.6} sizeAttenuation />
    </points>
  );
}

function GroundRings() {
  return (
    <group position={[STAGE_X, -2.35, 0]} rotation={[-Math.PI / 2, 0, 0]}>
      {[2.6, 3.6, 4.6].map((r) => (
        <mesh key={r}>
          <ringGeometry args={[r - 0.015, r, 96]} />
          <meshBasicMaterial color={PALETTE.purple} transparent opacity={0.16} side={THREE.DoubleSide} />
        </mesh>
      ))}
    </group>
  );
}

function Scene({ nodes, accent, reducedMotion }: SceneProps) {
  const { camera } = useThree();

  useFrame((state) => {
    if (reducedMotion) return;
    const targetX = STAGE_X * 0.5 + state.pointer.x * 1.0;
    const targetY = 0.6 + state.pointer.y * 0.6;
    camera.position.x += (targetX - camera.position.x) * 0.04;
    camera.position.y += (targetY - camera.position.y) * 0.04;
    camera.lookAt(STAGE_X, 0, 0);
  });

  return (
    <>
      <color attach="background" args={[PALETTE.bg]} />
      <fog attach="fog" args={[PALETTE.bg, 16, 36]} />
      <hemisphereLight args={["#ffffff", "#dfe4f6", 0.9]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[5, 8, 6]} intensity={1.1} color="#ffffff" />
      <directionalLight position={[-6, 2, -3]} intensity={0.5} color={PALETTE.cyan} />
      <pointLight position={[STAGE_X + 2, 1.5, 3]} intensity={0.8} color={accent} distance={18} />

      <PortalArch accent={accent} reducedMotion={reducedMotion} />
      <Assistant accent={accent} reducedMotion={reducedMotion} />
      <PhoneStage accent={accent} reducedMotion={reducedMotion} />
      <FloatingCards nodes={nodes} reducedMotion={reducedMotion} />
      <GroundRings />
      <Sparkles count={50} accent={accent} reducedMotion={reducedMotion} />
    </>
  );
}

export default function WowBundleRenderer({ nodes, accent, reducedMotion }: SceneProps) {
  return (
    <Canvas
      className="wow-bundle-canvas"
      dpr={[1, 1.8]}
      camera={{ position: [STAGE_X * 0.5, 0.6, 12], fov: 52 }}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <Scene nodes={nodes} accent={accent} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
