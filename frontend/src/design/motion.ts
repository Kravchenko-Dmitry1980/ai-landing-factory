import type { StyleProfileId } from "./styleProfiles";

export type MotionIntensity = "none" | "subtle" | "moderate";

export interface MotionRules {
  intensity: MotionIntensity;
  sectionReveal: { duration: number; y: number };
  staggerChildren: number;
  enableCounters: boolean;
  enableNodeReveal: boolean;
}

export function getMotionRules(profile: StyleProfileId): MotionRules {
  const map: Record<StyleProfileId, MotionRules> = {
    university_platform: {
      intensity: "none",
      sectionReveal: { duration: 0.25, y: 4 },
      staggerChildren: 0.02,
      enableCounters: false,
      enableNodeReveal: false,
    },
    minimal: {
      intensity: "none",
      sectionReveal: { duration: 0, y: 0 },
      staggerChildren: 0,
      enableCounters: false,
      enableNodeReveal: false,
    },
    corporate: {
      intensity: "subtle",
      sectionReveal: { duration: 0.3, y: 6 },
      staggerChildren: 0.03,
      enableCounters: false,
      enableNodeReveal: false,
    },
    tech: {
      intensity: "moderate",
      sectionReveal: { duration: 0.45, y: 12 },
      staggerChildren: 0.06,
      enableCounters: true,
      enableNodeReveal: true,
    },
    bold: {
      intensity: "moderate",
      sectionReveal: { duration: 0.5, y: 14 },
      staggerChildren: 0.07,
      enableCounters: true,
      enableNodeReveal: false,
    },
    custom: {
      intensity: "subtle",
      sectionReveal: { duration: 0.35, y: 8 },
      staggerChildren: 0.04,
      enableCounters: false,
      enableNodeReveal: false,
    },
  };
  return map[profile];
}

/** Framer variants — no infinite / parallax */
export const revealVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0 },
};
