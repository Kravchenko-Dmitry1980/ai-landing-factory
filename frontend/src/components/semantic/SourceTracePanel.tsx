import type { SemanticSourceTrace } from "@/lib/types";

interface Props {
  trace: SemanticSourceTrace[];
}

export function SourceTracePanel({ trace }: Props) {
  if (!trace.length) return null;
  return (
    <div className="rounded-lg border p-4 text-sm">
      <h3 className="mb-2 font-semibold">Source trace</h3>
      <ul className="space-y-2">
        {trace.slice(0, 10).map((t) => (
          <li key={`${t.field}-${t.section_type}-${t.evidence.slice(0, 20)}`}>
            <span className="font-medium">{t.section_type}</span>
            {t.source_key && <> ← {t.source_key}</>}
            {t.evidence && (
              <p className="text-muted-foreground">{t.evidence.slice(0, 120)}</p>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
