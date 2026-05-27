import { describe, expect, it } from "vitest";
import {
  buildRenderPlan,
  defaultRenderConfig,
  resolveExportTheme,
  resolveActiveProfileId,
  buildPreviewHref,
} from "./contract_adapter";
import type { GeneratedLanding, LandingContract } from "@/lib/types";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "corporate",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "AI Landing Factory", bullets: [] },
    { key: "essence", title: "Essence", body: "Content-first pipeline", bullets: [] },
    { key: "tasks", title: "Tasks", body: "", bullets: ["Task A", "Task B"] },
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

describe("buildRenderPlan", () => {
  it("orders sections per layout preset", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "enterprise",
      layoutId: "architecture_first",
    });
    const types = plan.sections.map((s) => s.type);
    expect(types[0]).toBe("hero");
    expect(types).toContain("architecture");
    expect(types.indexOf("architecture")).toBeLessThan(types.indexOf("footer"));
  });

  it("defaults to university_platform when no style saved", () => {
    const cfg = defaultRenderConfig(landing, contract);
    expect(cfg.profileId).toBe("university_platform");
  });

  it("runs hallmark gate", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "ai_research",
      layoutId: "technical_system",
    });
    expect(Array.isArray(plan.hallmarkViolations)).toBe(true);
  });
});

describe("resolveExportTheme", () => {
  it("maps university_platform profile to export theme query", () => {
    expect(
      resolveExportTheme(
        { profileId: "university_platform", layoutId: "technical_system" },
        contract,
        null,
        landing,
      ),
    ).toBe("university_platform");
  });

  it("prefers url style for export theme", () => {
    expect(resolveExportTheme(null, contract, "university_platform", landing)).toBe(
      "university_platform",
    );
  });

  it("returns enterprise_dark for enterprise render profile", () => {
    expect(
      resolveExportTheme(
        {
          profileId: "enterprise",
          layoutId: "technical_system",
          styleConfig: { profile: "minimal" },
        },
        contract,
        null,
        landing,
      ),
    ).toBe("enterprise_dark");
  });

  it("export defaults to university_platform", () => {
    expect(resolveExportTheme(null, contract, null, landing)).toBe("university_platform");
  });

  it("buildPreviewHref includes style query", () => {
    expect(buildPreviewHref("abc", "university_platform")).toBe(
      "/preview/abc?style=university_platform",
    );
  });

  it("resolveActiveProfileId prefers url over renderConfig", () => {
    expect(
      resolveActiveProfileId(
        { profileId: "medical", layoutId: "technical_system" },
        contract,
        "university_platform",
        landing,
      ),
    ).toBe("university_platform");
  });
});
