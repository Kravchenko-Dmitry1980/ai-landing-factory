import { afterEach, describe, expect, it, vi } from "vitest";
import {
  addShowcaseProject,
  createShowcase,
  exportShowcaseZip,
  listLandingCandidates,
  listShowcases,
  reorderShowcaseProjects,
} from "./showcaseApi";

function jsonResponse(body: unknown) {
  return {
    ok: true,
    status: 200,
    headers: { get: () => "" },
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("showcaseApi", () => {
  it("createShowcase POSTs the title", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "s1" }));
    vi.stubGlobal("fetch", fetchMock);

    await createShowcase({ title: "Витрина" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/showcases$/);
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({ title: "Витрина" });
  });

  it("listShowcases GETs /showcases", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    await listShowcases();
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/showcases$/);
  });

  it("addShowcaseProject POSTs to the projects sub-resource", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "s1" }));
    vi.stubGlobal("fetch", fetchMock);

    await addShowcaseProject("s1", { title: "P" });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/showcases\/s1\/projects$/);
    expect(init.method).toBe("POST");
  });

  it("reorderShowcaseProjects sends ordered_ids", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: "s1" }));
    vi.stubGlobal("fetch", fetchMock);

    await reorderShowcaseProjects("s1", ["b", "a"]);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toMatch(/\/showcases\/s1\/projects\/reorder$/);
    expect(JSON.parse(init.body as string)).toEqual({ ordered_ids: ["b", "a"] });
  });

  it("exportShowcaseZip requests the zip endpoint and returns a blob", async () => {
    const blob = new Blob(["PK"], { type: "application/zip" });
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      blob: async () => blob,
      headers: { get: () => 'attachment; filename="ai-showcase.zip"' },
    });
    vi.stubGlobal("fetch", fetchMock);

    const result = await exportShowcaseZip("s1");
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/showcases\/s1\/export-zip$/);
    expect(fetchMock.mock.calls[0][1].method).toBe("POST");
    expect(result.filename).toBe("ai-showcase.zip");
    expect(result.blob).toBe(blob);
  });

  it("listLandingCandidates GETs the singular showcase helper", async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse([]));
    vi.stubGlobal("fetch", fetchMock);

    await listLandingCandidates();
    expect(fetchMock.mock.calls[0][0]).toMatch(/\/showcase\/landing-candidates$/);
  });
});
