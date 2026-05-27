import { describe, expect, it } from "vitest";
import {
  DEFAULT_STYLE_CONFIG,
  PRESET_THEME_TOKENS,
  buildStyleConfigFromEditor,
  legacyStyleToProfile,
  profileToStyleProfileId,
  styleConfigToExportTheme,
} from "./styleConfig";

describe("styleConfig presets", () => {
  it("default is university_platform", () => {
    expect(DEFAULT_STYLE_CONFIG.profile).toBe("university_platform");
  });

  it("each preset maps to unique export theme", () => {
    const themes = new Set(
      (["university_platform", "minimal", "corporate", "tech", "bold", "custom"] as const).map(
        (p) => styleConfigToExportTheme(buildStyleConfigFromEditor(p, "")),
      ),
    );
    expect(themes.size).toBe(6);
    expect(themes.has("enterprise_dark")).toBe(false);
  });

  it("tech export theme is tech not enterprise_dark", () => {
    expect(styleConfigToExportTheme(buildStyleConfigFromEditor("tech", ""))).toBe("tech");
    expect(profileToStyleProfileId("tech")).toBe("ai_research");
  });

  it("legacy minimal maps to minimal profile not enterprise", () => {
    expect(legacyStyleToProfile("minimal", null, false)).toBe("minimal");
  });

  it("preset tokens differ between minimal and tech", () => {
    expect(PRESET_THEME_TOKENS.minimal.color_scheme).toBe("light");
    expect(PRESET_THEME_TOKENS.tech.color_scheme).toBe("dark");
  });
});
