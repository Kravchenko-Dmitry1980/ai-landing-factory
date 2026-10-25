import { buildProjectLanding, LandingBuildError } from "@/landing/build.server";
import { backendFetch } from "@/lib/session.server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PUBLISH_TIMEOUT_MS = 30_000;
/** The backend keeps 600 characters of the card text; longer ones would only fail validation. */
const SUMMARY_MAX = 600;

function detail(message: string, status: number): Response {
  return Response.json({ detail: message }, { status, headers: { "Cache-Control": "no-store" } });
}

/**
 * Browsers send Origin with every cross-origin POST; a page of another site must not publish.
 * Host names only: nginx passes Host without the port, and cookies are shared across ports anyway.
 */
function fromThisSite(request: Request): boolean {
  const origin = request.headers.get("origin");
  if (!origin) return true;
  const host = request.headers.get("x-forwarded-host") ?? request.headers.get("host") ?? "";
  try {
    if (new URL(origin).hostname === new URL(`http://${host}`).hostname) return true;
  } catch {
    // An unparsable Origin or Host is not this site.
  }
  console.warn("Publish refused: Origin", origin, "Host", host);
  return false;
}

async function expectedVersion(request: Request): Promise<number | null> {
  try {
    const body = (await request.json()) as { expected_version?: unknown };
    return typeof body.expected_version === "number" ? body.expected_version : null;
  } catch {
    return null;
  }
}

/**
 * POST /publish/{id} {"expected_version": n}: renders the saved landing exactly like the preview and
 * the download, then hands the page to the backend, which checks the editor's rights and stores it.
 * Answers in the backend's format: the publication, or {"detail": "..."} with its status.
 */
export async function POST(request: Request, { params }: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await params;
  if (!fromThisSite(request)) return detail("Запрос пришёл с другого сайта и отклонён.", 403);
  const onScreen = await expectedVersion(request);

  try {
    const built = await buildProjectLanding(projectId, { requireTeam: true });
    if (onScreen !== null && built.contract.version !== onScreen) {
      return detail(
        "Пока вы работали, лендинг изменил другой сотрудник. Обновите страницу, проверьте текст и опубликуйте снова.",
        409,
      );
    }
    let res: Response;
    try {
      res = await backendFetch(`/projects/${encodeURIComponent(projectId)}/publication`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          html: built.html,
          theme: built.theme,
          contract_version: built.contract.version,
          summary: built.model.description.slice(0, SUMMARY_MAX),
        }),
        signal: AbortSignal.timeout(PUBLISH_TIMEOUT_MS),
      });
    } catch (err) {
      const timedOut = err instanceof Error && err.name === "TimeoutError";
      console.error("Publish: backend request failed", projectId, err);
      return detail(
        timedOut
          ? "Сервер долго не отвечал. Публикация могла пройти: обновите страницу и проверьте её статус."
          : "Нет связи с сервером данных. Попробуйте опубликовать ещё раз.",
        timedOut ? 504 : 502,
      );
    }
    return new Response(await res.text(), {
      status: res.status,
      headers: { "Content-Type": res.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store" },
    });
  } catch (err) {
    if (err instanceof LandingBuildError) return detail(err.message, err.status);
    console.error("Publish: unexpected failure", projectId, err);
    return detail("Не удалось опубликовать лендинг. Сообщите разработчику.", 500);
  }
}
