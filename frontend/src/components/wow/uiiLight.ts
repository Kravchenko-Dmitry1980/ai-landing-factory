/**
 * UII Light 3D WOW scene palette & helpers (Stage P.7.2).
 *
 * Shared design tokens for the light, exhibition-grade "AI Learning Portal"
 * scene used by the WOW preview hero. Colors follow the УИИ visual language:
 * light background, soft violet / lavender / cyan accents, glossy plastic.
 *
 * Kept free of three.js imports so it can be reused by plain helpers and tests.
 */

import type { WowHeroNode } from "@/lib/wowHeroMapping";

export const UII_LIGHT = {
  /** Scene background (matches the CSS stage gradient base). */
  bg: "#f4f6fd",
  /** Primary brand accent (violet). */
  accent: "#7c4dff",
  /** Soft secondary purple. */
  purple: "#a78bfa",
  /** Cyan / glow highlight. */
  cyan: "#5dd6ff",
  /** Pale lavender. */
  lavender: "#d9ccff",
  /** Glossy white shells. */
  shell: "#ffffff",
  /** Slightly cooled white for secondary shells. */
  shell2: "#eef1fb",
  /** Dark face / screen ink. */
  ink: "#1b1f3b",
} as const;

/** Floating data-card accent per node kind (light-scene tuned). */
export const UII_NODE_COLOR: Record<WowHeroNode["kind"], string> = {
  data: "#38bdf8",
  ml: "#7c4dff",
  service: "#6366f1",
  ui: "#22d3ee",
  storage: "#8b7cf6",
  core: "#a78bfa",
};

/** Deterministic PRNG (mulberry32) for stable, repeatable layouts. */
export function makeRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface FloatingCardLayout {
  position: [number, number, number];
  rotation: [number, number, number];
  scale: number;
  color: string;
  /** Phase offset so cards don't bob in unison. */
  phase: number;
}

/**
 * Lay out floating data cards around the assistant/device stage.
 * Cards hover in a loose ring in front-of and beside the hero composition.
 */
export function layoutFloatingCards(
  nodes: WowHeroNode[],
  rng: () => number,
): FloatingCardLayout[] {
  const slots: Array<[number, number, number]> = [
    [-2.6, 1.5, 0.8],
    [2.5, 1.9, 0.4],
    [-3.0, -0.2, 1.1],
    [2.9, 0.2, 0.9],
    [-2.1, -1.4, 1.4],
    [2.2, -1.2, 1.2],
    [-1.2, 2.4, -0.2],
    [1.4, 2.6, -0.4],
  ];
  return nodes.slice(0, slots.length).map((node, i) => {
    const [x, y, z] = slots[i];
    const tilt = (rng() - 0.5) * 0.3;
    return {
      position: [x, y, z],
      rotation: [tilt * 0.6, x > 0 ? -0.35 : 0.35, tilt],
      scale: 0.9 + rng() * 0.25,
      color: UII_NODE_COLOR[node.kind],
      phase: i * 0.7,
    };
  });
}
