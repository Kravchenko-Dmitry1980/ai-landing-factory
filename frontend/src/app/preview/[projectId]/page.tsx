import { Suspense } from "react";
import { LandingPreview } from "@/components/preview/LandingPreview";

export default async function PreviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <Suspense fallback={<p className="px-6 py-8 text-fur">Открываю страницу…</p>}>
      <LandingPreview projectId={projectId} />
    </Suspense>
  );
}
