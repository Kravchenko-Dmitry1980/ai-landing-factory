"use client";

import { useState } from "react";
import { analyzeDomain, formatApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ArchetypeBadges } from "./ArchetypeBadges";
import { DomainProfilePanel } from "./DomainProfilePanel";
import { KnowledgeGraphPanel } from "./KnowledgeGraphPanel";
import { PatternMap } from "./PatternMap";
import type { DomainIntelligenceReport } from "./types";

interface Props {
  projectId: string;
  report?: DomainIntelligenceReport | null;
  semanticDomain?: string | null;
  onReport?: (report: DomainIntelligenceReport) => void;
  compact?: boolean;
}

export function DomainDebugPanel({
  projectId,
  report,
  semanticDomain,
  onReport,
  compact = false,
}: Props) {
  const [local, setLocal] = useState<DomainIntelligenceReport | null>(report ?? null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const data = local ?? report;

  async function handleRefresh() {
    setLoading(true);
    setError(null);
    try {
      const next = await analyzeDomain(projectId);
      setLocal(next);
      onReport?.(next);
    } catch (err) {
      setError(formatApiError(err, "Domain analysis failed"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4 rounded-lg border border-dashed p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h3 className="font-semibold">Domain Intelligence (Stage G)</h3>
          {!compact && (
            <p className="text-xs text-muted-foreground">
              Hybrid classifier · knowledge graph · topology hints
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <ArchetypeBadges
            domain={data?.graph.domain_profile.primary_domain ?? semanticDomain}
            archetypes={data?.graph.system_archetypes ?? []}
          />
          <Button variant="outline" size="sm" onClick={handleRefresh} disabled={loading}>
            {loading ? "Analyzing…" : "Обновить domain analysis"}
          </Button>
        </div>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {data?.warnings.map((w) => (
        <p key={w} className="text-sm text-amber-700">
          {w}
        </p>
      ))}
      <div className={`grid gap-4 ${compact ? "grid-cols-1" : "md:grid-cols-2"}`}>
        <DomainProfilePanel profile={data?.graph.domain_profile} />
        <PatternMap patterns={data?.graph.architecture_patterns ?? []} />
        <KnowledgeGraphPanel graph={data?.graph} />
      </div>
    </div>
  );
}
