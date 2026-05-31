import { describe, expect, it } from "vitest";
import {
  SHOWCASE_ZIP_DEFAULT_FILENAME,
  SHOWCASE_ZIP_EXPORT_PATH,
  candidateToProjectRequest,
  createEmptyProject,
  isSafeShowcaseUrl,
  moveProjectInList,
  showcaseZipFilename,
  toShowcasePayload,
  validateProjectRequest,
  validateShowcaseConfig,
  type LandingCandidate,
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

describe("showcase ZIP export helpers", () => {
  it("uses showcase export-zip API path", () => {
    expect(SHOWCASE_ZIP_EXPORT_PATH).toBe("/showcase/export-zip");
  });

  it("download filename ends with .zip", () => {
    expect(showcaseZipFilename()).toMatch(/\.zip$/i);
    expect(SHOWCASE_ZIP_DEFAULT_FILENAME).toBe("ai-showcase.zip");
  });
});

describe("moveProjectInList", () => {
  it("moves an item up and down", () => {
    const items = ["a", "b", "c"];
    expect(moveProjectInList(items, 2, -1)).toEqual(["a", "c", "b"]);
    expect(moveProjectInList(items, 0, 1)).toEqual(["b", "a", "c"]);
  });

  it("is a no-op at the boundaries", () => {
    const items = ["a", "b"];
    expect(moveProjectInList(items, 0, -1)).toBe(items);
    expect(moveProjectInList(items, 1, 1)).toBe(items);
  });
});

describe("candidateToProjectRequest", () => {
  it("fills title and description from a landing candidate", () => {
    const candidate: LandingCandidate = {
      project_id: "p-1",
      title: "Эндокринология+",
      client: "УИИ",
      description: "Лид-абзац",
      landing_url: "/preview/p-1",
      export_available: true,
    };
    const request = candidateToProjectRequest(candidate);
    expect(request.title).toBe("Эндокринология+");
    expect(request.description).toBe("Лид-абзац");
    expect(request.landing_url).toBe("/preview/p-1");
    expect(request.source_project_id).toBe("p-1");
  });
});

describe("validateProjectRequest", () => {
  it("requires a title", () => {
    expect(validateProjectRequest({ title: "  " }).ok).toBe(false);
  });

  it("rejects a dangerous demo url", () => {
    const result = validateProjectRequest({
      title: "X",
      demo_url: "javascript:alert(1)",
    });
    expect(result.ok).toBe(false);
    expect(result.errors.join(" ")).toMatch(/демо/i);
  });

  it("passes a valid manual project", () => {
    expect(
      validateProjectRequest({
        title: "X",
        demo_url: "https://aistudio.google.com/",
      }).ok,
    ).toBe(true);
  });
});
