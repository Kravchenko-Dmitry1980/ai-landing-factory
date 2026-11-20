import { getApiBaseUrl } from "@/lib/api";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Content-Security-Policy":
    "sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'",
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "no-store",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "Referrer-Policy": "no-referrer",
};

function unavailable(status: 404 | 502): Response {
  const text = status === 404
    ? "Эта страница недоступна: её сняли с публикации или ссылка неверна. Попросите отправителя прислать актуальную ссылку."
    : "Сервер сейчас не отвечает. Обновите страницу через минуту.";
  return new Response(
    `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Лендинг недоступен</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F6F7FB;color:#22262E;font:18px/1.6 system-ui,sans-serif"><p style="max-width:560px;padding:24px;text-align:center">${text}</p></body></html>`,
    { status, headers: HEADERS },
  );
}

/** Only the explicitly shared snapshot. No session, library metadata or staff navigation. */
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!/^[A-Za-z0-9_-]{43}$/.test(token)) return unavailable(404);
  try {
    const response = await fetch(`${getApiBaseUrl()}/public/landings/${token}`, {
      method: "GET",
      headers: { Accept: "text/html" },
      credentials: "omit",
      redirect: "error",
      cache: "no-store",
      signal: AbortSignal.timeout(15_000),
    });
    if (response.status === 404) return unavailable(404);
    if (!response.ok || !response.headers.get("content-type")?.toLowerCase().startsWith("text/html")) {
      return unavailable(502);
    }
    // Rebuild headers from an allowlist; never forward Set-Cookie or backend metadata.
    return new Response(await response.text(), { headers: HEADERS });
  } catch {
    // A public token is a share link, so neither it nor request credentials belong in logs.
    return unavailable(502);
  }
}
