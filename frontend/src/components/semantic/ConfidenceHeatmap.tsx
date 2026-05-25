import type { SemanticSection } from "@/lib/types";

interface Props {
  sections: SemanticSection[];
}

function heatColor(score: number): string {
  if (score >= 0.75) return "bg-emerald-200";
  if (score >= 0.5) return "bg-amber-200";
  return "bg-red-200";
}

export function ConfidenceHeatmap({ sections }: Props) {
  if (!sections.length) return null;
  return (
    <div className="rounded-lg border p-4 text-sm">
      <h3 className="mb-2 font-semibold">Confidence heatmap</h3>
      <div className="grid gap-2 sm:grid-cols-2">
        {sections.map((s) => (
          <div key={`${s.section_type}-${s.title}`} className="flex items-center gap-2">
            <span
              className={`inline-block h-3 w-3 rounded ${heatColor(s.confidence.overall)}`}
              title={`overall ${s.confidence.overall.toFixed(2)}`}
            />
            <span className="truncate">{s.section_type}</span>
            <span className="ml-auto text-xs text-muted-foreground">
              {s.confidence.overall.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
