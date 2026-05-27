import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ModulesSection } from "./ModulesSection";
import type { SectionData } from "@/rendering/types";
import { testRenderPlan } from "@/rendering/testPlan";

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
        plan={testRenderPlan({
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
