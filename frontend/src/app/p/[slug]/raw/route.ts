import { esc } from "@/landing/render";
import { backendFetch } from "@/lib/session.server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * Published pages carry no scripts. The sandbox also gives them no origin, so even a page that
 * somehow contained one could not act with the viewer's session. Framed only by our own /p/{slug}.
 */
const CSP =
  "sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'";

const HEADERS = {
  "Content-Security-Policy": CSP,
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "private, no-cache",
};

function message(text: string, status: number): Response {
  const page = `<!doctype html><html lang="ru"><head><meta charset="utf-8"><title>Лендинг недоступен</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F6F7FB;color:#22262E;font:18px/1.6 system-ui,sans-serif"><p style="max-width:520px;padding:24px;text-align:center">${esc(text)}</p></body></html>`;
  return new Response(page, { status, headers: { ...HEADERS, "Content-Type": "text/html; charset=utf-8" } });
}

/** GET /p/{slug}/raw: the published page itself, for the frame on /p/{slug} or a full-screen tab. */
export async function GET(_request: Request, { params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  let res: Response;
  try {
    res = await backendFetch(`/library/${encodeURIComponent(slug)}/html`, { signal: AbortSignal.timeout(15_000) });
  } catch (err) {
    console.error("Published page: backend request failed", slug, err);
    return message("Сервер сейчас не отвечает. Обновите страницу через минуту.", 502);
  }
  if (res.status === 401) return message("Войдите в учётную запись: библиотека открыта только сотрудникам.", 401);
  if (res.status === 404) return message("Такого лендинга в библиотеке нет: его сняли с публикации или адрес неверный.", 404);
  if (!res.ok) {
    const body = (await res.json().catch(() => null)) as { detail?: unknown } | null;
    console.error("Published page: backend answered", res.status, slug, body?.detail);
    // The backend explains its own failures (for example, a lost page file that only republishing fixes).
    const text = typeof body?.detail === "string" ? body.detail : "Не удалось открыть лендинг. Попробуйте ещё раз через минуту.";
    return message(text, 502);
  }
  return new Response(await res.text(), { headers: { ...HEADERS, "Content-Type": "text/html; charset=utf-8" } });
}
