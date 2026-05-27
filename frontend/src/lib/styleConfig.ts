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

export function isLandingStyleProfile(value: string): value is LandingStyleProfile {
  return (PRESET_PROFILES as string[]).includes(value);
}

/** Map user-facing preset → renderer StyleProfileId. */
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

export function resolveThemeTokens(config: LandingStyleConfig): ThemeTokens {
  if (config.profile === "custom" && config.custom_style_prompt?.trim()) {
    return parseStyleIntent(config.custom_style_prompt);
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
  return {
    profile,
    theme_tokens: { ...UNIVERSITY_DEFAULT_TOKENS },
  };
}

export function parseStyleConfigFromContract(
  styleConfig: LandingStyleConfig | null | undefined,
  presentationStyle: string | null | undefined,
): LandingStyleConfig {
  if (styleConfig?.profile) {
    return {
      ...DEFAULT_STYLE_CONFIG,
      ...styleConfig,
      theme_tokens: {
        ...UNIVERSITY_DEFAULT_TOKENS,
        ...styleConfig.theme_tokens,
      },
    };
  }
  const ps = (presentationStyle ?? "").trim();
  if (ps && !ps.startsWith("layout:") && isLandingStyleProfile(ps)) {
    return buildStyleConfigFromEditor(ps as LandingStyleProfile, "");
  }
  if (ps === "university_platform") {
    return { ...DEFAULT_STYLE_CONFIG };
  }
  return { ...DEFAULT_STYLE_CONFIG };
}

export function styleConfigToPresentationStyle(config: LandingStyleConfig): string | null {
  if (config.profile === "university_platform") {
    return "university_platform";
  }
  if (config.profile === "custom") {
    return "university_platform";
  }
  return config.profile;
}

export function styleConfigToExportTheme(config: LandingStyleConfig): string {
  const profileId = profileToStyleProfileId(config.profile);
  if (profileId === "university_platform") {
    return "university_platform";
  }
  return "enterprise_dark";
}
