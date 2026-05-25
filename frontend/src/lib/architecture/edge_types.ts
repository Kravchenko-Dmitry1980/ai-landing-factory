export type FlowType = "data" | "control" | "dependency";

export interface EdgeStyleConfig {
  stroke: string;
  strokeDasharray?: string;
  animated: boolean;
}

export function edgeStyle(
  inferred: boolean,
  confidence: number,
): EdgeStyleConfig {
  const low = confidence < 0.5 || inferred;
  return {
    stroke: low ? "var(--alf-text-muted, #94a3b8)" : "var(--alf-accent, #6366f1)",
    strokeDasharray: low ? "6 4" : undefined,
    animated: !low && confidence >= 0.7,
  };
}
