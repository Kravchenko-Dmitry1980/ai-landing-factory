import { getApiBaseUrl } from "./api";

const OPAQUE = /^[A-Za-z0-9_-]{43}$/;
const READABLE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const PAGE_HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Content-Security-Policy":
    "sandbox; default-src 'none'; img-src data:; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'; frame-ancestors 'self'",
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "no-store",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "Referrer-Policy": "no-referrer",
};

const SHARE_HEADERS = {
  "Content-Type": "text/html; charset=utf-8",
  "Content-Security-Policy":
    "default-src 'none'; media-src 'self'; img-src data: 'self'; font-src data:; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'",
  "X-Content-Type-Options": "nosniff",
  "Cache-Control": "no-store",
  "X-Robots-Tag": "noindex, nofollow, noarchive",
  "Referrer-Policy": "no-referrer",
};

export interface PublicDemoMeta {
  demo: boolean;
  poster: boolean;
  title: string;
}

export function isShareToken(token: string): boolean {
  return OPAQUE.test(token) || (token.length <= 80 && READABLE.test(token));
}

export function unavailablePage(status: 404 | 502): Response {
  const text = status === 404
    ? "Эта страница недоступна: её сняли с публикации или ссылка неверна. Попросите отправителя прислать актуальную ссылку."
    : "Сервер сейчас не отвечает. Обновите страницу через минуту.";
  return new Response(
    `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Лендинг недоступен</title></head><body style="margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#F6F7FB;color:#22262E;font:18px/1.6 system-ui,sans-serif"><p style="max-width:560px;padding:24px;text-align:center">${text}</p></body></html>`,
    { status, headers: PAGE_HEADERS },
  );
}

const DEMO_MARKER = "<!--demo-->";

function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** The player inside the dark page. It does not start by itself and does not add a second scrollbar. */
export function demoSection(token: string, poster: boolean, title: string): string {
  const posterAttr = poster ? ` poster="/s/${token}/poster"` : "";
  const head = title ? `<div class="video-head"><span>${esc(title)}</span></div>` : "";
  return `<section class="section" id="demo"><div class="wrap"><div class="kicker">Видеодемонстрация</div><h2>Посмотрите, как работает система</h2><p class="section-intro">Ролик внутри страницы. Он не запускается сам: нажмите воспроизведение.</p><div class="video-shell">${head}<div class="video-frame"><video controls preload="none" playsinline${posterAttr} src="/s/${token}/demo" aria-label="Демонстрация системы">Ваш браузер не поддерживает видео.</video></div></div></div></section>`;
}

/** Puts the demo into the published page and reveals the links to it. */
export function embedDemo(html: string, token: string, poster: boolean, title = ""): string {
  const section = demoSection(token, poster, title);
  const withPlayer = html.includes(DEMO_MARKER)
    ? html.replace(DEMO_MARKER, section)
    : html.replace("</main>", `${section}</main>`);
  return withPlayer.replaceAll('href="#demo" hidden', 'href="#demo"');
}

async function ask(path: string, headers?: HeadersInit): Promise<Response> {
  return fetch(`${getApiBaseUrl()}${path}`, {
    method: "GET",
    headers,
    credentials: "omit",
    redirect: "error",
    cache: "no-store",
    signal: AbortSignal.timeout(15_000),
  });
}

export async function readDemoMeta(token: string): Promise<PublicDemoMeta | "missing" | "down"> {
  try {
    const response = await ask(`/public/landings/${token}/meta`, { Accept: "application/json" });
    if (response.status === 404) return "missing";
    if (!response.ok) return "down";
    const body = await response.json() as Partial<PublicDemoMeta>;
    if (typeof body.demo !== "boolean" || typeof body.poster !== "boolean" || typeof body.title !== "string") {
      return "down";
    }
    return { demo: body.demo, poster: body.poster, title: body.title };
  } catch {
    return "down";
  }
}

/** The published landing alone, still unable to run scripts or load the demo. */
export async function publishedLanding(token: string): Promise<Response> {
  try {
    const response = await ask(`/public/landings/${token}`, { Accept: "text/html" });
    if (response.status === 404) return unavailablePage(404);
    const type = response.headers.get("content-type")?.toLowerCase() ?? "";
    if (!response.ok || !type.startsWith("text/html")) return unavailablePage(502);
    return new Response(await response.text(), { headers: PAGE_HEADERS });
  } catch {
    return unavailablePage(502);
  }
}

export function shareResponse(html: string): Response {
  return new Response(html, { headers: SHARE_HEADERS });
}

const FILE_HEADERS = ["content-type", "content-length", "content-range", "accept-ranges"];

/** Passes the video or cover through without the visitor's cookies or backend names. */
export async function publishedFile(token: string, kind: "demo" | "poster", range: string | null): Promise<Response> {
  try {
    const headers = new Headers({ Accept: kind === "demo" ? "video/mp4" : "image/*" });
    if (range) headers.set("Range", range);
    const response = await ask(`/public/landings/${token}/${kind}`, headers);
    if (response.status === 404) return new Response(null, { status: 404, headers: { "Cache-Control": "no-store" } });
    if (!response.ok && response.status !== 206) return new Response(null, { status: 502, headers: { "Cache-Control": "no-store" } });
    const type = response.headers.get("content-type")?.toLowerCase() ?? "";
    const expected = kind === "demo" ? "video/mp4" : "image/";
    if (!type.startsWith(expected)) return new Response(null, { status: 502, headers: { "Cache-Control": "no-store" } });
    const out = new Headers();
    for (const name of FILE_HEADERS) {
      const value = response.headers.get(name);
      if (value) out.set(name, value);
    }
    out.set("Cache-Control", "no-store");
    out.set("X-Content-Type-Options", "nosniff");
    out.set("Referrer-Policy", "no-referrer");
    out.set("X-Robots-Tag", "noindex, nofollow, noarchive");
    return new Response(response.body, { status: response.status, headers: out });
  } catch {
    return new Response(null, { status: 502, headers: { "Cache-Control": "no-store" } });
  }
}
