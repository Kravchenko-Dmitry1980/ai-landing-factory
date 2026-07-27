import { LandingEditor } from "@/components/editor/LandingEditor";
import { getApiBaseUrl } from "@/lib/api";
import { notFound } from "next/navigation";

export default async function EditorPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  // SSR: getApiBaseUrl() uses INTERNAL_API_URL (Docker: http://backend:8001/api/v1)
  const apiBase = getApiBaseUrl();
  const preflight = await fetch(`${apiBase}/projects/${projectId}`, {
    cache: "no-store",
  });
  if (preflight.status === 404) {
    notFound();
  }
  if (!preflight.ok) {
    throw new Error(`Editor preflight failed: HTTP ${preflight.status}`);
  }
  return <LandingEditor projectId={projectId} />;
}
