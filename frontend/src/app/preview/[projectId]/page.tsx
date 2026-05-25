import { Suspense } from "react";
import { LandingPreview } from "@/components/preview/LandingPreview";

export default async function PreviewPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">Интерактивный preview</h1>
      <Suspense fallback={<p className="text-muted-foreground">Загрузка preview…</p>}>
        <LandingPreview projectId={projectId} />
      </Suspense>
    </div>
  );
}
