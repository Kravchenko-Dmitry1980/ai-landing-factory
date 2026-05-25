import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { ProjectSourceStatusPanel } from "./ProjectSourceStatusPanel";
import type { EvidenceVisibility, LandingContract } from "@/lib/types";

const baseContract: LandingContract = {
  project_id: "p1",
  status: "draft",
  style: "minimal",
  client: null,
  goals: [],
  presentation_style: null,
  visual_assets: [],
  blocks: [],
  updated_at: "2026-05-25T10:00:00Z",
  version: 3,
  fidelity: {
    parser_mode: "multi_source_assembly",
    source_count: 2,
    team_structured: [],
    missing_fields: ["team"],
  },
};

const evidenceTwoSources: EvidenceVisibility = {
  project_id: "p1",
  parser_mode: "multi_source_assembly",
  source_count: 2,
  evidence_count: 10,
  assembly_confidence: 0.8,
  sources: [],
  field_sources: {
    team: {
      field_name: "team",
      coverage: "missing",
      confidence: 0,
      source_refs: [],
      reasons: [],
      selected_snippets: [],
    },
  },
  missing_fields: ["team"],
  weak_fields: [],
  strong_fields: [],
  warnings: [],
  improvement_hints: [],
};

describe("ProjectSourceStatusPanel", () => {
  it("shows single-file warning when source_count=1", () => {
    const html = renderToStaticMarkup(
      <ProjectSourceStatusPanel
        contract={{
          ...baseContract,
          fidelity: { ...baseContract.fidelity!, source_count: 1 },
        }}
        evidence={{ ...evidenceTwoSources, source_count: 1 }}
        landing={null}
      />,
    );
    expect(html).toContain("Загружен только один файл");
    expect(html).toContain("PPTX + DOCX/TXT");
  });

  it("shows team missing hint", () => {
    const html = renderToStaticMarkup(
      <ProjectSourceStatusPanel
        contract={baseContract}
        evidence={evidenceTwoSources}
        landing={null}
      />,
    );
    expect(html).toContain("Команда:");
    expect(html).toContain("missing");
    expect(html).toContain("Для команды загрузите DOCX/TXT");
  });

  it("shows stale warning when contract newer than landing without team block", () => {
    const html = renderToStaticMarkup(
      <ProjectSourceStatusPanel
        contract={{
          ...baseContract,
          updated_at: "2026-05-25T12:00:00Z",
          fidelity: {
            ...baseContract.fidelity!,
            team_structured: [
              {
                name: "Иванов Иван",
                role: "Dev",
                project_area: "",
                contributions: [],
              },
            ],
            missing_fields: [],
          },
        }}
        evidence={evidenceTwoSources}
        landing={{
          project_id: "p1",
          style: "minimal",
          blocks: [{ key: "essence", title: "Суть", body: "", bullets: [] }],
          generated_at: "2026-05-25T10:00:00Z",
          prompt_version: "stub",
        }}
      />,
    );
    expect(html).toContain("устаревш");
  });
});
