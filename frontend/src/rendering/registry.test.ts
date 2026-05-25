import { describe, expect, it } from "vitest";
import { listRegisteredSectionTypes, SECTION_REGISTRY } from "./registry";

describe("section registry", () => {
  it("registers all required section types", () => {
    const types = listRegisteredSectionTypes();
    expect(types).toContain("hero");
    expect(types).toContain("architecture");
    expect(types).toContain("metrics");
    expect(types.length).toBeGreaterThanOrEqual(9);
  });

  it("resolves components without throw", () => {
    for (const type of listRegisteredSectionTypes()) {
      expect(SECTION_REGISTRY[type]).toBeDefined();
    }
  });
});
