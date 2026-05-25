"use client";

import type { ArchitectureTopology } from "@/lib/types";
import { getDiagramPreset } from "@/lib/architecture/architecture_presets";
import { graphDensity } from "@/lib/architecture/graph_layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  topology: ArchitectureTopology | null | undefined;
}

export function ArchitectureDebugPanel({ topology }: Props) {
  if (!topology) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Architecture debug</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          No topology generated. Run «Сформировать ленд» first.
        </CardContent>
      </Card>
    );
  }

  const preset = getDiagramPreset(topology.diagram_type);
  const inferred = topology.nodes.filter((n) => n.inferred);
  const lowEdges = topology.edges.filter((e) => e.confidence < 0.5 || e.inferred);
  const density = graphDensity(topology.node_count, topology.edge_count);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Architecture debug</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <p>
          Diagram: <strong>{preset?.label ?? topology.diagram_type}</strong> · Layout:{" "}
          {topology.layout} · Density: {density.toFixed(3)}
        </p>
        <div>
          <p className="font-medium mb-1">Layers</p>
          <ul className="list-disc pl-5 text-muted-foreground">
            {topology.layers.map((l) => (
              <li key={l.id}>
                {l.label}: {l.node_ids.length} nodes
              </li>
            ))}
          </ul>
        </div>
        {inferred.length > 0 && (
          <div>
            <p className="font-medium text-amber-700">Inferred nodes ({inferred.length})</p>
            <p className="text-muted-foreground">{inferred.map((n) => n.label).join(", ")}</p>
          </div>
        )}
        {lowEdges.length > 0 && (
          <div>
            <p className="font-medium text-amber-700">Low confidence edges ({lowEdges.length})</p>
            <ul className="list-disc pl-5 text-muted-foreground">
              {lowEdges.slice(0, 5).map((e) => (
                <li key={e.id}>
                  {e.source} → {e.target} ({(e.confidence * 100).toFixed(0)}%)
                </li>
              ))}
            </ul>
          </div>
        )}
        {topology.warnings.length > 0 && (
          <div>
            <p className="font-medium">Topology warnings</p>
            <ul className="list-disc pl-5 text-amber-700">
              {topology.warnings.map((w) => (
                <li key={w}>{w}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
