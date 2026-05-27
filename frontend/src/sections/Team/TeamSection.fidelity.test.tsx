import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { TeamSection } from "./TeamSection";
import type { SectionData } from "@/rendering/types";
import { testRenderPlan } from "@/rendering/testPlan";

const section: SectionData = {
  id: "team-main",
  type: "team",
  title: "Команда проекта",
  body: "",
  bullets: [],
  sourceKeys: ["team"],
};

function planWithTeam() {
  const contributions = Array.from({ length: 6 }, (_, i) => `Contribution ${i + 1}`);
  return testRenderPlan({
    team: [
      {
        name: "Alice Dev",
        role: "Backend Lead",
        project_area: "API",
        contributions,
      },
    ],
    fidelityDiagnostics: {
      modulesSource: "fallback",
      teamSource: "fidelity",
      stackSource: "fallback",
      modulesCount: 0,
      teamCount: 1,
      stackCategoriesCount: 0,
    },
  });
}

describe("TeamSection fidelity", () => {
  it("renders participant name and role", () => {
    const html = renderToStaticMarkup(
      <TeamSection section={section} index={0} plan={planWithTeam()} />,
    );
    expect(html).toContain("Alice Dev");
    expect(html).toContain("Backend Lead");
  });

  it("collapses long contributions in details", () => {
    const html = renderToStaticMarkup(
      <TeamSection section={section} index={0} plan={planWithTeam()} />,
    );
    expect(html).toContain("Вклад участника");
    expect(html).toContain("<details");
    expect(html).toContain("Contribution 6");
  });
});
