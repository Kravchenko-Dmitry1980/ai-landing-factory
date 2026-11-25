import { isShareToken, publishedFile, unavailablePage } from "@/lib/public-snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** The cover image for one share link. */
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!isShareToken(token)) return unavailablePage(404);
  return publishedFile(token, "poster", null);
}
