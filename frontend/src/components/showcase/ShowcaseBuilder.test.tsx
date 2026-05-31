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
  it("renders an improved empty state when there are no projects", () => {
    const builder = source("ShowcaseBuilder.tsx");
    expect(builder).toMatch(/В витрине пока нет проектов/);
    expect(builder).toMatch(/Добавить из готовых лендов/);
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

  it("'Add from landing' prefills landing_url and leaves demo_url empty", () => {
    const candidate: LandingCandidate = {
      project_id: "p-1",
      title: "Эндокринология+",
      preview_url: "/preview/p-1",
      export_html_url: "/api/v1/projects/p-1/export/html",
      landing_url: "/preview/p-1",
      export_available: true,
    };
    const request = candidateToProjectRequest(candidate);
    expect(request.title).toBe("Эндокринология+");
    expect(request.landing_url).toBe("/preview/p-1");
    expect(request.demo_url).toBeUndefined();
  });

  it("shows landing autofill badge in the project form", () => {
    const form = source("ShowcaseProjectForm.tsx");
    expect(form).toMatch(/Подставлено автоматически/i);
    expect(form).toMatch(/Ссылка на ленд/);
    expect(form).toMatch(/Ссылка на демо/);
  });

  it("candidate pick opens the add form instead of immediate submit", () => {
    const builder = source("ShowcaseBuilder.tsx");
    expect(builder).toMatch(/handleCandidatePick/);
    expect(builder).toMatch(/landingAutofillHint/);
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
    expect(actions).toMatch(/showcase\.html и локальный A-Frame runtime/);
  });

  it("list page exposes quick-create template button", () => {
    const list = source("ShowcaseList.tsx");
    expect(list).toMatch(/Создать витрину AI-проектов УИИ/);
    expect(list).toMatch(/createDefaultShowcaseTemplate/);
  });

  it("builder includes readiness panel", () => {
    const builder = source("ShowcaseBuilder.tsx");
    expect(builder).toMatch(/ShowcaseReadinessPanel/);
    const panel = readFileSync(
      join(HERE, "ShowcaseReadinessPanel.tsx"),
      "utf-8",
    );
    expect(panel).toMatch(/Готовность к демонстрации/);
  });

  it("project card shows landing and demo status", () => {
    const card = source("ShowcaseProjectCard.tsx");
    expect(card).toMatch(/Ленд:/);
    expect(card).toMatch(/Demo-ссылка не добавлена/);
    expect(card).toMatch(/Открыть ленд/);
    expect(card).toMatch(/noopener noreferrer/);
  });
});
