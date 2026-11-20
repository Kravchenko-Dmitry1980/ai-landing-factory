/** Resolve only the public paths issued by our API, on the browser's current site. */
export function publicLandingUrl(path: string | null | undefined, origin: string): string | null {
  if (!path || !/^\/s\/[A-Za-z0-9_-]{43}$/.test(path)) return null;
  try {
    const base = new URL(origin);
    if (base.protocol !== "https:" && base.protocol !== "http:") return null;
    return new URL(path, base.origin).href;
  } catch {
    return null;
  }
}

/** Clipboard can be absent on HTTP or denied by the browser: the caller then selects its URL field. */
export async function copyPublicLink(url: string): Promise<boolean> {
  try {
    if (typeof navigator === "undefined" || !navigator.clipboard?.writeText) return false;
    await navigator.clipboard.writeText(url);
    return true;
  } catch {
    return false;
  }
}
