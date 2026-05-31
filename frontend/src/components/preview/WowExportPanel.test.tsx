import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { WowExportPanel } from "./WowExportPanel";

function panelSource(): string {
  const dir = dirname(fileURLToPath(import.meta.url));
  return readFileSync(join(dir, "WowExportPanel.tsx"), "utf-8");
}

describe("WowExportPanel", () => {
  it("exports a component", () => {
    expect(typeof WowExportPanel).toBe("function");
  });

  it("renders the demo export panel heading", () => {
    expect(panelSource()).toContain("Экспорт для демонстрации");
  });

  it("has a Standard HTML button", () => {
    expect(panelSource()).toContain("Standard HTML");
  });

  it("has a WOW HTML button", () => {
    expect(panelSource()).toMatch(/>\s*WOW HTML\s*</);
  });

  it("has a WOW HTML + 3D runtime button", () => {
    expect(panelSource()).toContain("WOW HTML + 3D runtime");
  });

  it("has an Interactive WOW ZIP button (Stage P.7.2)", () => {
    expect(panelSource()).toContain("Экспорт интерактивного WOW ZIP");
  });

  it("explains how to open the bundle and the file:// workaround", () => {
    const src = panelSource();
    expect(src).toContain("index.html");
    expect(src).toContain("python -m http.server");
  });

  it("shows the WOW helper text", () => {
    expect(panelSource()).toContain("презентационная версия проекта");
  });

  it("shows the standard-stays-stable safety text", () => {
    expect(panelSource()).toContain(
      "Standard export остаётся обычной стабильной версией",
    );
  });

  it("wires four distinct handlers", () => {
    const src = panelSource();
    expect(src).toContain("onStandard");
    expect(src).toContain("onWow");
    expect(src).toContain("onWow3d");
    expect(src).toContain("onWowBundle");
  });
});
