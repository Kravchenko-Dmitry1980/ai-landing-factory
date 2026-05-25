"use client";

import type { ArchitectureTopology } from "@/lib/types";
import { ArchitectureGraph } from "./ArchitectureGraph";
import { getDiagramPreset } from "@/lib/architecture/architecture_presets";

import type { StyleProfileId } from "@/design/style_profiles";

interface Props {
  topology: ArchitectureTopology;
  showDebug?: boolean;
  profileId?: StyleProfileId;
}

export function ArchitectureCanvas({ topology, showDebug, profileId }: Props) {
  const preset = getDiagramPreset(topology.diagram_type);
  const lightMode = profileId === "university_platform";

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3 text-xs text-[var(--alf-text-muted)]">
        <span className="font-medium text-[var(--alf-text)]">
          {preset?.label ?? topology.diagram_type}
        </span>
        <span>{topology.node_count} nodes · {topology.edge_count} edges</span>
        <span>layout: {topology.layout}</span>
        {topology.graph_density > 0.2 && (
          <span className="text-amber-600">high density</span>
        )}
      </div>
      <ArchitectureGraph topology={topology} showDebug={showDebug} lightMode={lightMode} />
    </div>
  );
}
