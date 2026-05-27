import type { StyleProfileId } from "@/design/style_profiles";
import {
  parseStyleIntent,
  UNIVERSITY_DEFAULT_TOKENS,
  type ThemeTokens,
} from "@/lib/styleIntent";
import type { LandingStyleConfig, LandingStyleProfile } from "@/lib/types";

export const DEFAULT_STYLE_CONFIG: LandingStyleConfig = {
  profile: "university_platform",
  theme_tokens: { ...UNIVERSITY_DEFAULT_TOKENS },
};

const PRESET_PROFILES: LandingStyleProfile[] = [
  "university_platform",
  "minimal",
  "corporate",
  "tech",
  "bold",
  "custom",
];

/** Preset theme tokens for preview (export uses backend CSS per profile). */
export const PRESET_THEME_TOKENS: Record<
  Exclude<LandingStyleProfile, "custom">,
  ThemeTokens
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

export function isLandingStyleProfile(value: string): value is LandingStyleProfile {
  return (PRESET_PROFILES as string[]).includes(value);
}

/** Map user-facing preset → renderer StyleProfileId (preview only). */
export function profileToStyleProfileId(profile: LandingStyleProfile): StyleProfileId {
  const map: Record<LandingStyleProfile, StyleProfileId> = {
    university_platform: "university_platform",
    minimal: "enterprise",
    corporate: "enterprise",
    tech: "ai_research",
    bold: "analytics",
    custom: "university_platform",
  };
  return map[profile] ?? "university_platform";
}

/** Export theme query = profile id (distinct CSS per preset). */
export function styleConfigToExportTheme(config: LandingStyleConfig): string {
  return config.profile;
}

export function resolveThemeTokens(config: LandingStyleConfig): ThemeTokens {
  if (config.profile === "custom" && config.custom_style_prompt?.trim()) {
    return parseStyleIntent(config.custom_style_prompt);
  }
  if (config.profile !== "custom" && config.profile in PRESET_THEME_TOKENS) {
    return {
      ...PRESET_THEME_TOKENS[config.profile as Exclude<LandingStyleProfile, "custom">],
      ...config.theme_tokens,
    };
  }
  if (config.theme_tokens && Object.keys(config.theme_tokens).length > 0) {
    return { ...UNIVERSITY_DEFAULT_TOKENS, ...config.theme_tokens };
  }
  return { ...UNIVERSITY_DEFAULT_TOKENS };
}

export function buildStyleConfigFromEditor(
  profile: LandingStyleProfile,
  customPrompt: string,
  appliedTokens?: ThemeTokens,
): LandingStyleConfig {
  if (profile === "custom") {
    const tokens = appliedTokens ?? parseStyleIntent(customPrompt);
    return {
      profile: "custom",
      custom_style_prompt: customPrompt.trim() || undefined,
      theme_tokens: tokens,
    };
  }
  const preset = PRESET_THEME_TOKENS[profile];
  return {
    profile,
    theme_tokens: { ...preset },
  };
}

export function parseStyleConfigFromContract(
  styleConfig: LandingStyleConfig | null | undefined,
  presentationStyle: string | null | undefined,
  contractStyle?: string | null,
): LandingStyleConfig {
  if (styleConfig?.profile) {
    return {
      ...DEFAULT_STYLE_CONFIG,
      ...styleConfig,
      theme_tokens: {
        ...resolveThemeTokens({ ...DEFAULT_STYLE_CONFIG, ...styleConfig }),
        ...styleConfig.theme_tokens,
      },
    };
  }
  const ps = (presentationStyle ?? "").trim();
  if (ps && !ps.startsWith("layout:") && isLandingStyleProfile(ps)) {
    return buildStyleConfigFromEditor(ps as LandingStyleProfile, "");
  }
  const legacy = legacyStyleToProfile(contractStyle, presentationStyle, false);
  if (legacy) {
    return buildStyleConfigFromEditor(legacy, "");
  }
  return { ...DEFAULT_STYLE_CONFIG };
}

/**
 * Legacy mapping for contracts without style_config (no enterprise_dark).
 */
export function legacyStyleToProfile(
  style: string | null | undefined,
  presentationStyle: string | null | undefined,
  hasStyleConfig: boolean,
): LandingStyleProfile | null {
  if (hasStyleConfig) return null;
  const ps = (presentationStyle ?? "").trim();
  if (ps && !ps.startsWith("layout:") && isLandingStyleProfile(ps)) {
    return ps as LandingStyleProfile;
  }
  const map: Record<string, LandingStyleProfile> = {
    minimal: "minimal",
    corporate: "corporate",
    tech: "tech",
    bold: "bold",
    university_platform: "university_platform",
  };
  if (style && map[style]) return map[style];
  return null;
}

export function styleConfigToPresentationStyle(config: LandingStyleConfig): string {
  if (config.profile === "custom") {
    return "university_platform";
  }
  return config.profile;
}

export function exportThemeBodyClass(theme: string): string {
  if (theme === "enterprise_dark") return "theme-enterprise_dark";
  return `theme-${theme}`;
}
