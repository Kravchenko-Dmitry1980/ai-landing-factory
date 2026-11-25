import { isShareToken, publishedFile, unavailablePage } from "@/lib/public-snapshot";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** The video for one share link. Seeking is forwarded; the visitor's session is not. */
export async function GET(request: Request, { params }: { params: Promise<{ token: string }> }) {
  const { token } = await params;
  if (!isShareToken(token)) return unavailablePage(404);
  return publishedFile(token, "demo", request.headers.get("range"));
}
