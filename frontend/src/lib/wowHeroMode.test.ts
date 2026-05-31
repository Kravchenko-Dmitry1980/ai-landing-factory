import { describe, expect, it } from "vitest";
import {
  parseWowHeroMode,
  isWowMode,
  sceneIntensity,
} from "./wowHeroMode";

describe("parseWowHeroMode", () => {
  it("defaults to standard when missing", () => {
    expect(parseWowHeroMode(null)).toBe("standard");
    expect(parseWowHeroMode(undefined)).toBe("standard");
    expect(parseWowHeroMode("")).toBe("standard");
  });

  it("parses valid modes case-insensitively", () => {
    expect(parseWowHeroMode("wow")).toBe("wow");
    expect(parseWowHeroMode("WOW3D")).toBe("wow3d");
    expect(parseWowHeroMode(" Wow ")).toBe("wow");
  });

  it("falls back to standard for unknown values", () => {
    expect(parseWowHeroMode("fancy")).toBe("standard");
    expect(parseWowHeroMode("3d")).toBe("standard");
  });
});

describe("isWowMode", () => {
  it("is true only for wow / wow3d", () => {
    expect(isWowMode("standard")).toBe(false);
    expect(isWowMode("wow")).toBe(true);
    expect(isWowMode("wow3d")).toBe(true);
  });
});

describe("sceneIntensity", () => {
  it("maps wow -> lite and wow3d -> full", () => {
    expect(sceneIntensity("wow")).toBe("lite");
    expect(sceneIntensity("wow3d")).toBe("full");
    expect(sceneIntensity("standard")).toBe("lite");
  });
});
