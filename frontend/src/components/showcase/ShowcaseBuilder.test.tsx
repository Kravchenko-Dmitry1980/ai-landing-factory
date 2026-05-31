import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  candidateToProjectRequest,
  moveProjectInList,
  validateProjectRequest,
  type LandingCandidate,
} from "@/lib/showcase";
import { addShowcaseProject } from "@/lib/showcaseApi";
import { LAYOUT_OPTIONS, THEME_OPTIONS } from "./ShowcaseSettingsPanel";

const HERE = dirname(fileURLToPath(import.meta.url));

function source(file: string): string {
  return readFileSync(join(HERE, file), "utf-8");
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("ShowcaseBuilder UI", () => {
  it("renders an empty state hint when there are no projects", () => {
    const builder = source("ShowcaseBuilder.tsx");
    expect(builder).toMatch(/Пока в витрине нет проектов/);
  });

  it("exposes manual add and add-from-landing entry points", () => {
    const builder = source("ShowcaseBuilder.tsx");
    expect(builder).toMatch(/Добавить проект/);
    expect(builder).toMatch(/Добавить из лендов/);
  });

  it("offers all layout and theme selectors", () => {
    expect(LAYOUT_OPTIONS.map((o) => o.value)).toEqual([
      "gallery_arc",
      "grid_hall",
      "circle_booths",
    ]);
    expect(THEME_OPTIONS.map((o) => o.value)).toEqual([
      "university",
      "tech",
      "dark",
    ]);
  });

  it("validates a bad demo URL before adding", () => {
    const result = validateProjectRequest({
      title: "X",
      demo_url: "javascript:alert(1)",
    });
    expect(result.ok).toBe(false);
  });

  it("can move a project up and down", () => {
    const items = [{ id: "a" }, { id: "b" }, { id: "c" }];
    expect(moveProjectInList(items, 0, 1).map((p) => p.id)).toEqual([
      "b",
      "a",
      "c",
    ]);
    expect(moveProjectInList(items, 2, -1).map((p) => p.id)).toEqual([
      "a",
      "c",
      "b",
    ]);
  });

  it("'Add from landing' fills the title from the candidate", () => {
    const candidate: LandingCandidate = {
      project_id: "p-1",
      title: "Эндокринология+",
      export_available: true,
    };
    expect(candidateToProjectRequest(candidate).title).toBe("Эндокринология+");
  });

  it("export ZIP button calls the API", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ id: "s1" }),
      text: async () => "{}",
      headers: { get: () => "" },
    });
    vi.stubGlobal("fetch", fetchMock);

    await addShowcaseProject("s1", { title: "P" });
    expect(fetchMock).toHaveBeenCalledTimes(1);

    const actions = source("ShowcaseExportActions.tsx");
    expect(actions).toMatch(/exportShowcaseZip/);
    expect(actions).toMatch(/Экспорт ZIP для офлайн-демо/);
  });
});
