"use client";

import type { EvidenceSourceView } from "@/lib/types";
import {
  formatParserMode,
  formatSourceRole,
  sourceStatusBadgeClass,
} from "@/lib/evidence-format";

interface Props {
  sources: EvidenceSourceView[];
}

export function SourceInventoryTable({ sources }: Props) {
  if (sources.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">Источники не найдены.</p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-muted-foreground">
            <th className="py-2 pr-3 font-medium">File</th>
            <th className="py-2 pr-3 font-medium">Type</th>
            <th className="py-2 pr-3 font-medium">Role</th>
            <th className="py-2 pr-3 font-medium">Evidence</th>
            <th className="py-2 pr-3 font-medium">Status</th>
            <th className="py-2 font-medium">Notes</th>
          </tr>
        </thead>
        <tbody>
          {sources.map((src) => (
            <tr key={src.source_id} className="border-b border-border align-top">
              <td className="py-2 pr-3 font-medium">{src.filename}</td>
              <td className="py-2 pr-3 text-muted-foreground">
                {src.detected_source_type}
              </td>
              <td className="py-2 pr-3">{formatSourceRole(src.source_role)}</td>
              <td className="py-2 pr-3">{src.evidence_count}</td>
              <td className="py-2 pr-3">
                <span
                  className={`inline-block rounded px-2 py-0.5 text-xs ${sourceStatusBadgeClass(src.status)}`}
                >
                  {src.status}
                </span>
              </td>
              <td className="py-2 text-muted-foreground">
                {src.notes.length > 0 ? src.notes.join(" ") : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function EvidenceSummaryRow({
  label,
  value,
}: {
  label: string;
  value: string | number;
}) {
  return (
    <div>
      <span className="text-muted-foreground">{label}: </span>
      <span className="font-medium">{value}</span>
    </div>
  );
}

export { formatParserMode };
