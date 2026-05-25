import type { ArchitectureTopology, TopologyNode } from "@/lib/types";

export interface LayoutPosition {
  x: number;
  y: number;
}

const LAYER_Y: Record<string, number> = {
  frontend: 0,
  orchestration: 140,
  ai: 280,
  backend: 420,
  data: 560,
  security: 700,
  infra: 840,
};

export function layoutNodes(
  topology: ArchitectureTopology,
): Map<string, LayoutPosition> {
  const positions = new Map<string, LayoutPosition>();
  const layout = topology.layout;

  if (layout === "vertical_pipeline" || layout === "layered") {
    const byLayer = new Map<string, TopologyNode[]>();
    for (const node of topology.nodes) {
      const layer = node.layer ?? "backend";
      const list = byLayer.get(layer) ?? [];
      list.push(node);
      byLayer.set(layer, list);
    }
    for (const [layer, nodes] of byLayer) {
      const y = LAYER_Y[layer] ?? 400;
      const gap = 180;
      const startX = -((nodes.length - 1) * gap) / 2;
      nodes.forEach((node, i) => {
        positions.set(node.id, { x: startX + i * gap, y });
      });
    }
    return positions;
  }

  // horizontal / mesh fallback
  const cols = Math.ceil(Math.sqrt(topology.nodes.length));
  topology.nodes.forEach((node, i) => {
    positions.set(node.id, {
      x: (i % cols) * 200,
      y: Math.floor(i / cols) * 120,
    });
  });
  return positions;
}

export function graphDensity(nodeCount: number, edgeCount: number): number {
  if (nodeCount <= 1) return 0;
  return edgeCount / (nodeCount * (nodeCount - 1));
}
