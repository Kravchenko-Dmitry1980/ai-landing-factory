"use client";

import type { EvidenceVisibility, SourceStructureReport } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EvidenceVisibilityPanel } from "./EvidenceVisibilityPanel";

interface Props {
  report: SourceStructureReport | null;
  evidence: EvidenceVisibility | null;
  loading: boolean;
  evidenceLoading?: boolean;
  parserMode?: string;
}

export function SourceStructurePanel({
  report,
  evidence,
  loading,
  evidenceLoading = false,
  parserMode,
}: Props) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Структура источника</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Загрузка…</CardContent>
      </Card>
    );
  }

  return (
    <>
      {report && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Структура источника</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p className="text-muted-foreground">
              Mode: <span className="font-medium text-foreground">{report.parser_mode}</span>
              {" · "}
              Confidence: {(report.parser_confidence * 100).toFixed(0)}%
            </p>

            {report.sections.length > 0 && (
              <ul className="space-y-1">
                {report.sections.map((s) => (
                  <li key={s.key} className="flex justify-between gap-4 border-b border-border py-1">
                    <span>{s.key}</span>
                    <span className="text-muted-foreground">
                      {s.length} chars
                      {s.item_count > 0 ? ` · ${s.item_count} items` : ""}
                    </span>
                  </li>
                ))}
              </ul>
            )}

            {report.missing_sections.length > 0 && (
              <p className="text-amber-800">
                Missing sections: {report.missing_sections.join(", ")}
              </p>
            )}

            {report.detection.detected_sections.length > 0 && (
              <p className="text-muted-foreground">
                Detected: {report.detection.detected_sections.join(", ")}
              </p>
            )}
          </CardContent>
        </Card>
      )}

      <EvidenceVisibilityPanel
        evidence={evidence}
        loading={evidenceLoading}
        parserMode={parserMode ?? report?.parser_mode}
      />
    </>
  );
}
