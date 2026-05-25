import { describe, expect, it } from "vitest";
import { graphDensity, layoutNodes } from "@/lib/architecture/graph_layout";
import type { ArchitectureTopology } from "@/lib/types";

const sampleTopology: ArchitectureTopology = {
  diagram_type: "pipeline",
  layout: "vertical_pipeline",
  nodes: [
    { id: "a", label: "Frontend", node_type: "frontend", layer: "frontend", confidence: 0.9, source: ["stack"], inferred: false },
    { id: "b", label: "Backend", node_type: "backend", layer: "backend", confidence: 0.9, source: ["stack"], inferred: false },
  ],
  edges: [{ id: "a->b", source: "a", target: "b", flow_type: "data", confidence: 0.8, source_refs: [], inferred: false }],
  layers: [],
  flows: [],
  warnings: [],
  node_count: 2,
  edge_count: 1,
  graph_density: 0.5,
  generated_at: null,
};

describe("graph_layout", () => {
  it("assigns positions to all nodes", () => {
    const positions = layoutNodes(sampleTopology);
    expect(positions.size).toBe(2);
    expect(positions.get("a")).toBeDefined();
  });

  it("computes density", () => {
    expect(graphDensity(2, 1)).toBe(0.5);
    expect(graphDensity(1, 0)).toBe(0);
  });
});

describe("node_types", () => {
  it("resolves redis type", async () => {
    const { resolveNodeType } = await import("@/lib/architecture/node_types");
    expect(resolveNodeType("redis").id).toBe("redis");
  });
});
