import { describe, expect, it } from "vitest";
import { computeShowcaseReadiness } from "./showcaseReadiness";
import type { ShowcaseConfig } from "./showcase";

function baseConfig(overrides?: Partial<ShowcaseConfig>): ShowcaseConfig {
  return {
    id: "s1",
    title: "Витрина",
    layout: "gallery_arc",
    mode: "vr_ready",
    theme: "tech",
    projects: [],
    ...overrides,
  };
}

describe("computeShowcaseReadiness", () => {
  it("empty showcase is not ready", () => {
    const report = computeShowcaseReadiness(baseConfig());
    expect(report.ready).toBe(false);
    expect(report.checks.some((c) => c.id === "projects" && c.status === "warning")).toBe(
      true,
    );
  });

  it("projects without demo links produce a warning", () => {
    const report = computeShowcaseReadiness(
      baseConfig({
        projects: [
          {
            id: "p1",
            title: "A",
            description: "",
            landing_url: "/preview/a",
            tags: [],
            order_index: 0,
          },
        ],
      }),
    );
    expect(report.ready).toBe(false);
    expect(report.checks.some((c) => c.id === "demo_links" && c.status === "warning")).toBe(
      true,
    );
  });

  it("showcase with demo links is ready", () => {
    const report = computeShowcaseReadiness(
      baseConfig({
        projects: [
          {
            id: "p1",
            title: "A",
            description: "",
            landing_url: "/preview/a",
            demo_url: "https://aistudio.google.com/",
            tags: [],
            order_index: 0,
          },
        ],
      }),
    );
    expect(report.ready).toBe(true);
    expect(report.checks.some((c) => c.id === "demo_links" && c.status === "ok")).toBe(
      true,
    );
  });

  it("includes ZIP readiness message", () => {
    const report = computeShowcaseReadiness(baseConfig());
    expect(report.checks.some((c) => c.id === "zip_export")).toBe(true);
    expect(report.checks.find((c) => c.id === "zip_export")?.label).toMatch(/ZIP/i);
  });

  it("includes demo internet warning", () => {
    const report = computeShowcaseReadiness(baseConfig());
    expect(report.checks.some((c) => c.id === "demo_internet")).toBe(true);
    expect(report.checks.find((c) => c.id === "demo_internet")?.label).toMatch(
      /интернет/i,
    );
  });
});
