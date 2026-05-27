import type { ThemeTokens as SemanticTokens } from "@/lib/styleIntent";
import { UNIVERSITY_DEFAULT_TOKENS } from "@/lib/styleIntent";

export type StyleProfileId =
  | "university_platform"
  | "minimal"
  | "corporate"
  | "tech"
  | "bold"
  | "custom";

export type LayoutDensity = "compact" | "normal" | "spacious";
export type CardStyle = "flat" | "soft" | "glass" | "outlined";
export type HeroStyle = "classic" | "gradient" | "bold" | "future_3d";
export type ProfileMotion = "none" | "subtle" | "expressive";

export interface StyleProfile {
  id: StyleProfileId;
  label: string;
  description: string;
  baseTokens: SemanticTokens;
  layoutDensity: LayoutDensity;
  cardStyle: CardStyle;
  heroStyle: HeroStyle;
  motion: ProfileMotion;
}

export const STYLE_PROFILE_IDS: StyleProfileId[] = [
  "university_platform",
  "minimal",
  "corporate",
  "tech",
  "bold",
  "custom",
];

export const PRESET_BASE_TOKENS: Record<
  Exclude<StyleProfileId, "custom">,
  SemanticTokens
> = {
  university_platform: { ...UNIVERSITY_DEFAULT_TOKENS },
  minimal: {
    color_scheme: "light",
    accent: "violet",
    radius: "sharp",
    density: "spacious",
    motion: "none",
    hero_mode: "classic",
    background: "#ffffff",
    surface: "#fafafa",
  },
  corporate: {
    color_scheme: "light",
    accent: "blue",
    radius: "soft",
    density: "normal",
    motion: "subtle",
    hero_mode: "classic",
    background: "#f8fafc",
    surface: "#ffffff",
  },
  tech: {
    color_scheme: "dark",
    accent: "blue",
    radius: "rounded",
    density: "normal",
    motion: "expressive",
    hero_mode: "gradient",
    background: "#0f172a",
    surface: "#1e293b",
  },
  bold: {
    color_scheme: "light",
    accent: "violet",
    radius: "rounded",
    density: "compact",
    motion: "expressive",
    hero_mode: "cards",
    background: "#ffffff",
    surface: "#fff7ed",
  },
};

export const STYLE_PROFILES: Record<StyleProfileId, StyleProfile> = {
  university_platform: {
    id: "university_platform",
    label: "University / Платформа УИИ",
    description: "Light academic platform look with violet accent.",
    baseTokens: PRESET_BASE_TOKENS.university_platform,
    layoutDensity: "normal",
    cardStyle: "soft",
    heroStyle: "classic",
    motion: "subtle",
  },
  minimal: {
    id: "minimal",
    label: "Minimal",
    description: "White canvas, restrained color, generous whitespace.",
    baseTokens: PRESET_BASE_TOKENS.minimal,
    layoutDensity: "spacious",
    cardStyle: "flat",
    heroStyle: "classic",
    motion: "none",
  },
  corporate: {
    id: "corporate",
    label: "Corporate",
    description: "Neutral business layout with blue accent and outlined cards.",
    baseTokens: PRESET_BASE_TOKENS.corporate,
    layoutDensity: "normal",
    cardStyle: "outlined",
    heroStyle: "classic",
    motion: "subtle",
  },
  tech: {
    id: "tech",
    label: "Tech",
    description: "Dark semi-gradient tech feel with stronger contrast.",
    baseTokens: PRESET_BASE_TOKENS.tech,
    layoutDensity: "normal",
    cardStyle: "glass",
    heroStyle: "gradient",
    motion: "expressive",
  },
  bold: {
    id: "bold",
    label: "Bold",
    description: "Expressive typography and cards with warm accent.",
    baseTokens: PRESET_BASE_TOKENS.bold,
    layoutDensity: "compact",
    cardStyle: "soft",
    heroStyle: "bold",
    motion: "expressive",
  },
  custom: {
    id: "custom",
    label: "Custom",
    description: "Derived from safe parsed style intent tokens.",
    baseTokens: { ...UNIVERSITY_DEFAULT_TOKENS },
    layoutDensity: "normal",
    cardStyle: "soft",
    heroStyle: "classic",
    motion: "subtle",
  },
};

export function isStyleProfileId(value: string): value is StyleProfileId {
  return (STYLE_PROFILE_IDS as string[]).includes(value);
}

export function getStyleProfile(id: StyleProfileId): StyleProfile {
  return STYLE_PROFILES[id];
}
