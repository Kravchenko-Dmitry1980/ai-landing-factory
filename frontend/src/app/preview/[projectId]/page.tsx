import type { Metadata } from "next";
import { Suspense } from "react";
import { LandingPreview } from "@/components/preview/LandingPreview";
import { StaffPreview } from "@/components/preview/StaffPreview";
import { requireUser } from "@/lib/session.server";

export const metadata: Metadata = { title: "Как увидят посетители — Ленд" };

export default async function PreviewPage({
  params,
  searchParams,
}: {
  params: Promise<{ projectId: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { projectId } = await params;
  const { dev } = await searchParams;
  await requireUser(`/preview/${projectId}`, "editor");
  // ?dev=1 keeps the old renderer with its export panels and debug views for developers.
  if (dev !== undefined) {
    return (
      <Suspense fallback={<p className="px-6 py-8 text-fur">Открываю страницу…</p>}>
        <LandingPreview projectId={projectId} />
      </Suspense>
    );
  }
  return <StaffPreview projectId={projectId} />;
}
