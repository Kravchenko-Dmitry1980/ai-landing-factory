import { describe, expect, it } from "vitest";
import { applyThemeTokenOverrides } from "@/design/applyThemeTokens";
import { exportThemeBodyClass } from "@/lib/styleConfig";
import { buildRenderPlan } from "./contract_adapter";
import { testRenderPlan } from "./testPlan";
import type { GeneratedLanding, LandingContract } from "@/lib/types";
import { buildStyleConfigFromEditor } from "@/lib/styleConfig";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "minimal",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [{ key: "tagline", title: "T", body: "B", bullets: [] }],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "minimal",
  goals: [],
  presentation_style: null,
  blocks: [],
  updated_at: landing.generated_at,
  version: 1,
};

describe("style profile rendering", () => {
  it("export body classes are distinct per preset", () => {
    expect(exportThemeBodyClass("tech")).toBe("theme-tech");
    expect(exportThemeBodyClass("bold")).toBe("theme-bold");
    expect(exportThemeBodyClass("minimal")).toBe("theme-minimal");
  });

  it("tech tokens apply dark background in preview CSS vars", () => {
    const cfg = buildStyleConfigFromEditor("tech", "");
    const vars = applyThemeTokenOverrides("tech", cfg.theme_tokens);
    expect(vars["--alf-bg"]).toBe("#0f172a");
  });

  it("buildRenderPlan carries styleConfig theme tokens", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "tech",
      layoutId: "architecture_first",
      styleConfig: buildStyleConfigFromEditor("tech", ""),
    });
    expect(plan.profileId).toBe("tech");
    expect(plan.themeTokens.hero_mode).toBe("gradient");
  });

  it("testRenderPlan includes cssVars", () => {
    const plan = testRenderPlan({ profileId: "university_platform" });
    expect(plan.cssVars["--alf-accent"]).toBeTruthy();
  });
});
