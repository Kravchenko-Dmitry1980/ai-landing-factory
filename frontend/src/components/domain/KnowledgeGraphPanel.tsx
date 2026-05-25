"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ProjectKnowledgeGraph } from "./types";

interface Props {
  graph: ProjectKnowledgeGraph | null | undefined;
}

export function KnowledgeGraphPanel({ graph }: Props) {
  if (!graph) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-base">Knowledge Graph</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">No graph data.</CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-dashed">
      <CardHeader>
        <CardTitle className="text-base">Knowledge Graph</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          Entities: {graph.entities.length} · Relations: {graph.relations.length} · Overall
          confidence: {(graph.confidence_summary.overall * 100).toFixed(0)}%
        </p>
        {graph.missing_knowledge.length > 0 && (
          <div>
            <p className="font-medium text-amber-800">Missing knowledge</p>
            <ul className="list-disc pl-5 text-muted-foreground">
              {graph.missing_knowledge.slice(0, 5).map((m) => (
                <li key={m}>{m}</li>
              ))}
            </ul>
          </div>
        )}
        {graph.recommendations.length > 0 && (
          <div>
            <p className="font-medium">Recommendations</p>
            <ul className="list-disc pl-5 text-muted-foreground">
              {graph.recommendations.slice(0, 4).map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
        )}
        <ul className="max-h-40 overflow-y-auto text-xs text-muted-foreground">
          {graph.entities.slice(0, 12).map((e) => (
            <li key={e.id}>
              [{e.entity_type}] {e.label} ({(e.confidence * 100).toFixed(0)}%)
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
