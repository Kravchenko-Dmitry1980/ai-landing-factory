import { describe, expect, it } from "vitest";
import { readFileSync, readdirSync } from "node:fs";
import { join } from "node:path";
import {
  containsUnsafeTokenValue,
  normalizeThemeTokens,
  serializeThemeTokens,
  themeTokensToCssVars,
} from "./themeTokens";
import { buildStyleConfigFromEditor } from "@/lib/styleConfig";
import type { LandingStyleConfig } from "@/lib/types";

const FIXTURE_DIR = join(__dirname, "__fixtures__", "theme_tokens");

interface FixtureCase {
  id: string;
  styleConfig: LandingStyleConfig;
  expected: Partial<ReturnType<typeof serializeThemeTokens>>;
}

function loadFixtures(): FixtureCase[] {
  return readdirSync(FIXTURE_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(readFileSync(join(FIXTURE_DIR, f), "utf8")) as FixtureCase);
}

describe("themeTokens contract", () => {
  it("every profile preset produces full token set", () => {
    for (const profile of [
      "university_platform",
      "minimal",
      "corporate",
      "tech",
      "bold",
      "custom",
    ] as const) {
      const tokens = normalizeThemeTokens(buildStyleConfigFromEditor(profile, ""));
      expect(tokens.bg).toBeTruthy();
      expect(tokens.accent).toMatch(/^#/);
      expect(tokens.radiusPx).toBeGreaterThan(0);
      expect(tokens.gapRem).toBeGreaterThan(0);
    }
  });

  it("no token value contains raw script/css", () => {
    const evil = buildStyleConfigFromEditor(
      "custom",
      "<script>alert(1)</script> body { display:none }",
    );
    const tokens = normalizeThemeTokens(evil);
    const serialized = JSON.stringify(tokens);
    expect(serialized).not.toContain("<script>");
    expect(Object.values(tokens).every((v) => !containsUnsafeTokenValue(String(v)))).toBe(
      true,
    );
  });

  it("custom prompt maps to safe token set", () => {
    const cfg = buildStyleConfigFromEditor(
      "custom",
      "тёмный технологичный стиль с синим акцентом и 3D карточками",
    );
    const tokens = normalizeThemeTokens(cfg);
    expect(tokens.colorScheme).toBe("dark");
    expect(tokens.accent).toBe("#2563eb");
    expect(tokens.heroMode).toBe("future_3d");
  });

  it("css vars include alf and compatibility aliases", () => {
    const vars = themeTokensToCssVars(
      normalizeThemeTokens(buildStyleConfigFromEditor("tech", "")),
    );
    expect(vars["--alf-bg"]).toBe("#0f172a");
    expect(vars["--bg"]).toBe("var(--alf-bg)");
    expect(vars["--alf-hero-gradient"]).toContain("gradient");
  });

  it.each(loadFixtures())("fixture parity: $id", (fixture) => {
    const tokens = serializeThemeTokens(fixture.styleConfig);
    for (const [key, value] of Object.entries(fixture.expected)) {
      expect(tokens[key as keyof typeof tokens]).toEqual(value);
    }
  });
});
