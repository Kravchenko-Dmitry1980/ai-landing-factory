import type { StyleProfileId } from "./style_profiles";

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
    enterprise: {
      intensity: "subtle",
      sectionReveal: { duration: 0.35, y: 8 },
      staggerChildren: 0.04,
      enableCounters: true,
      enableNodeReveal: true,
    },
    medical: {
      intensity: "subtle",
      sectionReveal: { duration: 0.3, y: 6 },
      staggerChildren: 0.03,
      enableCounters: false,
      enableNodeReveal: false,
    },
    ai_research: {
      intensity: "moderate",
      sectionReveal: { duration: 0.4, y: 10 },
      staggerChildren: 0.05,
      enableCounters: true,
      enableNodeReveal: true,
    },
    education: {
      intensity: "subtle",
      sectionReveal: { duration: 0.35, y: 8 },
      staggerChildren: 0.04,
      enableCounters: false,
      enableNodeReveal: false,
    },
    analytics: {
      intensity: "subtle",
      sectionReveal: { duration: 0.35, y: 8 },
      staggerChildren: 0.04,
      enableCounters: true,
      enableNodeReveal: false,
    },
    university_platform: {
      intensity: "none",
      sectionReveal: { duration: 0.25, y: 4 },
      staggerChildren: 0.02,
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
