import { LandingEditor } from "@/components/editor/LandingEditor";

export default async function EditorPage({
  params,
}: {
  params: Promise<{ projectId: string }>;
}) {
  const { projectId } = await params;
  return <LandingEditor projectId={projectId} />;
}
