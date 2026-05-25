import { describe, expect, it } from "vitest";
import { LAYOUT_PRESETS } from "./layout_presets";

describe("layout presets", () => {
  it("includes architecture_first with hero first", () => {
    const preset = LAYOUT_PRESETS.architecture_first;
    expect(preset.sectionOrder[0]).toBe("hero");
    expect(preset.sectionOrder).toContain("architecture");
    expect(preset.gridLogic).toBe("two-column");
  });

  it("dashboard places metrics early", () => {
    const preset = LAYOUT_PRESETS.dashboard;
    expect(preset.sectionOrder.indexOf("metrics")).toBeLessThan(
      preset.sectionOrder.indexOf("footer"),
    );
  });
});
