import type { MotionRules } from "./motion";
import { getMotionRules } from "./motion";
import type { SpacingScale } from "./spacing";
import { getSpacingScale } from "./spacing";
import type { ThemeTokens } from "./tokens";
import type { TypographyScale } from "./typography";
import { getTypographyScale } from "./typography";
import { buildThemeTokens } from "./themes";

export type StyleProfileId =
  | "enterprise"
  | "medical"
  | "ai_research"
  | "education"
  | "analytics"
  | "university_platform";

export type DiagramPreference = "flow" | "grid" | "timeline" | "minimal";

export interface StyleProfile {
  id: StyleProfileId;
  label: string;
  tokens: ThemeTokens;
  typography: TypographyScale;
  spacing: SpacingScale;
  motion: MotionRules;
  sectionDensity: "compact" | "standard";
  diagramPreference: DiagramPreference;
}

export const STYLE_PROFILES: Record<StyleProfileId, StyleProfile> = {} as Record<
  StyleProfileId,
  StyleProfile
>;

const IDS: StyleProfileId[] = [
  "enterprise",
  "medical",
  "ai_research",
  "education",
  "analytics",
  "university_platform",
];

const LABELS: Partial<Record<StyleProfileId, string>> = {
  university_platform: "University / Платформа УИИ",
};

for (const id of IDS) {
  STYLE_PROFILES[id] = {
    id,
    label: LABELS[id] ?? id.replace("_", " "),
    tokens: buildThemeTokens(id),
    typography: getTypographyScale(id),
    spacing: getSpacingScale(id),
    motion: getMotionRules(id),
    sectionDensity:
      id === "medical" || id === "ai_research" ? "compact" : "standard",
    diagramPreference:
      id === "ai_research" || id === "university_platform"
        ? "flow"
        : id === "analytics"
          ? "grid"
          : id === "education"
            ? "timeline"
            : "minimal",
  };
}

/** Map legacy backend style preset → domain profile */
export function legacyStyleToProfile(
  style: string | undefined,
  presentationStyle?: string | null,
): StyleProfileId {
  if (presentationStyle && presentationStyle in STYLE_PROFILES) {
    return presentationStyle as StyleProfileId;
  }
  const map: Record<string, StyleProfileId> = {
    minimal: "enterprise",
    corporate: "enterprise",
    tech: "ai_research",
    bold: "analytics",
    enterprise: "enterprise",
    medical: "medical",
    ai_research: "ai_research",
    education: "education",
    analytics: "analytics",
    university_platform: "university_platform",
  };
  return map[style ?? "minimal"] ?? "enterprise";
}

export function getStyleProfile(id: StyleProfileId): StyleProfile {
  return STYLE_PROFILES[id];
}
