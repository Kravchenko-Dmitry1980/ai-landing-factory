import type { SemanticNarrative } from "@/lib/types";

interface Props {
  narrative: SemanticNarrative;
}

export function NarrativePanel({ narrative }: Props) {
  const items = [
    ["Problem", narrative.problem],
    ["System", narrative.system],
    ["Architecture", narrative.architecture],
    ["Modules", narrative.modules],
    ["Metrics", narrative.metrics],
    ["Roadmap", narrative.roadmap],
  ].filter(([, v]) => v?.trim());

  if (!items.length) return null;

  return (
    <div className="rounded-lg border p-4 text-sm">
      <h3 className="mb-2 font-semibold">Narrative arc · {narrative.tone}</h3>
      <dl className="grid gap-2">
        {items.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs uppercase text-muted-foreground">{label}</dt>
            <dd className="mt-0.5">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
