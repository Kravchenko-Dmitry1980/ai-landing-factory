import { describe, expect, it } from "vitest";
import { STYLE_PROFILES } from "@/design/style_profiles";
import { buildThemeTokens } from "@/design/themes";
import {
  buildRenderPlan,
  isStyleProfileId,
  resolveRenderConfig,
} from "@/rendering/contract_adapter";
import type { GeneratedLanding, LandingContract } from "@/lib/types";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "corporate",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "Эндокринология+", bullets: [] },
    { key: "essence", title: "Essence", body: "Content-first pipeline", bullets: [] },
    {
      key: "tasks",
      title: "Modules",
      body: "",
      bullets: ["GlaucoLogic: AI module", "Copilot врача: assistant", "VitaCalc: calc"],
    },
    { key: "inputs", title: "Inputs", body: "", bullets: ["DOCX", "PDF"] },
    { key: "outputs", title: "Outputs", body: "", bullets: ["Contract", "Preview"] },
    { key: "results", title: "Results", body: "", bullets: ["MVP", "PII guard"] },
    { key: "tech_stack", title: "Stack", body: "", bullets: ["FastAPI", "Next.js"] },
    { key: "team", title: "Team", body: "", bullets: ["Alex — Lead"] },
    { key: "outlook", title: "Roadmap", body: "", bullets: ["Q1", "Q2"] },
  ],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "corporate",
  client: "ACME",
  title: "Enterprise AI Landing",
  timeline: "2026",
  lead: "PM",
  goals: [],
  presentation_style: null,
  visual_assets: [],
  blocks: [],
  updated_at: landing.generated_at,
  version: 1,
};

describe("university_platform style profile", () => {
  it("exists with light tokens", () => {
    expect(STYLE_PROFILES.university_platform).toBeDefined();
    expect(STYLE_PROFILES.university_platform.label).toContain("University");
    const tokens = buildThemeTokens("university_platform");
    expect(tokens["--alf-bg"]).toBe("#ffffff");
    expect(tokens["--alf-accent"]).toBe("#7C3AED");
    expect(tokens["--alf-text"]).toBe("#111111");
  });

  it("recognizes style query param", () => {
    expect(isStyleProfileId("university_platform")).toBe(true);
    const cfg = resolveRenderConfig(
      landing.project_id,
      landing,
      contract,
      "university_platform",
    );
    expect(cfg.profileId).toBe("university_platform");
  });

  it("prefers url style over presentation_style", () => {
    const withPresentation: LandingContract = {
      ...contract,
      presentation_style: "medical",
    };
    const cfg = resolveRenderConfig(
      landing.project_id,
      landing,
      withPresentation,
      "university_platform",
    );
    expect(cfg.profileId).toBe("university_platform");
  });

  it("builds render plan with university profile", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "university_platform",
      layoutId: "architecture_first",
    });
    expect(plan.profileId).toBe("university_platform");
    expect(plan.profile.tokens["--alf-bg"]).toBe("#ffffff");
    const modules = plan.sections.find((s) => s.type === "modules");
    expect(modules?.bullets.some((b) => b.includes("GlaucoLogic"))).toBe(true);
  });
});
