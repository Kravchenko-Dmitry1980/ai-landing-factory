import { afterEach, describe, expect, it, vi } from "vitest";
import { exportHtml } from "./api";

function mockFetchOk(html: string) {
  const fetchMock = vi.fn(async () =>
    new Response(JSON.stringify({ html }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    }),
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function lastUrl(fetchMock: ReturnType<typeof vi.fn>): string {
  return String(fetchMock.mock.calls.at(-1)?.[0] ?? "");
}

describe("exportHtml export modes", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("standard export does not set mode param", async () => {
    const fetchMock = mockFetchOk("<html>standard</html>");
    await exportHtml("p1", { theme: "tech" });
    const url = lastUrl(fetchMock);
    expect(url).not.toContain("mode=");
    expect(url).toContain("theme=tech");
  });

  it("WOW export sets mode=wow", async () => {
    const fetchMock = mockFetchOk("<html>wow</html>");
    await exportHtml("p1", { theme: "tech", mode: "wow" });
    expect(lastUrl(fetchMock)).toContain("mode=wow");
  });

  it("WOW 3D export sets mode=wow and wow_3d_runtime=aframe", async () => {
    const fetchMock = mockFetchOk("<html>wow3d</html>");
    await exportHtml("p1", { theme: "tech", mode: "wow", wow3dRuntime: "aframe" });
    const url = lastUrl(fetchMock);
    expect(url).toContain("mode=wow");
    expect(url).toContain("wow_3d_runtime=aframe");
  });

  it("does not leak wow_3d_runtime when mode is standard", async () => {
    const fetchMock = mockFetchOk("<html>standard</html>");
    await exportHtml("p1", { theme: "tech", wow3dRuntime: "aframe" });
    expect(lastUrl(fetchMock)).not.toContain("wow_3d_runtime");
  });

  it("returns the html payload", async () => {
    mockFetchOk("<html>wow</html>");
    const html = await exportHtml("p1", { mode: "wow" });
    expect(html).toContain("wow");
  });
});
