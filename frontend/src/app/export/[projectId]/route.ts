import { getApiBaseUrl } from "@/lib/api";
import { slugifyRu } from "@/lib/staff";
import type { LandingContract, TeamMember } from "@/lib/types";
import { loadLandingAssets } from "@/landing/assets.server";
import { buildLandingModel, themeFromContract, type LandingTheme } from "@/landing/model";
import { esc, renderLandingHtml } from "@/landing/render";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BACKEND_TIMEOUT_MS = 15_000;

/**
 * The page has no scripts and loads nothing from outside. This header enforces that for the preview
 * and for anyone opening /export directly; the downloaded file itself carries no CSP.
 */
const CSP =
  "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'";

class ExportError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

/** Plain text for fetch() callers; a small readable page for the preview iframe and direct visits. */
function errorResponse(error: ExportError, wantsHtml: boolean): Response {
  const headers: Record<string, string> = { "Cache-Control": "no-store", "Content-Security-Policy": CSP };
  if (!wantsHtml) {
    return new Response(error.message, { status: error.status, headers: { ...headers, "Content-Type": "text/plain; charset=utf-8" } });
  }
  const page = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Страница не собрана</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F6F7FB;color:#22262E;font:18px/1.6 system-ui,sans-serif"><p style="max-width:520px;padding:24px;text-align:center">${esc(error.message)}</p></body></html>`;
  return new Response(page, { status: error.status, headers: { ...headers, "Content-Type": "text/html; charset=utf-8" } });
}

async function backendJson<T>(path: string, what: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${getApiBaseUrl()}${path}`, { cache: "no-store", signal: AbortSignal.timeout(BACKEND_TIMEOUT_MS) });
  } catch (err) {
    const timedOut = err instanceof Error && err.name === "TimeoutError";
    console.error(`Export: ${what} request failed`, path, err);
    throw new ExportError(
      timedOut ? "Сервер данных не ответил вовремя. Попробуйте ещё раз." : "Нет связи с сервером данных. Попробуйте ещё раз.",
      timedOut ? 504 : 502,
    );
  }
  if (res.status === 404 || res.status === 422) {
    throw new ExportError("Лендинг не найден или материалы ещё не загружены.", 404);
  }
  if (!res.ok) {
    console.error(`Export: ${what} returned ${res.status}`, path, (await res.text()).slice(0, 300));
    throw new ExportError("Сервер данных вернул ошибку. Попробуйте ещё раз через минуту.", 502);
  }
  try {
    return (await res.json()) as T;
  } catch (err) {
    console.error(`Export: ${what} is not JSON`, path, err);
    throw new ExportError("Сервер данных ответил не тем форматом. Сообщите разработчику.", 502);
  }
}

function assertContract(value: unknown): asserts value is LandingContract {
  const c = value as LandingContract | null;
  if (!c || typeof c !== "object" || !Array.isArray(c.blocks)) {
    console.error("Export: contract has an unexpected shape", value);
    throw new ExportError("Данные лендинга повреждены. Сообщите разработчику.", 502);
  }
}

/**
 * The landing page of a project, rendered by the single v2 engine.
 * GET /export/{id}            — inline, for the preview
 * GET /export/{id}?download=1 — the same bytes as an attachment
 * GET /export/{id}?theme=light|night — overrides the theme saved in the project
 */
export async function GET(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  const url = new URL(request.url);
  const download = url.searchParams.get("download") === "1";
  const wantsHtml = !download && (request.headers.get("accept") ?? "").includes("text/html");
  const id = encodeURIComponent(projectId);

  try {
    const [contract, publicTeam] = await Promise.all([
      backendJson<unknown>(`/projects/${id}/contract`, "contract"),
      // The team goes through the backend publication policy; without it the page shows no team.
      backendJson<TeamMember[]>(`/projects/${id}/public-team`, "public team").catch((err: unknown) => {
        console.error("Export: publishable team unavailable, rendering without a team", projectId, err);
        return null;
      }),
    ]);
    assertContract(contract);

    const asked = url.searchParams.get("theme");
    const theme: LandingTheme = asked === "light" || asked === "night" ? asked : themeFromContract(contract);

    let assets;
    try {
      assets = await loadLandingAssets();
    } catch (err) {
      console.error("Export: fonts or cat image could not be read from disk", err);
      throw new ExportError("Не удалось собрать страницу: на сервере нет файлов оформления. Сообщите разработчику.", 500);
    }

    let html: string;
    try {
      html = renderLandingHtml(buildLandingModel(contract, Array.isArray(publicTeam) ? publicTeam : null), { theme, assets });
    } catch (err) {
      console.error("Export: render failed", projectId, err);
      throw new ExportError("Не удалось собрать страницу. Сообщите разработчику.", 500);
    }

    const fileName = `${slugifyRu(contract.title || "landing")}.html`;
    return new Response(html, {
      headers: {
        "Content-Type": "text/html; charset=utf-8",
        "Content-Disposition": download ? `attachment; filename="${fileName}"` : "inline",
        "X-Landing-Filename": fileName,
        "Content-Security-Policy": CSP,
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "no-store",
      },
    });
  } catch (err) {
    if (err instanceof ExportError) return errorResponse(err, wantsHtml);
    console.error("Export: unexpected failure", projectId, err);
    return errorResponse(new ExportError("Не удалось собрать страницу. Сообщите разработчику.", 500), wantsHtml);
  }
}
