import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StackSection } from "./StackSection";
import type { RenderPlan, SectionData } from "@/rendering/types";
import { getLayoutPreset } from "@/design/layout_presets";
import { getStyleProfile } from "@/design/style_profiles";

const section: SectionData = {
  id: "stack-main",
  type: "stack",
  title: "Используемый технологический стек",
  body: "",
  bullets: ["Python"],
  sourceKeys: ["tech_stack"],
};

describe("StackSection fidelity", () => {
  it("renders grouped categories and tags", () => {
    const plan: RenderPlan = {
      meta: {
        projectId: "p1",
        title: "Test",
        client: null,
        timeline: null,
        lead: null,
        version: 1,
        updatedAt: null,
      },
      profile: getStyleProfile("university_platform"),
      layout: getLayoutPreset("architecture_first"),
      profileId: "university_platform",
      layoutId: "architecture_first",
      sections: [],
      modules: [],
      team: [],
      stackGrouped: {
        "AI / LLM": ["OpenAI"],
        "Backend / API": ["FastAPI"],
      },
      fidelityDiagnostics: {
        modulesSource: "fallback",
        teamSource: "fallback",
        stackSource: "fidelity",
        modulesCount: 0,
        teamCount: 0,
        stackCategoriesCount: 2,
      },
      hallmarkViolations: [],
      builtAt: Date.now(),
    };

    const html = renderToStaticMarkup(
      <StackSection section={section} index={0} plan={plan} />,
    );
    expect(html).toContain("AI / LLM");
    expect(html).toContain("Backend / API");
    expect(html).toContain("OpenAI");
    expect(html).toContain("FastAPI");
  });
});
