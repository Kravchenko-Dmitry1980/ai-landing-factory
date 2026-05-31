import { describe, expect, it } from "vitest";
import {
  createDefaultShowcaseTemplate,
  createEmptyShowcaseRequest,
} from "./showcaseTemplates";

describe("createDefaultShowcaseTemplate", () => {
  it("uii_ai_projects has correct title, subtitle and organization", () => {
    const req = createDefaultShowcaseTemplate("uii_ai_projects");
    expect(req.title).toBe("Витрина AI-проектов УИИ");
    expect(req.subtitle).toMatch(/VR\/AR/);
    expect(req.organization).toBe("Университет искусственного интеллекта");
  });

  it("uses gallery_arc layout", () => {
    expect(createDefaultShowcaseTemplate().layout).toBe("gallery_arc");
  });

  it("uses tech theme and vr_ready mode", () => {
    const req = createDefaultShowcaseTemplate();
    expect(req.theme).toBe("tech");
    expect(req.mode).toBe("vr_ready");
  });

  it("returns a valid create request with required title", () => {
    const req = createDefaultShowcaseTemplate();
    expect(req.title.trim().length).toBeGreaterThan(0);
  });
});

describe("createEmptyShowcaseRequest", () => {
  it("returns a minimal title-only payload", () => {
    expect(createEmptyShowcaseRequest()).toEqual({ title: "Новая витрина" });
  });
});
