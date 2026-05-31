import { ShowcaseBuilder } from "@/components/showcase/ShowcaseBuilder";

export const metadata = {
  title: "Редактор витрины — AI Landing Factory",
};

export default async function ShowcaseBuilderPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold tracking-tight">Редактор витрины</h1>
      <ShowcaseBuilder showcaseId={id} />
    </div>
  );
}
