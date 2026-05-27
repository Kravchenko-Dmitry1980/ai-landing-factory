import {
  getStyleProfile,
  isStyleProfileId,
  PRESET_BASE_TOKENS,
  type StyleProfile,
  type StyleProfileId,
} from "@/design/styleProfiles";
import {
  DEFAULT_STYLE_CONFIG,
  legacyStyleToProfile,
  parseStyleConfigFromContract,
  resolveThemeTokens,
} from "@/lib/styleConfig";
import type { LandingContract, LandingStyleConfig } from "@/lib/types";

export type ExportTheme = StyleProfileId;

let lastUnknownProfileWarning: string | null = null;

export function consumeUnknownProfileWarning(): string | null {
  const w = lastUnknownProfileWarning;
  lastUnknownProfileWarning = null;
  return w;
}

function warnUnknownProfile(raw: string): void {
  lastUnknownProfileWarning = `Unknown style profile "${raw}" — falling back to university_platform.`;
  if (typeof console !== "undefined" && process.env.NODE_ENV !== "production") {
    console.warn(`[resolveStyleConfig] ${lastUnknownProfileWarning}`);
  }
}

/**
 * Resolve effective style_config from contract + optional editor override.
 */
export function resolveStyleConfig(
  contract: LandingContract | null | undefined,
  editorOverride?: LandingStyleConfig | null,
): LandingStyleConfig {
  if (editorOverride?.profile) {
    return {
      ...DEFAULT_STYLE_CONFIG,
      ...editorOverride,
      theme_tokens: resolveThemeTokens({
        ...DEFAULT_STYLE_CONFIG,
        ...editorOverride,
      }),
    };
  }
  return parseStyleConfigFromContract(
    contract?.style_config,
    contract?.presentation_style,
    contract?.style,
  );
}

/**
 * Preview profile for a resolved style_config (id matches export theme).
 */
export function resolvePreviewProfile(styleConfig: LandingStyleConfig): StyleProfile {
  const profileId = styleConfig.profile;
  if (profileId === "custom") {
    const tokens = resolveThemeTokens(styleConfig);
    return {
      ...getStyleProfile("custom"),
      baseTokens: tokens,
      layoutDensity: tokens.density ?? "normal",
      motion: tokens.motion ?? "subtle",
      heroStyle: mapHeroMode(tokens.hero_mode),
      cardStyle: tokens.color_scheme === "dark" ? "glass" : "soft",
    };
  }
  if (isStyleProfileId(profileId)) {
    return getStyleProfile(profileId);
  }
  warnUnknownProfile(profileId);
  return getStyleProfile("university_platform");
}

/** Export theme id — 1:1 with preview profile id. */
export function resolveExportTheme(styleConfig: LandingStyleConfig): ExportTheme {
  const id = styleConfig.profile;
  if (isStyleProfileId(id)) return id;
  warnUnknownProfile(id);
  return "university_platform";
}

/** Preview profile id from style_config (same as export theme id). */
export function resolvePreviewProfileId(
  styleConfig: LandingStyleConfig,
): StyleProfileId {
  return resolveExportTheme(styleConfig);
}

/**
 * Legacy contracts without style_config: map old style preset → export profile.
 * Does NOT map minimal/corporate to enterprise.
 */
export function resolveLegacyContractProfile(
  contract: LandingContract | null | undefined,
): LandingStyleProfile | null {
  if (!contract || contract.style_config?.profile) return null;
  return legacyStyleToProfile(
    contract.style,
    contract.presentation_style,
    Boolean(contract.style_config?.profile),
  );
}

type LandingStyleProfile = LandingStyleConfig["profile"];

function mapHeroMode(
  mode?: string,
): StyleProfile["heroStyle"] {
  switch (mode) {
    case "gradient":
      return "gradient";
    case "future_3d":
      return "future_3d";
    case "cards":
      return "bold";
    default:
      return "classic";
  }
}

export { PRESET_BASE_TOKENS };
