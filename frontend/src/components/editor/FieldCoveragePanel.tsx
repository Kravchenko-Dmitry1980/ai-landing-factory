"use client";

import type { FieldSourceView } from "@/lib/types";
import {
  coverageBadgeClass,
  formatCoverageStatus,
  formatFieldName,
  parseSourceRef,
} from "@/lib/evidence-format";

const FIELD_ORDER = [
  "title",
  "client",
  "timeline",
  "lead",
  "essence",
  "tasks",
  "purpose",
  "inputs",
  "outputs",
  "results",
  "outlook",
  "tech_stack",
  "team",
  "modules",
  "quote",
];

interface Props {
  fieldSources: Record<string, FieldSourceView>;
}

export function FieldCoveragePanel({ fieldSources }: Props) {
  const entries = FIELD_ORDER.filter((key) => fieldSources[key]).map(
    (key) => fieldSources[key],
  );

  if (entries.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Покрытие полей недоступно для этого контракта.
      </p>
    );
  }

  return (
    <ul className="space-y-3">
      {entries.map((field) => (
        <li
          key={field.field_name}
          className="rounded-md border border-border px-3 py-2"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-medium">{formatFieldName(field.field_name)}</span>
            <span
              className={`rounded border px-2 py-0.5 text-xs ${coverageBadgeClass(field.coverage)}`}
            >
              {formatCoverageStatus(field.coverage)}
            </span>
            {field.confidence > 0 && (
              <span className="text-xs text-muted-foreground">
                confidence {(field.confidence * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {field.source_refs.length > 0 && (
            <div className="mt-2 space-y-1 text-sm text-muted-foreground">
              {field.source_refs.slice(0, 4).map((ref) => {
                const parsed = parseSourceRef(ref);
                return (
                  <p key={ref}>
                    source: {parsed.filename}
                    {parsed.location ? ` · ${parsed.location}` : ""}
                  </p>
                );
              })}
            </div>
          )}

          {field.reasons.length > 0 && (
            <p className="mt-1 text-sm text-muted-foreground">
              reason: {field.reasons.join("; ")}
            </p>
          )}

          {field.selected_snippets.length > 0 && (
            <ul className="mt-2 list-disc pl-5 text-xs text-muted-foreground">
              {field.selected_snippets.map((snippet) => (
                <li key={snippet.slice(0, 40)}>{snippet}</li>
              ))}
            </ul>
          )}
        </li>
      ))}
    </ul>
  );
}
