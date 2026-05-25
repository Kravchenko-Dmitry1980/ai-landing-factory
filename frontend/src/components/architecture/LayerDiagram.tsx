"use client";

import type { ArchitectureTopology } from "@/lib/types";
import { ArchitectureCanvas } from "./ArchitectureCanvas";

export function LayerDiagram({ topology, showDebug }: { topology: ArchitectureTopology; showDebug?: boolean }) {
  return (
    <div className="space-y-4">
      {topology.layers.map((layer) => (
        <div key={layer.id} className="rounded border border-[var(--alf-border)] p-3">
          <h4 className="text-xs font-semibold uppercase tracking-wide text-[var(--alf-text-muted)] mb-2">
            {layer.label}
          </h4>
          <div className="flex flex-wrap gap-2">
            {layer.node_ids.map((nid) => {
              const node = topology.nodes.find((n) => n.id === nid);
              if (!node) return null;
              return (
                <span
                  key={nid}
                  className="text-xs px-2 py-1 rounded bg-[var(--alf-surface)] border border-[var(--alf-border)]"
                >
                  {node.label}
                </span>
              );
            })}
          </div>
        </div>
      ))}
      <ArchitectureCanvas topology={topology} showDebug={showDebug} />
    </div>
  );
}
