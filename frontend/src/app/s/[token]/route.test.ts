import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { GET } from "./route";

const TOKEN = "Ab0_-".repeat(8) + "xyz";
const HTML = '<!doctype html><html lang="ru"><title>Учебный проект</title><body>Опубликованная версия</body></html>';
const fetchMock = vi.fn<typeof fetch>();

function metaResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function answer(meta: Response, html?: Response): void {
  fetchMock.mockImplementation((input) => {
    const url = String(input);
    if (url.endsWith("/meta")) return Promise.resolve(meta);
    return Promise.resolve(html ?? meta);
  });
}

function openPage(token = TOKEN): Promise<Response> {
  const request = new Request(`https://lend.example/s/${encodeURIComponent(token)}`, {
    headers: { Cookie: "lend_session=private-session", Authorization: "Bearer private-credential" },
  });
  return GET(request, { params: Promise.resolve({ token }) });
}

function expectIsolatedHeaders(response: Response): void {
  expect(response.headers.get("content-type")).toMatch(/^text\/html\b/);
  expect(response.headers.get("cache-control")).toContain("no-store");
  expect(response.headers.get("x-content-type-options")).toBe("nosniff");
  expect(response.headers.get("referrer-policy")).toBe("no-referrer");
  const robots = response.headers.get("x-robots-tag") ?? "";
  for (const instruction of ["noindex", "nofollow", "noarchive"]) expect(robots).toContain(instruction);
  const csp = response.headers.get("content-security-policy") ?? "";
  expect(csp).toMatch(/(?:^|;)\s*sandbox\s*(?:;|$)/);
  expect(csp).toContain("default-src 'none'");
  expect(csp).toContain("style-src 'unsafe-inline'");
  expect(csp).not.toContain("allow-scripts");
  expect(csp).not.toContain("allow-same-origin");
  expect(response.headers.get("set-cookie")).toBeNull();
}

beforeEach(() => {
  vi.stubEnv("INTERNAL_API_URL", "http://backend:8001/api/v1/");
  vi.stubGlobal("fetch", fetchMock);
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.unstubAllEnvs();
});

describe("public landing route", () => {
  it("serves the HTML snapshot without forwarding the visitor's credentials or backend headers", async () => {
    answer(
      metaResponse({ demo: false, poster: false, title: "Учебный проект" }),
      new Response(HTML, {
        headers: {
          "content-type": "text/html; charset=utf-8",
          "set-cookie": "backend_session=must-not-reach-browser",
          "x-internal-project": "private-project-id",
          "cache-control": "public, max-age=3600",
        },
      }),
    );

    const response = await openPage();
    expect(response.status).toBe(200);
    expect(await response.text()).toBe(HTML);
    expectIsolatedHeaders(response);
    expect(response.headers.get("x-internal-project")).toBeNull();

    expect(fetchMock).toHaveBeenCalledTimes(2);
    const [metaUrl, metaInit] = fetchMock.mock.calls[0];
    expect(metaUrl).toBe(`http://backend:8001/api/v1/public/landings/${TOKEN}/meta`);
    expect(metaInit).toMatchObject({ cache: "no-store", credentials: "omit", redirect: "error" });
    const [url, init] = fetchMock.mock.calls[1];
    expect(url).toBe(`http://backend:8001/api/v1/public/landings/${TOKEN}`);
    expect(init).toMatchObject({ cache: "no-store", credentials: "omit", redirect: "error" });
    expect(init?.signal).toBeInstanceOf(AbortSignal);
    const headers = new Headers(init?.headers);
    expect([...headers.entries()]).toEqual([["accept", "text/html"]]);
  });

  it("puts the demo inside the landing and does not start it or nest a second page", async () => {
    const page = '<!doctype html><html lang="ru"><body><main><a href="#demo" hidden>Смотреть демо</a><!--demo--></main></body></html>';
    answer(
      metaResponse({ demo: true, poster: true, title: "Комус <script>" }),
      new Response(page, { headers: { "content-type": "text/html; charset=utf-8" } }),
    );
    const response = await openPage();
    expect(response.status).toBe(200);
    const html = await response.text();
    expect(html).toContain(`src="/s/${TOKEN}/demo"`);
    expect(html).toContain(`poster="/s/${TOKEN}/poster"`);
    expect(html).toContain('id="demo"');
    expect(html).toContain("Посмотрите, как работает система");
    expect(html).toContain("Комус &lt;script&gt;");
    expect(html).toContain('href="#demo"');
    expect(html).not.toContain('href="#demo" hidden');
    expect(html).not.toContain("<iframe");
    expect(html).not.toContain("autoplay");
    expect(html).not.toContain("<script");
    expect(html).not.toContain("Комус <script>");
    expect(html).not.toContain("Библиотека");
    const csp = response.headers.get("content-security-policy") ?? "";
    expect(csp).toContain("media-src 'self'");
    expect(csp).toContain("img-src data: 'self'");
    expect(csp).not.toContain("script-src");
    expect(csp).not.toContain("sandbox");
    expect(response.headers.get("set-cookie")).toBeNull();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("asks the backend for a readable project address", async () => {
    answer(
      metaResponse({ demo: false, poster: false, title: "Проект" }),
      new Response(HTML, { headers: { "content-type": "text/html; charset=utf-8" } }),
    );
    const response = await openPage("prognoz-defolta");
    expect(response.status).toBe(200);
    expect(String(fetchMock.mock.calls[0][0])).toContain("/public/landings/prognoz-defolta/meta");
  });

  it.each(["", "Short", "a_b", "-lend", "lend-", "a".repeat(81), "../" + "a".repeat(40), "a".repeat(42) + ".", "я".repeat(43)])(
    "rejects malformed token %j before asking the backend",
    async (token) => {
      const response = await openPage(token);
      expect(response.status).toBe(404);
      expectIsolatedHeaders(response);
      expect(fetchMock).not.toHaveBeenCalled();
    },
  );

  it("uses the same generic unavailable page for a missing or revoked share", async () => {
    answer(metaResponse({ detail: "private project metadata" }, 404));
    const missing = await openPage();
    const malformed = await openPage("нет");
    expect(missing.status).toBe(404);
    expectIsolatedHeaders(missing);
    const text = await missing.text();
    expect(text).toBe(await malformed.text());
    expect(text).not.toContain("private project metadata");
    expect(text).not.toContain(TOKEN);
    expect(text).not.toContain("/login");
  });

  it.each([401, 403, 500, 503])("turns backend HTTP %i into a generic temporary error", async (status) => {
    answer(metaResponse({ detail: "server-secret-path-and-project-id" }, status));
    const response = await openPage();
    expect(response.status).toBe(502);
    expectIsolatedHeaders(response);
    const text = await response.text();
    expect(text).not.toContain("server-secret-path-and-project-id");
    expect(text).not.toContain(TOKEN);
  });

  it("does not serve a success response containing JSON as a landing", async () => {
    answer(
      metaResponse({ demo: false, poster: false, title: "Страница" }),
      new Response(JSON.stringify({ project: "private-id" }), { headers: { "content-type": "application/json" } }),
    );
    const response = await openPage();
    expect(response.status).toBe(502);
    expectIsolatedHeaders(response);
    expect(await response.text()).not.toContain("private-id");
  });

  it("keeps a backend connection failure isolated from the visitor", async () => {
    fetchMock.mockRejectedValue(new Error("Internal connection error containing private details"));
    const response = await openPage();
    expect(response.status).toBe(502);
    expectIsolatedHeaders(response);
    expect(await response.text()).not.toContain("private details");
  });
});
