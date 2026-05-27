import type { StyleProfileId } from "./styleProfiles";

/** Legacy renderer profile ids from pre-P.3.2 contracts and dev tooling. */
export type LegacyStyleProfileId =
  | "enterprise"
  | "medical"
  | "ai_research"
  | "education"
  | "analytics";

const LEGACY_TO_EXPORT: Record<LegacyStyleProfileId, StyleProfileId> = {
  enterprise: "corporate",
  medical: "corporate",
  ai_research: "tech",
  education: "university_platform",
  analytics: "bold",
};

export function isLegacyStyleProfileId(
  value: string,
): value is LegacyStyleProfileId {
  return value in LEGACY_TO_EXPORT;
}

/** Map legacy preview ids to export-aligned profiles (never enterprise for minimal/corporate). */
export function coerceLegacyProfileId(value: string): StyleProfileId {
  if (isLegacyStyleProfileId(value)) {
    return LEGACY_TO_EXPORT[value];
  }
  const direct: StyleProfileId[] = [
    "university_platform",
    "minimal",
    "corporate",
    "tech",
    "bold",
    "custom",
  ];
  if ((direct as string[]).includes(value)) {
    return value as StyleProfileId;
  }
  return "university_platform";
}
