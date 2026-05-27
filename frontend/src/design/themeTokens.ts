import type { StyleProfileId } from "@/design/styleProfiles";
import { STYLE_PROFILES } from "@/design/styleProfiles";
import type { LandingStyleConfig } from "@/lib/types";
import {
  parseStyleIntent,
  accentToHex,
  type ThemeTokens as SemanticTokens,
} from "@/lib/styleIntent";
import { resolveThemeTokens } from "@/lib/styleConfig";

export type ColorScheme = "light" | "dark";
export type Density = "compact" | "normal" | "spacious";
export type Motion = "none" | "subtle" | "expressive";
export type HeroMode = "classic" | "gradient" | "bold" | "future_3d";
export type CardStyle = "flat" | "soft" | "glass" | "outlined";

export interface ThemeTokens {
  colorScheme: ColorScheme;
  bg: string;
  surface: string;
  surface2: string;
  text: string;
  muted: string;
  border: string;
  accent: string;
  accentHover: string;
  accentLight: string;
  radiusPx: number;
  gapRem: number;
  density: Density;
  motion: Motion;
  heroMode: HeroMode;
  cardStyle: CardStyle;
}

export type SerializedThemeTokens = ThemeTokens;

const RADIUS_PX: Record<string, number> = { sharp: 4, soft: 8, rounded: 16 };
const GAP_REM: Record<Density, number> = {
  compact: 1,
  normal: 1.5,
  spacious: 2,
};
const MOTION_DURATION: Record<Motion, string> = {
  none: "0s",
  subtle: "0.25s",
  expressive: "0.45s",
};
const CARD_TRANSFORM: Record<CardStyle, string> = {
  flat: "none",
  soft: "translateY(-4px)",
  glass: "translateY(-2px)",
  outlined: "none",
};

export const PROFILE_PRESETS: Record<StyleProfileId, ThemeTokens> = {
  university_platform: {
    colorScheme: "light",
    bg: "#ffffff",
    surface: "#F1F4F7",
    surface2: "#EEF2F5",
    text: "#111111",
    muted: "#7A8799",
    border: "#E5E7EB",
    accent: "#7C3AED",
    accentHover: "#6D28D9",
    accentLight: "#EDE9FE",
    radiusPx: 8,
    gapRem: 1.5,
    density: "normal",
    motion: "subtle",
    heroMode: "classic",
    cardStyle: "soft",
  },
  minimal: {
    colorScheme: "light",
    bg: "#ffffff",
    surface: "#fafafa",
    surface2: "#f5f5f5",
    text: "#171717",
    muted: "#737373",
    border: "#f0f0f0",
    accent: "#525252",
    accentHover: "#404040",
    accentLight: "#f5f5f5",
    radiusPx: 4,
    gapRem: 2,
    density: "spacious",
    motion: "none",
    heroMode: "classic",
    cardStyle: "flat",
  },
  corporate: {
    colorScheme: "light",
    bg: "#f8fafc",
    surface: "#ffffff",
    surface2: "#f1f5f9",
    text: "#0f172a",
    muted: "#64748b",
    border: "#cbd5e1",
    accent: "#2563eb",
    accentHover: "#1d4ed8",
    accentLight: "#dbeafe",
    radiusPx: 8,
    gapRem: 1.5,
    density: "normal",
    motion: "subtle",
    heroMode: "classic",
    cardStyle: "outlined",
  },
  tech: {
    colorScheme: "dark",
    bg: "#0f172a",
    surface: "#1e293b",
    surface2: "#334155",
    text: "#e8edf4",
    muted: "#94a3b8",
    border: "rgba(148,163,184,0.25)",
    accent: "#6366f1",
    accentHover: "#4f46e5",
    accentLight: "rgba(99,102,241,0.2)",
    radiusPx: 16,
    gapRem: 1.5,
    density: "normal",
    motion: "expressive",
    heroMode: "gradient",
    cardStyle: "glass",
  },
  bold: {
    colorScheme: "light",
    bg: "#ffffff",
    surface: "#fff7ed",
    surface2: "#ffedd5",
    text: "#1c1917",
    muted: "#78716c",
    border: "#fed7aa",
    accent: "#ea580c",
    accentHover: "#c2410c",
    accentLight: "#ffedd5",
    radiusPx: 16,
    gapRem: 1,
    density: "compact",
    motion: "expressive",
    heroMode: "bold",
    cardStyle: "soft",
  },
  custom: {
    colorScheme: "light",
    bg: "#ffffff",
    surface: "#F1F4F7",
    surface2: "#EEF2F5",
    text: "#111111",
    muted: "#7A8799",
    border: "#E5E7EB",
    accent: "#7C3AED",
    accentHover: "#6D28D9",
    accentLight: "#EDE9FE",
    radiusPx: 8,
    gapRem: 1.5,
    density: "normal",
    motion: "subtle",
    heroMode: "classic",
    cardStyle: "soft",
  },
};

function heroModeFromSemantic(mode?: string): HeroMode {
  if (mode === "cards") return "bold";
  if (mode === "gradient" || mode === "future_3d" || mode === "bold") return mode;
  return "classic";
}

function cardStyleFor(
  colorScheme: ColorScheme,
  profile: StyleProfileId,
  heroMode: HeroMode,
): CardStyle {
  if (profile !== "custom") return STYLE_PROFILES[profile].cardStyle;
  if (colorScheme === "dark" || heroMode === "future_3d") return "glass";
  return "soft";
}

function applySemantic(base: ThemeTokens, semantic: SemanticTokens): ThemeTokens {
  const out = { ...base };
  if (semantic.accent) {
    out.accent = accentToHex(semantic.accent);
    if (semantic.accent === "blue") {
      out.accentHover = "#1d4ed8";
      out.accentLight = "#dbeafe";
    } else if (semantic.accent === "green") {
      out.accentHover = "#047857";
      out.accentLight = "#d1fae5";
    } else {
      out.accentHover = "#6D28D9";
      out.accentLight = "#EDE9FE";
    }
  }
  if (semantic.background) out.bg = semantic.background;
  if (semantic.surface) {
    out.surface = semantic.surface;
    out.surface2 = semantic.surface;
  }
  if (semantic.color_scheme === "dark") {
    out.colorScheme = "dark";
    out.bg = semantic.background ?? "#0f1419";
    out.surface = semantic.surface ?? "#1a2332";
    out.surface2 = "#243044";
    out.text = "#e8edf4";
    out.muted = "#94a3b8";
    out.border = "rgba(148,163,184,0.25)";
    out.accentLight = `${out.accent}26`;
  } else if (semantic.color_scheme === "light") {
    out.colorScheme = "light";
  }
  if (semantic.radius && semantic.radius in RADIUS_PX) {
    out.radiusPx = RADIUS_PX[semantic.radius];
  }
  if (semantic.density && semantic.density in GAP_REM) {
    out.density = semantic.density;
    out.gapRem = GAP_REM[semantic.density];
  }
  if (semantic.motion === "none" || semantic.motion === "subtle" || semantic.motion === "expressive") {
    out.motion = semantic.motion;
  }
  if (semantic.hero_mode) {
    out.heroMode = heroModeFromSemantic(semantic.hero_mode);
  }
  out.cardStyle = cardStyleFor(out.colorScheme, "custom", out.heroMode);
  return out;
}

export function normalizeThemeTokens(styleConfig: LandingStyleConfig): ThemeTokens {
  const profile = styleConfig.profile as StyleProfileId;
  const base = { ...PROFILE_PRESETS[profile] ?? PROFILE_PRESETS.university_platform };

  const explicitTokens = styleConfig.theme_tokens ?? {};
  const hasExplicitOverrides =
    profile === "custom" ||
    Boolean(styleConfig.custom_style_prompt?.trim()) ||
    Object.keys(explicitTokens).length > 0;

  if (!hasExplicitOverrides) {
    return base;
  }

  let semantic: SemanticTokens = resolveThemeTokens(styleConfig);
  if (profile === "custom" && styleConfig.custom_style_prompt?.trim()) {
    semantic = {
      ...parseStyleIntent(styleConfig.custom_style_prompt),
      ...semantic,
    };
  }

  return applySemantic(base, semantic);
}

export function serializeThemeTokens(styleConfig: LandingStyleConfig): SerializedThemeTokens {
  return normalizeThemeTokens(styleConfig);
}

export function heroGradientValue(tokens: ThemeTokens): string {
  if (tokens.heroMode === "gradient") {
    return `linear-gradient(135deg, ${tokens.accentLight} 0%, transparent 55%)`;
  }
  if (tokens.heroMode === "future_3d") {
    return `linear-gradient(120deg, ${tokens.accentLight}, transparent 70%)`;
  }
  if (tokens.heroMode === "bold") {
    return `linear-gradient(90deg, ${tokens.accentLight}, transparent 80%)`;
  }
  return "none";
}

export function themeTokensToCssVars(tokens: ThemeTokens): Record<string, string> {
  const heroModeCss = tokens.heroMode === "bold" ? "cards" : tokens.heroMode;
  return {
    "--alf-bg": tokens.bg,
    "--alf-surface": tokens.surface,
    "--alf-surface-2": tokens.surface2,
    "--alf-text": tokens.text,
    "--alf-muted": tokens.muted,
    "--alf-border": tokens.border,
    "--alf-accent": tokens.accent,
    "--alf-accent-hover": tokens.accentHover,
    "--alf-accent-light": tokens.accentLight,
    "--alf-radius": `${tokens.radiusPx}px`,
    "--alf-gap": `${tokens.gapRem}rem`,
    "--alf-motion-duration": MOTION_DURATION[tokens.motion],
    "--alf-card-transform": CARD_TRANSFORM[tokens.cardStyle],
    "--alf-hero-gradient": heroGradientValue(tokens),
    "--alf-hero-mode": heroModeCss,
    "--alf-code-bg": tokens.surface2,
    // legacy aliases (preview sections may still reference these)
    "--alf-text-muted": tokens.muted,
    "--alf-accent-muted": tokens.accentLight,
    "--bg": "var(--alf-bg)",
    "--surface": "var(--alf-surface)",
    "--surface-2": "var(--alf-surface-2)",
    "--text": "var(--alf-text)",
    "--muted": "var(--alf-muted)",
    "--border": "var(--alf-border)",
    "--accent": "var(--alf-accent)",
    "--accent-hover": "var(--alf-accent-hover)",
    "--accent-light": "var(--alf-accent-light)",
    "--radius": "var(--alf-radius)",
    "--gap": "var(--alf-gap)",
  };
}

export type AlfCssVars = ReturnType<typeof themeTokensToCssVars>;

export function containsUnsafeTokenValue(value: string): boolean {
  return /(<\s*script|javascript:|@import|url\s*\(|expression\s*\()/i.test(value);
}
