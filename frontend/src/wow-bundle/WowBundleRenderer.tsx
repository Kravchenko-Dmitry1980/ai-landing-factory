/**
 * Minimal ambient 3D backdrop for the Interactive WOW Bundle (Stage P.7.6).
 *
 * Soft sparkles only — no portal arch, no 3D floating cards. The cat mascot is
 * rendered as an HTML/CSS layer in {@link WowBundleApp}.
 */

import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type * as THREE from "three";
import type { WowSceneNode } from "./WowBundleData";

interface SceneProps {
  nodes: WowSceneNode[];
  accent: string;
  reducedMotion: boolean;
}

const PALETTE = {
  bg: "#f4f6fd",
};

function Sparkles({ count, accent, reducedMotion }: { count: number; accent: string; reducedMotion: boolean }) {
  const ref = useRef<THREE.Points>(null);
  const positions = useMemo(() => {
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i += 1) {
      arr[i * 3] = 1.2 + (Math.random() - 0.5) * 14;
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
      <pointsMaterial size={0.09} color={accent} transparent opacity={0.45} sizeAttenuation />
    </points>
  );
}

function Scene({ accent, reducedMotion }: Omit<SceneProps, "nodes">) {
  const { camera } = useThree();

  useFrame((state) => {
    if (reducedMotion) return;
    const targetX = state.pointer.x * 0.25;
    const targetY = 0.55 + state.pointer.y * 0.2;
    camera.position.x += (targetX - camera.position.x) * 0.04;
    camera.position.y += (targetY - camera.position.y) * 0.04;
    camera.lookAt(1.2, 0.1, 0);
  });

  return (
    <>
      <color attach="background" args={[PALETTE.bg]} />
      <fog attach="fog" args={[PALETTE.bg, 16, 36]} />
      <hemisphereLight args={["#ffffff", "#dfe4f6", 0.9]} />
      <ambientLight intensity={0.55} />
      <directionalLight position={[5, 8, 6]} intensity={0.9} color="#ffffff" />
      <Sparkles count={36} accent={accent} reducedMotion={reducedMotion} />
    </>
  );
}

export default function WowBundleRenderer({ accent, reducedMotion }: SceneProps) {
  return (
    <Canvas
      className="wow-bundle-canvas"
      dpr={[1, 1.8]}
      camera={{ position: [0.4, 0.55, 12], fov: 52 }}
      frameloop={reducedMotion ? "demand" : "always"}
      gl={{ antialias: true, powerPreference: "high-performance" }}
    >
      <Scene accent={accent} reducedMotion={reducedMotion} />
    </Canvas>
  );
}
