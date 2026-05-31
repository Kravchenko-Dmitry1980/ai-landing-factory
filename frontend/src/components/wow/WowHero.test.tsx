import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { WowHeroCanvas } from "./WowHeroCanvas";
import { WowHeroFallback } from "./WowHeroFallback";
import { WowHeroMascot } from "./WowHeroMascot";
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
    expect(typeof WowHeroMascot).toBe("function");
    expect(typeof WowHeroOverlay).toBe("function");
    expect(typeof WowMetricStrip).toBe("function");
  });

  it("renders a static fallback while hydrating", () => {
    const src = source("WowHeroCanvas.tsx");
    expect(src).toContain('reason="loading"');
    expect(src).toContain("WowHeroFallback");
  });

  it("uses a pure 2D hero without R3F portal scene", () => {
    const canvas = source("WowHeroCanvas.tsx");
    expect(canvas).toContain("WowHeroBackdrop");
    expect(canvas).not.toContain("WowHeroR3F");
    expect(canvas).not.toContain("dynamic(() => import");
  });

  it("keeps the CTA clickable and metrics anchored in the overlay", () => {
    const src = source("WowHeroOverlay.tsx");
    expect(src).toContain("Смотреть лендинг");
    expect(src).toContain('id="wow-metrics"');
    expect(src).toContain("aria-label");
  });

  it("mounts the cat mascot with 2D UI cards, no portal ring", () => {
    const canvas = source("WowHeroCanvas.tsx");
    const fallback = source("WowHeroFallback.tsx");
    const mascot = source("WowHeroMascot.tsx");
    expect(canvas).toContain("WowHeroMascot");
    expect(fallback).toContain("WowHeroMascot");
    expect(mascot).toContain("wow-hero-ui-card--chart");
    expect(mascot).not.toContain("wow-hero-mascot-portal");
    expect(mascot).not.toContain("wow-hero-mascot-platform");
    expect(source("wowMascotAsset.ts")).toContain("/assets/wow/cat-assistant.png");
  });

  it("mascot uses 2.5D motion rig layers (Stage P.7.7)", () => {
    const mascot = source("WowHeroMascot.tsx");
    const motion = source("wow-mascot-motion.css");
    expect(mascot).toContain("wow-hero-mascot-rig");
    expect(mascot).toContain("wow-hero-mascot-eyelid");
    expect(mascot).toContain("wow-hero-mascot-medallion");
    expect(mascot).toContain("wow-hero-mascot-typing-glow");
    expect(mascot).toContain("prefersReducedMotion");
    expect(motion).toContain("wow-cat-blink");
    expect(motion).toContain("wow-cat-head-sway");
    expect(motion).toContain("wow-cat-typing");
    expect(motion).toContain("wow-cat-medallion-pulse");
    expect(motion).toContain("wow-ui-drift-a");
  });

  it("UII light scene has no portal arch or 3D floating cards", () => {
    const scene = source("WowHeroSceneUiiLight.tsx");
    expect(scene).not.toContain("WowPortalArch");
    expect(scene).not.toContain("WowFloatingCards");
    expect(scene).toContain("WowAmbientDecor");
  });

  it("WowHeroMascot renders standalone cat img, not preview screenshot", () => {
    const html = renderToStaticMarkup(<WowHeroMascot reducedMotion />);
    expect(html).toContain("wow-hero-mascot-image");
    expect(html).toContain("/assets/wow/cat-assistant.png");
    expect(html).toContain("wow-hero-mascot-rig");
    expect(html).toContain("wow-hero-mascot-spotlight");
    expect(html).toContain("wow-hero-mascot-contact-shadow");
    expect(html).not.toContain("wow-hero-mascot-platform");
    expect(html).not.toMatch(/screenshot|mockup|preview-card|landing-preview|hero-preview/i);
  });
});
