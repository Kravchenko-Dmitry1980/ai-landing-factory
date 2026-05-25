import type { DiagramTypeId } from "@/lib/types";

export interface DiagramPreset {
  id: DiagramTypeId;
  label: string;
  description: string;
}

export const DIAGRAM_PRESETS: DiagramPreset[] = [
  { id: "pipeline", label: "Pipeline", description: "ETL / AI pipelines" },
  { id: "layered", label: "Layered", description: "Enterprise systems" },
  { id: "hub_spoke", label: "Hub & Spoke", description: "Orchestrators" },
  { id: "microservices", label: "Microservices", description: "Distributed systems" },
  { id: "dashboard_flow", label: "Dashboard Flow", description: "Analytics" },
  { id: "research_graph", label: "Research Graph", description: "AI research" },
];

export function getDiagramPreset(id: string): DiagramPreset | undefined {
  return DIAGRAM_PRESETS.find((p) => p.id === id);
}
