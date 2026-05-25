import type { SemanticSection } from "@/lib/types";

interface Props {
  sections: SemanticSection[];
}

export function SemanticInsights({ sections }: Props) {
  const withInsights = sections.filter((s) => s.insights.length > 0 || s.callouts.length > 0);
  if (!withInsights.length) return null;

  return (
    <div className="rounded-lg border p-4 text-sm">
      <h3 className="mb-2 font-semibold">Semantic insights</h3>
      <ul className="space-y-3">
        {withInsights.map((s) => (
          <li key={`${s.section_type}-${s.title}`}>
            <p className="font-medium">{s.title}</p>
            {s.insights.map((i) => (
              <p key={i} className="text-muted-foreground">
                {i}
              </p>
            ))}
            {s.callouts.map((c) => (
              <p key={c} className="text-amber-800">
                {c}
              </p>
            ))}
          </li>
        ))}
      </ul>
    </div>
  );
}
