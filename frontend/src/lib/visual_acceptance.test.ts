import { describe, expect, it } from "vitest";
import {
  buildSyntheticPreviewHtml,
  comparePreviewExportMarkers,
  detectDarkThemeMarkers,
  detectRequiredMarkers,
  summarizeChecks,
  validateExportHtml,
  validatePreviewHtml,
} from "./visual_acceptance";

const SAMPLE_EXPORT_HTML = `<!DOCTYPE html>
<html><head><style>
:root { --accent: #7C3AED; --bg: #ffffff; }
.container { max-width: 1200px; }
</style></head>
<body class="theme-university_platform">
<h1>Эндокринология+</h1>
<section id="modules">
  <div class="card module-card"><h3>GlaucoLogic</h3></div>
  <div class="card module-card"><h3>Copilot врача</h3></div>
  <div class="card module-card"><h3>VitaCalc</h3></div>
</section>
<section id="stack"><h2>Используемый технологический стек</h2>
  <div class="stack-group"><span class="stack-tag">Python</span></div>
  <div class="stack-group"><span class="stack-tag">FastAPI</span></div>
  <div class="stack-group"><span class="stack-tag">Next.js</span></div>
  <div class="stack-group"><span class="stack-tag">PostgreSQL</span></div>
  <div class="stack-group"><span class="stack-tag">Redis</span></div>
</section>
<section id="team"><h2>Команда проекта</h2>
  ${Array.from({ length: 15 }, (_, i) => `<div class="team-card">Member ${i}</div>`).join("")}
</section>
</body></html>`;

const SAMPLE_PREVIEW_HTML = `<div data-profile="university_platform" style="--alf-bg:#ffffff">
<h1>Эндокринология+</h1>
<h3>GlaucoLogic</h3><h3>Copilot врача</h3><h3>VitaCalc</h3>
<h2>Команда проекта</h2>
<h2>Используемый технологический стек</h2>
<span>#7C3AED</span>
</div>`;

const DARK_EXPORT_HTML = `<style>--bg: #0f1419; max-width: 720px;</style>
<h1>Project Landing</h1>`;

describe("visual_acceptance markers", () => {
  it("detectRequiredMarkers finds export tokens", () => {
    const results = detectRequiredMarkers(SAMPLE_EXPORT_HTML, "export");
    expect(summarizeChecks(results)).toBe(true);
  });

  it("detectRequiredMarkers finds preview tokens", () => {
    const results = detectRequiredMarkers(SAMPLE_PREVIEW_HTML, "preview");
    expect(summarizeChecks(results)).toBe(true);
  });

  it("detectDarkThemeMarkers flags enterprise fallback", () => {
    const results = detectDarkThemeMarkers(DARK_EXPORT_HTML);
    expect(results.some((r) => !r.ok && r.label.includes("0f1419"))).toBe(true);
    expect(results.some((r) => !r.ok && r.label.includes("720px"))).toBe(true);
    expect(results.some((r) => !r.ok && r.label.includes("Project Landing"))).toBe(true);
  });

  it("comparePreviewExportMarkers requires modules in both", () => {
    const results = comparePreviewExportMarkers(SAMPLE_PREVIEW_HTML, SAMPLE_EXPORT_HTML);
    expect(summarizeChecks(results)).toBe(true);
  });

  it("comparePreviewExportMarkers fails when export missing module", () => {
    const badExport = SAMPLE_EXPORT_HTML.replace("VitaCalc", "");
    const results = comparePreviewExportMarkers(SAMPLE_PREVIEW_HTML, badExport);
    expect(summarizeChecks(results)).toBe(false);
  });

  it("validateExportHtml passes sample university export", () => {
    expect(summarizeChecks(validateExportHtml(SAMPLE_EXPORT_HTML))).toBe(true);
  });

  it("validatePreviewHtml passes sample preview DOM", () => {
    expect(summarizeChecks(validatePreviewHtml(SAMPLE_PREVIEW_HTML))).toBe(true);
  });

  it("buildSyntheticPreviewHtml includes fidelity fields", () => {
    const html = buildSyntheticPreviewHtml({
      title: "Эндокринология+",
      fidelity: {
        modules: [
          { name: "GlaucoLogic", description: "AI", type: "ML" },
          { name: "Copilot врача" },
          { name: "VitaCalc" },
        ],
        team_structured: Array.from({ length: 16 }, (_, i) => ({
          name: `Member ${i}`,
          role: "Dev",
        })),
        tech_stack_grouped: {
          Backend: ["Python"],
          Frontend: ["Next.js"],
          Data: ["PostgreSQL"],
          Infra: ["Docker"],
          AI: ["OpenAI"],
        },
      },
      blocks: [{ key: "essence", content: "Long essence text ".repeat(50) }],
    });
    expect(html).toContain("Эндокринология+");
    expect(html).toContain("GlaucoLogic");
    expect(html).toContain("Copilot врача");
    expect(html).toContain("VitaCalc");
    expect(html).toContain("Команда проекта");
    expect(summarizeChecks(validatePreviewHtml(html))).toBe(true);
  });
});
