import { afterEach, describe, expect, it, vi } from "vitest";
import { WOW_BUNDLE_ZIP_FILENAME, exportWowBundleZip } from "./api";

function mockZipOk(disposition?: string) {
  const headers: Record<string, string> = { "Content-Type": "application/zip" };
  if (disposition) headers["Content-Disposition"] = disposition;
  const fetchMock = vi.fn(
    async () => new Response(new Blob(["PK"], { type: "application/zip" }), { status: 200, headers }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function lastUrl(fetchMock: ReturnType<typeof vi.fn>): string {
  return String(fetchMock.mock.calls.at(-1)?.[0] ?? "");
}

describe("exportWowBundleZip", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("calls the wow-bundle export endpoint", async () => {
    const fetchMock = mockZipOk();
    await exportWowBundleZip("p1");
    expect(lastUrl(fetchMock)).toContain("/projects/p1/export/wow-bundle");
  });

  it("forwards demo_url and showcase_url query params", async () => {
    const fetchMock = mockZipOk();
    await exportWowBundleZip("p1", {
      demoUrl: "https://demo.example",
      showcaseUrl: "/showcase/1",
    });
    const url = lastUrl(fetchMock);
    expect(url).toContain("demo_url=");
    expect(url).toContain("showcase_url=");
  });

  it("returns a blob and a filename from Content-Disposition", async () => {
    mockZipOk('attachment; filename="ai-wow-landing-p1.zip"');
    const { blob, filename } = await exportWowBundleZip("p1");
    expect(blob).toBeInstanceOf(Blob);
    expect(filename).toBe("ai-wow-landing-p1.zip");
  });

  it("falls back to the default filename without a header", async () => {
    mockZipOk();
    const { filename } = await exportWowBundleZip("p1");
    expect(filename).toBe(WOW_BUNDLE_ZIP_FILENAME);
  });

  it("throws a friendly error on non-ok responses", async () => {
    const fetchMock = vi.fn(async () => new Response("missing build", { status: 503 }));
    vi.stubGlobal("fetch", fetchMock);
    await expect(exportWowBundleZip("p1")).rejects.toThrow();
  });
});
