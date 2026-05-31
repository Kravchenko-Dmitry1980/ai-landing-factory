/**
 * UII Light ambient 3D backdrop for the Interactive WOW Bundle (Stage P.7.5).
 *
 * Portal arch + floating cards + sparkles only. The cat mascot is rendered as an
 * HTML/CSS layer in {@link WowBundleApp} — no procedural robot scene here.
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

const STAGE_X = 1.2;

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

function Scene({ nodes, accent, reducedMotion }: SceneProps) {
  const { camera } = useThree();

  useFrame((state) => {
    if (reducedMotion) return;
    const targetX = state.pointer.x * 0.45;
    const targetY = 0.55 + state.pointer.y * 0.35;
    camera.position.x += (targetX - camera.position.x) * 0.04;
    camera.position.y += (targetY - camera.position.y) * 0.04;
    camera.lookAt(STAGE_X, 0.1, 0);
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
      <FloatingCards nodes={nodes} reducedMotion={reducedMotion} />
      <Sparkles count={50} accent={accent} reducedMotion={reducedMotion} />
    </>
  );
}

export default function WowBundleRenderer({ nodes, accent, reducedMotion }: SceneProps) {
  return (
    <Canvas
      className="wow-bundle-canvas"
      dpr={[1, 1.8]}
      camera={{ position: [0.4, 0.55, 12], fov: 52 }}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <Scene nodes={nodes} accent={accent} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
