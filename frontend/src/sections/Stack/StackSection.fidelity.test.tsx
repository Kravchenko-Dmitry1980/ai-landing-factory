import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { StackSection } from "./StackSection";
import type { SectionData } from "@/rendering/types";
import { testRenderPlan } from "@/rendering/testPlan";

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
    const plan = testRenderPlan({
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
    });

    const html = renderToStaticMarkup(
      <StackSection section={section} index={0} plan={plan} />,
    );
    expect(html).toContain("AI / LLM");
    expect(html).toContain("Backend / API");
    expect(html).toContain("OpenAI");
    expect(html).toContain("FastAPI");
  });
});
