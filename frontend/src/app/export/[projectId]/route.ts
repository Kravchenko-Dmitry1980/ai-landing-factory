import { buildProjectLanding, LandingBuildError } from "@/landing/build.server";
import type { LandingTheme } from "@/landing/model";
import { esc } from "@/landing/render";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * The page has no scripts and loads nothing from outside. This header enforces that for the preview
 * and for anyone opening /export directly; the downloaded file itself carries no CSP.
 */
const CSP =
  "default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'";

/** Plain text for fetch() callers; a small readable page for the preview iframe and direct visits. */
function errorResponse(error: LandingBuildError, wantsHtml: boolean): Response {
  const headers: Record<string, string> = { "Cache-Control": "no-store", "Content-Security-Policy": CSP };
  if (!wantsHtml) {
    return new Response(error.message, { status: error.status, headers: { ...headers, "Content-Type": "text/plain; charset=utf-8" } });
  }
  const page = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Страница не собрана</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F6F7FB;color:#22262E;font:18px/1.6 system-ui,sans-serif"><p style="max-width:520px;padding:24px;text-align:center">${esc(error.message)}</p></body></html>`;
  return new Response(page, { status: error.status, headers: { ...headers, "Content-Type": "text/html; charset=utf-8" } });
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
  const asked = url.searchParams.get("theme");
  const theme: LandingTheme | undefined = asked === "light" || asked === "night" ? asked : undefined;

  try {
    const { html, fileName } = await buildProjectLanding(projectId, { theme });
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
    if (err instanceof LandingBuildError) return errorResponse(err, wantsHtml);
    console.error("Export: unexpected failure", projectId, err);
    return errorResponse(new LandingBuildError("Не удалось собрать страницу. Сообщите разработчику.", 500), wantsHtml);
  }
}
