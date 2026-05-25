"use client";

import type { ArchitectureTopology } from "@/lib/types";
import { ArchitectureCanvas } from "./ArchitectureCanvas";

export function SystemMap({ topology, showDebug }: { topology: ArchitectureTopology; showDebug?: boolean }) {
  return <ArchitectureCanvas topology={topology} showDebug={showDebug} />;
}
