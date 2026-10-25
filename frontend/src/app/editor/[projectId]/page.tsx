import { LandingEditor } from "@/components/editor/LandingEditor";
import { StaffEditor } from "@/components/editor/StaffEditor";
import { AppHeader } from "@/components/shell/AppHeader";
import { backendFetch, requireUser } from "@/lib/session.server";
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
  const user = await requireUser(`/editor/${projectId}`, "editor");
  // SSR: the backend address comes from INTERNAL_API_URL (Docker: http://backend:8001/api/v1).
  const preflight = await backendFetch(`/projects/${encodeURIComponent(projectId)}`);
  // 422: not a project id at all, which for a visitor is the same as a missing landing.
  if (preflight.status === 404 || preflight.status === 422) {
    notFound();
  }
  if (!preflight.ok) {
    throw new Error(`Editor preflight failed: HTTP ${preflight.status}`);
  }
  // ?dev=1 keeps the old diagnostic editor (PII, evidence, parser panels) for developers.
  if (dev !== undefined) {
    return (
      <>
        <AppHeader user={user} current="studio" />
        <main className="mx-auto max-w-6xl px-4 py-8">
          <LandingEditor projectId={projectId} />
        </main>
      </>
    );
  }
  const project = (await preflight.json()) as { name?: string };
  return <StaffEditor projectId={projectId} projectName={project.name ?? ""} />;
}
