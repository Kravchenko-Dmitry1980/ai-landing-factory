import { ApiRequestError } from "./api-errors";
import { staffErrorMessage } from "./staff";

const LANDING_TIMEOUT_MS = 30_000;

/** Same-origin URL of the landing page rendered by the v2 engine (frontend route, not the backend API). */
export function landingUrl(projectId: string, options?: { download?: boolean }): string {
  return `/export/${encodeURIComponent(projectId)}${options?.download ? "?download=1" : ""}`;
}

export interface LandingFile {
  html: string;
  fileName: string;
}

/** The exact page a visitor gets: the preview shows it and "Скачать сайт" saves the same text. */
export async function fetchLandingFile(projectId: string): Promise<LandingFile> {
  let res: Response;
  try {
    res = await fetch(landingUrl(projectId), { cache: "no-store", signal: AbortSignal.timeout(LANDING_TIMEOUT_MS) });
  } catch (err) {
    console.error("Landing request failed", projectId, err);
    throw new ApiRequestError(err instanceof Error && err.name === "TimeoutError" ? "timeout" : "Failed to fetch", null);
  }
  const text = await res.text();
  // The route answers errors with a short plain-Russian sentence meant for staff.
  if (!res.ok) throw new ApiRequestError(text, res.status);
  return { html: text, fileName: res.headers.get("X-Landing-Filename") ?? "landing.html" };
}

/** Message for a failed landing request: the route's own explanation when it gave one. */
export function landingErrorMessage(err: unknown, action: string): string {
  if (err instanceof ApiRequestError && err.status !== null && err.message && err.message.length <= 200) {
    return `${action}. ${err.message}`;
  }
  if (err instanceof ApiRequestError && err.message === "timeout") {
    return `${action}: сервер не ответил вовремя. Попробуйте ещё раз.`;
  }
  return staffErrorMessage(err, action);
}
