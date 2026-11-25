import { isShareToken, publishedLanding, unavailablePage } from "@/lib/public-snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** The landing inside the share page. Scripts stay off, and this address does not play the demo. */
export async function GET(_request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!isShareToken(token)) return unavailablePage(404);
  return publishedLanding(token);
}
