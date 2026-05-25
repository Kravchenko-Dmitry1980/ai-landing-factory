import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ModulesSection } from "./ModulesSection";
import type { RenderPlan, SectionData } from "@/rendering/types";
import { getLayoutPreset } from "@/design/layout_presets";
import { getStyleProfile } from "@/design/style_profiles";

function minimalPlan(overrides: Partial<RenderPlan>): RenderPlan {
  const profileId = overrides.profileId ?? "university_platform";
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

const section: SectionData = {
  id: "modules-tasks",
  type: "modules",
  title: "Ключевые системы",
  body: "",
  bullets: ["Fallback"],
  sourceKeys: ["tasks"],
};

describe("ModulesSection fidelity", () => {
  it("renders GlaucoLogic / Copilot / VitaCalc as cards", () => {
    const html = renderToStaticMarkup(
      <ModulesSection
        section={section}
        index={0}
        plan={minimalPlan({
          modules: [
            { name: "GlaucoLogic", description: "OCT", type: "AI" },
            { name: "Copilot врача", description: "Docs", type: "Platform" },
            { name: "VitaCalc", description: "Nutrition", type: "Calc" },
          ],
          fidelityDiagnostics: {
            modulesSource: "fidelity",
            teamSource: "fallback",
            stackSource: "fallback",
            modulesCount: 3,
            teamCount: 0,
            stackCategoriesCount: 0,
          },
        })}
      />,
    );
    expect(html).toContain("GlaucoLogic");
    expect(html).toContain("Copilot врача");
    expect(html).toContain("VitaCalc");
    expect(html).not.toContain("Module 1");
  });
});
