import { describe, expect, it } from "vitest";
import {
  createEmptyProject,
  isSafeShowcaseUrl,
  toShowcasePayload,
  validateShowcaseConfig,
  type ShowcaseConfigInput,
} from "./showcase";

function baseConfig(overrides?: Partial<ShowcaseConfigInput>): ShowcaseConfigInput {
  return {
    title: "Витрина",
    layout: "gallery_arc",
    mode: "web3d",
    theme: "university",
    projects: [
      {
        ...createEmptyProject(),
        title: "Проект 1",
        description: "Описание",
        demo_url: "https://aistudio.google.com/",
      },
    ],
    ...overrides,
  };
}

describe("isSafeShowcaseUrl", () => {
  it("accepts https and relative paths", () => {
    expect(isSafeShowcaseUrl("https://example.com")).toBe(true);
    expect(isSafeShowcaseUrl("/landings/x")).toBe(true);
    expect(isSafeShowcaseUrl("")).toBe(true);
    expect(isSafeShowcaseUrl(undefined)).toBe(true);
  });

  it("rejects dangerous schemes", () => {
    expect(isSafeShowcaseUrl("javascript:alert(1)")).toBe(false);
    expect(isSafeShowcaseUrl("data:text/html,<script>")).toBe(false);
    expect(isSafeShowcaseUrl("vbscript:x")).toBe(false);
    expect(isSafeShowcaseUrl("file:///etc/passwd")).toBe(false);
  });
});

describe("createEmptyProject", () => {
  it("returns unique ids", () => {
    const a = createEmptyProject();
    const b = createEmptyProject();
    expect(a.id).not.toEqual(b.id);
  });
});

describe("validateShowcaseConfig", () => {
  it("passes a valid config", () => {
    expect(validateShowcaseConfig(baseConfig()).ok).toBe(true);
  });

  it("requires a title", () => {
    const result = validateShowcaseConfig(baseConfig({ title: "  " }));
    expect(result.ok).toBe(false);
    expect(result.errors.join(" ")).toMatch(/название витрины/i);
  });

  it("requires at least one project", () => {
    const result = validateShowcaseConfig(baseConfig({ projects: [] }));
    expect(result.ok).toBe(false);
  });

  it("flags an invalid demo url", () => {
    const config = baseConfig();
    config.projects[0].demo_url = "javascript:alert(1)";
    const result = validateShowcaseConfig(config);
    expect(result.ok).toBe(false);
    expect(result.errors.join(" ")).toMatch(/небезопасный demo/i);
  });
});

describe("toShowcasePayload", () => {
  it("strips empty optional fields", () => {
    const config = baseConfig();
    config.projects[0].landing_url = "";
    config.subtitle = "";
    const payload = toShowcasePayload(config);
    expect(payload.subtitle).toBeUndefined();
    expect(payload.projects[0].landing_url).toBeUndefined();
    expect(payload.projects[0].demo_url).toBe("https://aistudio.google.com/");
  });
});
