import { describe, expect, it } from "vitest";
import { heroModeClass, motionClass } from "@/design/applyThemeTokens";
import { buildSectionNavItems, SECTION_NAV_ORDER } from "@/rendering/sectionAnchors";
import { buildRenderPlan } from "@/rendering/contract_adapter";
import { parseStyleIntent } from "@/lib/styleIntent";
import type { GeneratedLanding, LandingContract } from "@/lib/types";

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "tech",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "Test", bullets: [] },
    { key: "essence", title: "Суть", body: "Essence body", bullets: [] },
    { key: "tasks", title: "Задачи", body: "", bullets: ["Task A", "Task B"] },
    { key: "team", title: "Команда", body: "", bullets: ["Alex — Lead"] },
    { key: "outlook", title: "Перспектива", body: "", bullets: ["Next step"] },
  ],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "tech",
  client: null,
  goals: [],
  presentation_style: null,
  blocks: [],
  updated_at: landing.generated_at,
  version: 1,
};

describe("interactive landing P.4", () => {
  it("future_3d adds alf-hero--future-3d class", () => {
    expect(heroModeClass("future_3d")).toBe("alf-hero--future-3d");
  });

  it("motion none adds alf-motion--none class", () => {
    expect(motionClass("none")).toBe("alf-motion--none");
  });

  it("buildSectionNavItems returns expected Russian labels", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "tech",
      layoutId: "architecture_first",
      styleConfig: { profile: "tech" },
    });
    const items = buildSectionNavItems(plan.sections);
    const labels = items.map((i) => i.label);
    expect(labels).toContain("Суть");
    expect(labels).toContain("Задачи");
    expect(labels).toContain("Команда");
    expect(labels).toContain("Перспектива");
    expect(SECTION_NAV_ORDER.map((i) => i.id)).toContain("essence");
  });

  it("custom 3D prompt sets future_3d tokens without script leak", () => {
    const prompt = "тёмный технологичный стиль с синим акцентом и 3D карточками";
    const tokens = parseStyleIntent(prompt);
    const plan = buildRenderPlan(landing, contract, {
      profileId: "custom",
      layoutId: "architecture_first",
      styleConfig: {
        profile: "custom",
        custom_style_prompt: prompt,
        theme_tokens: tokens,
      },
    });
    expect(plan.normalizedTokens.heroMode).toBe("future_3d");
    expect(heroModeClass(plan.normalizedTokens.heroMode)).toBe("alf-hero--future-3d");
    expect(JSON.stringify(plan)).not.toContain("<script>");
  });

  it("section ids align with export anchors", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "tech",
      layoutId: "architecture_first",
      styleConfig: { profile: "tech" },
    });
    const ids = plan.sections.map((s) => s.id);
    expect(ids).toContain("hero");
    expect(ids).toContain("essence");
    expect(ids).toContain("tasks");
    expect(ids).toContain("team");
    expect(ids).toContain("outlook");
  });
});
