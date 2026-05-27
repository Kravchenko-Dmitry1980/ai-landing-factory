import { applyThemeTokenOverrides } from "@/design/applyThemeTokens";
import { getLayoutPreset } from "@/design/layout_presets";
import { getStyleProfile, type StyleProfileId } from "@/design/style_profiles";
import { UNIVERSITY_DEFAULT_TOKENS } from "@/lib/styleIntent";
import type { RenderPlan } from "./types";

export function testRenderPlan(overrides: Partial<RenderPlan> = {}): RenderPlan {
  const profileId = (overrides.profileId ?? "university_platform") as StyleProfileId;
  return {
    meta: {
      projectId: "p1",
      title: "Test",
      client: null,
      timeline: null,
      lead: null,
      version: 1,
      updatedAt: null,
    },
    profile: getStyleProfile(profileId),
    layout: getLayoutPreset("architecture_first"),
    profileId,
    layoutId: "architecture_first",
    themeTokens: UNIVERSITY_DEFAULT_TOKENS,
    cssVars: applyThemeTokenOverrides(profileId, UNIVERSITY_DEFAULT_TOKENS),
    sections: [],
    modules: [],
    team: [],
    stackGrouped: {},
    fidelityDiagnostics: {
      modulesSource: "fidelity",
      teamSource: "fidelity",
      stackSource: "fidelity",
      modulesCount: 0,
      teamCount: 0,
      stackCategoriesCount: 0,
    },
    hallmarkViolations: [],
    builtAt: Date.now(),
    ...overrides,
  };
}
