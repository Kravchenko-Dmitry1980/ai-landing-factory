import { LandingEditor } from "@/components/editor/LandingEditor";
import { StaffEditor } from "@/components/editor/StaffEditor";
import { AppHeader } from "@/components/shell/AppHeader";
import { getApiBaseUrl } from "@/lib/api";
import { notFound } from "next/navigation";

export default async function EditorPage({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { projectId } = await params;
  const { dev } = await searchParams;
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
  // ?dev=1 keeps the old diagnostic editor (PII, evidence, parser panels) for developers.
  if (dev !== undefined) {
    return (
      <>
        <AppHeader />
        <main className="mx-auto max-w-6xl px-4 py-8">
          <LandingEditor projectId={projectId} />
        </main>
      </>
    );
  }
  const project = (await preflight.json()) as { name?: string };
  return <StaffEditor projectId={projectId} projectName={project.name ?? ""} />;
}
