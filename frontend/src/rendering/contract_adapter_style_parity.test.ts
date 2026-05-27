import { describe, expect, it } from "vitest";
import { buildRenderPlan } from "./contract_adapter";
import { parseStyleIntent } from "@/lib/styleIntent";
import { buildStyleConfigFromEditor } from "@/lib/styleConfig";
import type { GeneratedLanding, LandingContract } from "@/lib/types";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "corporate",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "Demo", bullets: [] },
    { key: "tasks", title: "Modules", body: "", bullets: ["Mod A", "Mod B"] },
    { key: "team", title: "Team", body: "", bullets: ["Alex — Lead"] },
    { key: "tech_stack", title: "Stack", body: "", bullets: ["Next.js", "FastAPI"] },
  ],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "corporate",
  goals: [],
  presentation_style: null,
  blocks: [],
  updated_at: landing.generated_at,
  version: 1,
};

describe("contract_adapter style parity", () => {
  it("rendered preview uses data-profile matching style", () => {
    for (const preset of ["minimal", "corporate", "tech", "bold"] as const) {
      const styleConfig = buildStyleConfigFromEditor(preset, "");
      const plan = buildRenderPlan(landing, contract, {
        profileId: preset,
        layoutId: "architecture_first",
        styleConfig,
      });
      expect(plan.profileId).toBe(preset);
      expect(plan.profile.id).toBe(preset);
    }
  });

  it("style selection affects module/team/stack sections", () => {
    const minimal = buildRenderPlan(landing, contract, {
      profileId: "minimal",
      layoutId: "architecture_first",
      styleConfig: buildStyleConfigFromEditor("minimal", ""),
    });
    const bold = buildRenderPlan(landing, contract, {
      profileId: "bold",
      layoutId: "architecture_first",
      styleConfig: buildStyleConfigFromEditor("bold", ""),
    });
    expect(minimal.profile.spacing.sectionY).not.toBe(bold.profile.spacing.sectionY);
    expect(minimal.profile.typography.hero).not.toBe(bold.profile.typography.hero);
    expect(minimal.sections.some((s) => s.type === "modules")).toBe(true);
    expect(bold.sections.some((s) => s.type === "team")).toBe(true);
  });

  it("no raw custom prompt injection", () => {
    const evil = "<script>alert(1)</script> { body: red }";
    const plan = buildRenderPlan(landing, contract, {
      profileId: "custom",
      layoutId: "architecture_first",
      styleConfig: {
        profile: "custom",
        custom_style_prompt: evil,
        theme_tokens: parseStyleIntent(evil),
      },
    });
    expect(JSON.stringify(plan)).not.toContain("<script>");
    expect(plan.profileId).toBe("custom");
  });

  it("minimal preview is not corporate/enterprise", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "minimal",
      layoutId: "architecture_first",
      styleConfig: buildStyleConfigFromEditor("minimal", ""),
    });
    expect(plan.profileId).toBe("minimal");
    expect(plan.profile.cardStyle).toBe("flat");
    expect(plan.cssVars["--alf-bg"]).toBe("#ffffff");
  });
});
