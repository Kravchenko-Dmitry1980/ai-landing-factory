import { embedDemo, isShareToken, publishedLanding, readDemoMeta, shareResponse, unavailablePage } from "@/lib/public-snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** The share link. A demo is part of the page; without one, only the landing is returned. */
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!isShareToken(token)) return unavailablePage(404);
  const meta = await readDemoMeta(token);
  if (meta === "missing") return unavailablePage(404);
  if (meta === "down") return unavailablePage(502);
  if (!meta.demo) return publishedLanding(token);
  const landing = await publishedLanding(token);
  if (landing.status !== 200) return landing;
  return shareResponse(embedDemo(await landing.text(), token, meta.poster, meta.title));
}
