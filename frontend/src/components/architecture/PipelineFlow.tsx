"use client";

import type { ArchitectureTopology } from "@/lib/types";
import { ArchitectureCanvas } from "./ArchitectureCanvas";

export function PipelineFlow({ topology, showDebug }: { topology: ArchitectureTopology; showDebug?: boolean }) {
  return <ArchitectureCanvas topology={{ ...topology, diagram_type: "pipeline" }} showDebug={showDebug} />;
}
