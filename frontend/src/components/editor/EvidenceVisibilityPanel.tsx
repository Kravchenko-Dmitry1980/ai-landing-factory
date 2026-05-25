"use client";

import { useState } from "react";
import type { EvidenceVisibility } from "@/lib/types";
import { formatParserMode, hasEvidenceData } from "@/lib/evidence-format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { SourceInventoryTable } from "./SourceInventoryTable";
import { FieldCoveragePanel } from "./FieldCoveragePanel";
import { EvidenceHints } from "./EvidenceHints";

interface Props {
  evidence: EvidenceVisibility | null;
  loading?: boolean;
  parserMode?: string;
  defaultExpanded?: boolean;
}

export function EvidenceVisibilityPanel({
  evidence,
  loading = false,
  parserMode = "unknown",
  defaultExpanded = false,
}: Props) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const mode = evidence?.parser_mode ?? parserMode;
  const showSummaryAlways = mode === "multi_source_assembly";

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Source & Evidence</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">Загрузка…</CardContent>
      </Card>
    );
  }

  if (!evidence && !showSummaryAlways) {
    return null;
  }

  if (!evidence) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Source & Evidence</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Данные о сборке из источников недоступны.
        </CardContent>
      </Card>
    );
  }

  const hasData = hasEvidenceData(evidence, null);
  const strongCount = evidence.strong_fields.length;
  const weakCount = evidence.weak_fields.length;
  const missingCount = evidence.missing_fields.length;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle className="text-base">Source & Evidence</CardTitle>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? "Скрыть источники сборки" : "Показать источники сборки"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4 text-sm">
        <div className="flex flex-wrap gap-x-6 gap-y-2">
          <div>
            <span className="text-muted-foreground">Parser mode: </span>
            <span className="font-medium">{formatParserMode(evidence.parser_mode)}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Sources: </span>
            <span className="font-medium">{evidence.source_count}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Evidence items: </span>
            <span className="font-medium">{evidence.evidence_count}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Assembly confidence: </span>
            <span className="font-medium">
              {evidence.assembly_confidence.toFixed(2)}
            </span>
          </div>
          {hasData && (
            <>
              <div>
                <span className="text-muted-foreground">Strong fields: </span>
                <span className="font-medium text-emerald-700">{strongCount}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Weak fields: </span>
                <span className="font-medium text-amber-700">{weakCount}</span>
              </div>
              <div>
                <span className="text-muted-foreground">Missing fields: </span>
                <span className="font-medium text-slate-700">{missingCount}</span>
              </div>
            </>
          )}
        </div>

        <EvidenceHints
          hints={evidence.improvement_hints}
          warnings={evidence.warnings}
          parserMode={evidence.parser_mode}
        />

        {expanded && hasData && (
          <>
            <div>
              <p className="mb-2 font-medium">Sources</p>
              <SourceInventoryTable sources={evidence.sources} />
            </div>
            <div>
              <p className="mb-2 font-medium">Field coverage</p>
              <FieldCoveragePanel fieldSources={evidence.field_sources} />
            </div>
          </>
        )}

        {!hasData && (
          <p className="text-muted-foreground">
            Данные о сборке из источников недоступны для этого контракта.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
