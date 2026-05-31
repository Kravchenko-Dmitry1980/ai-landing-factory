import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { WowHeroCanvas } from "./WowHeroCanvas";
import { WowHeroFallback } from "./WowHeroFallback";
import { WowHeroOverlay } from "./WowHeroOverlay";
import { WowMetricStrip } from "./WowMetricStrip";

function source(file: string): string {
  const dir = dirname(fileURLToPath(import.meta.url));
  return readFileSync(join(dir, file), "utf-8");
}

describe("WOW hero components", () => {
  it("export components", () => {
    expect(typeof WowHeroCanvas).toBe("function");
    expect(typeof WowHeroFallback).toBe("function");
    expect(typeof WowHeroOverlay).toBe("function");
    expect(typeof WowMetricStrip).toBe("function");
  });

  it("renders a static fallback before WebGL is confirmed and when unavailable", () => {
    const src = source("WowHeroCanvas.tsx");
    expect(src).toContain('reason="loading"');
    expect(src).toContain('reason="no-webgl"');
    expect(src).toContain("isWebGLAvailable");
  });

  it("loads the R3F canvas client-only via next/dynamic ssr:false", () => {
    const src = source("WowHeroCanvas.tsx");
    expect(src).toContain("dynamic(() => import(\"./WowHeroR3F\")");
    expect(src).toContain("ssr: false");
  });

  it("keeps the CTA clickable and metrics anchored in the overlay", () => {
    const src = source("WowHeroOverlay.tsx");
    expect(src).toContain("Смотреть лендинг");
    expect(src).toContain('id="wow-metrics"');
    expect(src).toContain("aria-label");
  });

  it("supports reduced motion in the scene", () => {
    const src = source("WowHeroScene.tsx");
    expect(src).toContain("reducedMotion");
    const r3f = source("WowHeroR3F.tsx");
    expect(r3f).toContain('frameloop={reducedMotion ? "demand" : "always"}');
  });
});
