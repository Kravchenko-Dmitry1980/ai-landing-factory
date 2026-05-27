import { describe, expect, it } from "vitest";
import {
  resolveExportTheme,
  resolvePreviewProfile,
  resolvePreviewProfileId,
  resolveStyleConfig,
} from "@/lib/resolveStyleConfig";
import { buildStyleConfigFromEditor } from "@/lib/styleConfig";
import { parseStyleIntent } from "@/lib/styleIntent";
import type { LandingContract } from "@/lib/types";

const baseContract: LandingContract = {
  project_id: "00000000-0000-0000-0000-000000000001",
  status: "draft",
  style: "corporate",
  goals: [],
  presentation_style: null,
  blocks: [],
  updated_at: new Date().toISOString(),
  version: 1,
};

describe("resolveStyleConfig", () => {
  it("default → university_platform", () => {
    const cfg = resolveStyleConfig(null);
    expect(cfg.profile).toBe("university_platform");
    expect(resolvePreviewProfileId(cfg)).toBe("university_platform");
    expect(resolveExportTheme(cfg)).toBe("university_platform");
  });

  it("tech style_config → preview tech + export tech", () => {
    const cfg = buildStyleConfigFromEditor("tech", "");
    const resolved = resolveStyleConfig(
      { ...baseContract, style_config: cfg },
      cfg,
    );
    expect(resolvePreviewProfileId(resolved)).toBe("tech");
    expect(resolveExportTheme(resolved)).toBe("tech");
    expect(resolvePreviewProfile(resolved).id).toBe("tech");
  });

  it("bold style_config → preview bold + export bold", () => {
    const cfg = buildStyleConfigFromEditor("bold", "");
    expect(resolvePreviewProfileId(cfg)).toBe("bold");
    expect(resolveExportTheme(cfg)).toBe("bold");
  });

  it("custom prompt tokens → preview custom + export custom", () => {
    const tokens = parseStyleIntent(
      "тёмный технологичный стиль с синим акцентом и 3D карточками",
    );
    const cfg = buildStyleConfigFromEditor(
      "custom",
      "тёмный технологичный стиль с синим акцентом и 3D карточками",
      tokens,
    );
    expect(resolveExportTheme(cfg)).toBe("custom");
    const profile = resolvePreviewProfile(cfg);
    expect(profile.id).toBe("custom");
    expect(profile.baseTokens.color_scheme).toBe("dark");
    expect(profile.baseTokens.accent).toBe("blue");
  });

  it("legacy minimal does not map to enterprise for new contract", () => {
    const cfg = resolveStyleConfig({
      ...baseContract,
      style: "minimal",
      style_config: buildStyleConfigFromEditor("minimal", ""),
    });
    expect(resolvePreviewProfileId(cfg)).toBe("minimal");
    expect(resolvePreviewProfileId(cfg)).not.toBe("corporate");
  });
});
