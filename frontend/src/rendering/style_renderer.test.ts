import { describe, expect, it } from "vitest";
import { applyThemeTokenOverrides } from "@/design/applyThemeTokens";
import {
  buildRenderPlan,
  defaultRenderConfig,
  resolveExportTheme,
} from "./contract_adapter";
import { parseStyleIntent } from "@/lib/styleIntent";
import type { GeneratedLanding, LandingContract } from "@/lib/types";
import { DEFAULT_STYLE_CONFIG } from "@/lib/styleConfig";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "corporate",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "Test", bullets: [] },
    { key: "essence", title: "Essence", body: "Body", bullets: [] },
  ],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "corporate",
  client: null,
  goals: [],
  presentation_style: null,
  blocks: [],
  updated_at: landing.generated_at,
  version: 1,
};

describe("style renderer defaults", () => {
  it("default profile is university_platform", () => {
    const cfg = defaultRenderConfig(landing, contract);
    expect(cfg.profileId).toBe("university_platform");
    expect(cfg.styleConfig?.profile).toBe("university_platform");
  });

  it("export theme defaults to university_platform", () => {
    expect(resolveExportTheme(null, contract, null, landing)).toBe("university_platform");
  });

  it("custom tokens affect CSS variables", () => {
    const tokens = parseStyleIntent("тёмный стиль с синим акцентом");
    const vars = applyThemeTokenOverrides("university_platform", tokens);
    expect(vars["--alf-accent"]).toBe("#2563eb");
    expect(vars["--alf-bg"]).toBe("#0f1419");
  });

  it("future_3d sets hero mode css var", () => {
    const tokens = parseStyleIntent("3D интерактив");
    const plan = buildRenderPlan(landing, contract, {
      profileId: "university_platform",
      layoutId: "architecture_first",
      styleConfig: {
        profile: "custom",
        custom_style_prompt: "3D",
        theme_tokens: tokens,
      },
    });
    expect(plan.themeTokens.hero_mode).toBe("future_3d");
    expect(plan.cssVars["--alf-hero-mode"]).toBe("future_3d");
  });

  it("does not embed raw custom prompt in render plan", () => {
    const evil = "<script>alert(1)</script>";
    const plan = buildRenderPlan(landing, contract, {
      profileId: "university_platform",
      layoutId: "architecture_first",
      styleConfig: {
        profile: "custom",
        custom_style_prompt: evil,
        theme_tokens: parseStyleIntent(evil),
      },
    });
    expect(JSON.stringify(plan)).not.toContain("<script>");
  });

  it("DEFAULT_STYLE_CONFIG uses university", () => {
    expect(DEFAULT_STYLE_CONFIG.profile).toBe("university_platform");
  });
});
