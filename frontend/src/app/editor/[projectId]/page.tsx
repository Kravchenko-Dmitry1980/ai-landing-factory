import { LandingEditor } from "@/components/editor/LandingEditor";
import { notFound } from "next/navigation";

function resolveApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  return raw ? raw.replace(/\/$/, "") : "http://127.0.0.1:8001/api/v1";
}

export default async function EditorPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  const apiBase = resolveApiBaseUrl();
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
