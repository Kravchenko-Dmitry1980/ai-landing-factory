"use client";

import type { ArchitectureFlow, ArchitectureTopology } from "@/lib/types";
import { ArchitectureGraph } from "./ArchitectureGraph";

function FlowPath({ flow, topology }: { flow: ArchitectureFlow; topology: ArchitectureTopology }) {
  const labels = flow.path
    .map((id) => topology.nodes.find((n) => n.id === id)?.label)
    .filter(Boolean);
  if (!labels.length) return null;
  return (
    <div className="text-xs text-[var(--alf-text-muted)]">
      <span className="font-medium text-[var(--alf-text)]">{flow.label}: </span>
      {labels.join(" → ")}
    </div>
  );
}

export function DataFlowGraph({ topology, showDebug }: { topology: ArchitectureTopology; showDebug?: boolean }) {
  return (
    <div className="space-y-3">
      {topology.flows.map((f) => (
        <FlowPath key={f.id} flow={f} topology={topology} />
      ))}
      <ArchitectureGraph topology={topology} showDebug={showDebug} height={360} />
    </div>
  );
}
