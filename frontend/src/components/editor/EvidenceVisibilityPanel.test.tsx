import React from "react";
import { describe, expect, it } from "vitest";
import { renderToStaticMarkup } from "react-dom/server";
import { EvidenceVisibilityPanel } from "./EvidenceVisibilityPanel";
import type { EvidenceVisibility } from "@/lib/types";

const sampleEvidence: EvidenceVisibility = {
  project_id: "p1",
  parser_mode: "multi_source_assembly",
  source_count: 3,
  evidence_count: 42,
  assembly_confidence: 0.87,
  sources: [
    {
      source_id: "s1",
      filename: "01_landing.docx",
      file_type: "docx",
      detected_source_type: "ready_landing_doc",
      source_role: "primary_project_doc",
      evidence_count: 12,
      char_count: 5000,
      slide_count: null,
      page_count: null,
      status: "used",
      notes: ["defines project identity"],
    },
    {
      source_id: "s2",
      filename: "02_glaucologic_presentation.pptx",
      file_type: "pptx",
      detected_source_type: "pptx_project_presentation",
      source_role: "module_presentation",
      evidence_count: 10,
      char_count: 3000,
      slide_count: 8,
      page_count: null,
      status: "used",
      notes: ["enriches module GlaucoLogic"],
    },
    {
      source_id: "s3",
      filename: "03_ai_copilot_presentation.pptx",
      file_type: "pptx",
      detected_source_type: "pptx_project_presentation",
      source_role: "module_presentation",
      evidence_count: 0,
      char_count: 0,
      slide_count: 12,
      page_count: null,
      status: "empty",
      notes: ["no extractable text"],
    },
  ],
  field_sources: {
    title: {
      field_name: "title",
      coverage: "strong",
      confidence: 0.95,
      source_refs: ["01_landing.docx#section:1"],
      reasons: ["primary_project_doc identity source"],
      selected_snippets: ["Эндокринология"],
    },
    modules: {
      field_name: "modules",
      coverage: "strong",
      confidence: 0.9,
      source_refs: [
        "01_landing.docx#section:2",
        "02_glaucologic_presentation.pptx#slide:1",
      ],
      reasons: ["primary modules + module enrichment"],
      selected_snippets: [],
    },
    tech_stack: {
      field_name: "tech_stack",
      coverage: "strong",
      confidence: 0.88,
      source_refs: ["01_landing.docx#section:5"],
      reasons: ["union of stack evidence"],
      selected_snippets: [],
    },
  },
  missing_fields: ["quote"],
  weak_fields: ["results"],
  strong_fields: ["title", "modules", "tech_stack"],
  warnings: [],
  improvement_hints: [
    "Добавьте отчёт или слайд с итогами проекта.",
    "Файл «03_ai_copilot_presentation.pptx» похож на image-only презентацию.",
  ],
};

describe("EvidenceVisibilityPanel", () => {
  it("renders summary parser mode, source count, evidence count", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={sampleEvidence} />,
    );
    expect(html).toContain("multi_source_assembly");
    expect(html).toContain("Sources:");
    expect(html).toContain("42");
  });

  it("renders sources table when expanded content requested via markup", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={sampleEvidence} />,
    );
    expect(html).toContain("Показать источники сборки");
  });

  it("renders primary_project_doc and module_presentation labels in field data", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={sampleEvidence} defaultExpanded />,
    );
    expect(html).toContain("primary_project_doc");
    expect(html).toContain("module_presentation");
  });

  it("renders field coverage for title/modules/tech_stack when expanded", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={sampleEvidence} defaultExpanded />,
    );
    expect(html).toContain("Название");
    expect(html).toContain("Модули");
    expect(html).toContain("Технологический стек");
  });

  it("does not crash when evidence is absent", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={null} parserMode="structured" />,
    );
    expect(html).not.toContain("undefined");
  });

  it("shows improvement hints for missing/weak fields", () => {
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={sampleEvidence} />,
    );
    expect(html).toContain("Что улучшить");
    expect(html).toContain("итогами проекта");
  });

  it("shows team missing hint when team is weak", () => {
    const evidence: EvidenceVisibility = {
      ...sampleEvidence,
      weak_fields: ["team"],
      improvement_hints: ["Добавьте файл или слайд с составом команды."],
      field_sources: {
        team: {
          field_name: "team",
          coverage: "weak",
          confidence: 0.2,
          source_refs: [],
          reasons: [],
          selected_snippets: [],
        },
      },
    };
    const html = renderToStaticMarkup(
      <EvidenceVisibilityPanel evidence={evidence} defaultExpanded />,
    );
    expect(html).toContain("составом команды");
  });
});
