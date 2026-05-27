/**
 * Render-layer style profiles — export-aligned ids with typography/spacing/motion.
 * Legacy domain ids (enterprise, ai_research, …) are isolated in legacyProfileCompat.
 */
import type { MotionRules } from "./motion";
import { getMotionRules } from "./motion";
import type { SpacingScale } from "./spacing";
import { getSpacingScale } from "./spacing";
import {
  getStyleProfile as getExportProfile,
  isStyleProfileId as isExportProfileId,
  STYLE_PROFILES as EXPORT_PROFILES,
  type StyleProfile as ExportStyleProfile,
  type StyleProfileId,
} from "./styleProfiles";
import type { ThemeTokens as CssThemeTokens } from "./tokens";
import type { TypographyScale } from "./typography";
import { getTypographyScale } from "./typography";
import { buildThemeTokens } from "./themes";

export type { StyleProfileId } from "./styleProfiles";
export { isStyleProfileId, STYLE_PROFILES as EXPORT_STYLE_PROFILES } from "./styleProfiles";

export type DiagramPreference = "flow" | "grid" | "timeline" | "minimal";

export interface StyleProfile {
  id: StyleProfileId;
  label: string;
  description: string;
  tokens: CssThemeTokens;
  typography: TypographyScale;
  spacing: SpacingScale;
  motion: MotionRules;
  sectionDensity: "compact" | "standard";
  diagramPreference: DiagramPreference;
  layoutDensity: ExportStyleProfile["layoutDensity"];
  cardStyle: ExportStyleProfile["cardStyle"];
  heroStyle: ExportStyleProfile["heroStyle"];
  profileMotion: ExportStyleProfile["motion"];
}

export const STYLE_PROFILES: Record<StyleProfileId, StyleProfile> = {} as Record<
  StyleProfileId,
  StyleProfile
>;

const DIAGRAM: Record<StyleProfileId, DiagramPreference> = {
  university_platform: "flow",
  minimal: "minimal",
  corporate: "grid",
  tech: "flow",
  bold: "grid",
  custom: "minimal",
};

for (const id of Object.keys(EXPORT_PROFILES) as StyleProfileId[]) {
  const exp = getExportProfile(id);
  STYLE_PROFILES[id] = {
    id,
    label: exp.label,
    description: exp.description,
    tokens: buildThemeTokens(id),
    typography: getTypographyScale(id),
    spacing: getSpacingScale(id),
    motion: getMotionRules(id),
    sectionDensity: exp.layoutDensity === "compact" ? "compact" : "standard",
    diagramPreference: DIAGRAM[id],
    layoutDensity: exp.layoutDensity,
    cardStyle: exp.cardStyle,
    heroStyle: exp.heroStyle,
    profileMotion: exp.motion,
  };
}

export function getStyleProfile(id: StyleProfileId): StyleProfile {
  return STYLE_PROFILES[id];
}

export function isRenderableProfileId(value: string): value is StyleProfileId {
  return isExportProfileId(value);
}

/** @deprecated Use resolveStyleConfig + resolvePreviewProfileId instead. */
export function legacyStyleToProfile(
  style: string | undefined,
  presentationStyle?: string | null,
): StyleProfileId {
  if (presentationStyle && isExportProfileId(presentationStyle)) {
    return presentationStyle;
  }
  const map: Record<string, StyleProfileId> = {
    minimal: "minimal",
    corporate: "corporate",
    tech: "tech",
    bold: "bold",
    university_platform: "university_platform",
    custom: "custom",
    // legacy domain ids → nearest export profile
    enterprise: "corporate",
    medical: "corporate",
    ai_research: "tech",
    education: "university_platform",
    analytics: "bold",
  };
  return map[style ?? "minimal"] ?? "university_platform";
}
