import type { SemanticGenerationMetadata } from "@/lib/types";

interface Props {
  metadata: SemanticGenerationMetadata;
}

export function SectionPlannerView({ metadata }: Props) {
  return (
    <div className="rounded-lg border p-4 text-sm">
      <h3 className="mb-2 font-semibold">Section planner</h3>
      <p>
        Domain: <code>{metadata.domain}</code> · Layout:{" "}
        <code>{metadata.layout_preset}</code> · Profile:{" "}
        <code>{metadata.style_profile}</code>
      </p>
      <p className="mt-2 text-muted-foreground">
        Selected: {metadata.selected_sections.join(" → ") || "none"}
      </p>
      <p className="mt-1 text-xs text-muted-foreground">
        Provider: {metadata.provider} · fallback:{" "}
        {metadata.fallback_used ? "yes" : "no"} · PII redacted:{" "}
        {metadata.privacy_redacted ? "yes" : "no"}
      </p>
    </div>
  );
}
