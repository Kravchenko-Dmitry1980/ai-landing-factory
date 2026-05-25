import type { GeneratedSemanticLanding } from "@/lib/types";
import { AssumptionWarnings } from "./AssumptionWarnings";
import { ConfidenceHeatmap } from "./ConfidenceHeatmap";
import { NarrativePanel } from "./NarrativePanel";
import { SectionPlannerView } from "./SectionPlannerView";
import { SemanticInsights } from "./SemanticInsights";
import { SourceTracePanel } from "./SourceTracePanel";

interface Props {
  semantic: GeneratedSemanticLanding;
  message?: string | null;
}

export function SemanticDebugPanel({ semantic, message }: Props) {
  const meta = semantic.metadata;
  return (
    <div className="space-y-4 rounded-xl border border-dashed border-violet-300 bg-violet-50/50 p-4">
      <div>
        <h2 className="text-lg font-semibold">Semantic debug (Stage E)</h2>
        {message && <p className="text-sm text-muted-foreground">{message}</p>}
      </div>
      <SectionPlannerView metadata={meta} />
      <NarrativePanel narrative={semantic.narrative} />
      <ConfidenceHeatmap sections={semantic.sections} />
      <AssumptionWarnings
        missing={meta.missing_fields}
        assumptions={meta.assumptions}
        warnings={meta.hallucination_warnings}
      />
      <SourceTracePanel trace={meta.source_trace} />
      <SemanticInsights sections={semantic.sections} />
    </div>
  );
}
