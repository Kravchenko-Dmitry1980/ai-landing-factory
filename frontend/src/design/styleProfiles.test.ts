import { describe, expect, it } from "vitest";
import {
  getStyleProfile,
  isStyleProfileId,
  STYLE_PROFILE_IDS,
  STYLE_PROFILES,
} from "@/design/styleProfiles";

describe("styleProfiles", () => {
  it("all six profiles exist", () => {
    expect(STYLE_PROFILE_IDS).toHaveLength(6);
    for (const id of STYLE_PROFILE_IDS) {
      expect(STYLE_PROFILES[id]).toBeDefined();
      expect(STYLE_PROFILES[id].id).toBe(id);
    }
  });

  it("each profile has distinct id and baseTokens", () => {
    const presets = STYLE_PROFILE_IDS.filter((id) => id !== "custom");
    const tokenKeys = presets.map(
      (id) => JSON.stringify(STYLE_PROFILES[id].baseTokens),
    );
    const unique = new Set(tokenKeys);
    expect(unique.size).toBe(presets.length);
    expect(STYLE_PROFILES.custom.id).toBe("custom");
  });

  it("tech profile is dark with gradient hero", () => {
    const tech = getStyleProfile("tech");
    expect(tech.baseTokens.color_scheme).toBe("dark");
    expect(tech.heroStyle).toBe("gradient");
    expect(tech.baseTokens.hero_mode).toBe("gradient");
  });

  it("minimal is light and spacious", () => {
    const minimal = getStyleProfile("minimal");
    expect(minimal.baseTokens.color_scheme).toBe("light");
    expect(minimal.layoutDensity).toBe("spacious");
    expect(minimal.motion).toBe("none");
  });

  it("bold has expressive motion", () => {
    const bold = getStyleProfile("bold");
    expect(bold.motion).toBe("expressive");
    expect(bold.baseTokens.motion).toBe("expressive");
  });

  it("isStyleProfileId accepts export ids only", () => {
    expect(isStyleProfileId("tech")).toBe(true);
    expect(isStyleProfileId("enterprise")).toBe(false);
  });
});
