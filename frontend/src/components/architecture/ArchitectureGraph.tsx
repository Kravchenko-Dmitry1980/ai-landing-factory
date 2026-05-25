"use client";

import { memo, useMemo } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  type Edge,
  type Node,
  MarkerType,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { edgeStyle } from "@/lib/architecture/edge_types";
import { layoutNodes } from "@/lib/architecture/graph_layout";
import { resolveNodeType } from "@/lib/architecture/node_types";
import type { ArchitectureTopology } from "@/lib/types";

interface Props {
  topology: ArchitectureTopology;
  showDebug?: boolean;
  height?: number;
  lightMode?: boolean;
}

function ArchNode({
  data,
}: {
  data: {
    label: string;
    nodeType: string;
    inferred: boolean;
    confidence: number;
    lightMode?: boolean;
  };
}) {
  const cfg = resolveNodeType(data.nodeType);
  const borderColor = data.inferred
    ? "#94A3B8"
    : data.lightMode
      ? "#7C3AED"
      : cfg.color;
  return (
    <div
      className="rounded-lg border px-3 py-2 text-xs min-w-[120px]"
      style={{
        borderColor,
        borderStyle: data.inferred ? "dashed" : "solid",
        background: data.lightMode ? "#F1F4F7" : "var(--alf-surface, #fff)",
        color: "#111111",
        boxShadow: "none",
      }}
    >
      <div className="font-semibold truncate">{data.label}</div>
      <div className="text-[10px] opacity-70 mt-0.5">{cfg.label}</div>
      {data.inferred && (
        <div className="text-[10px] text-amber-600 mt-1">inferred · {(data.confidence * 100).toFixed(0)}%</div>
      )}
    </div>
  );
}

const nodeTypes = { archNode: ArchNode };

function ArchitectureGraphInner({ topology, showDebug, height = 420, lightMode = false }: Props) {
  const { nodes, edges } = useMemo(() => {
    const positions = layoutNodes(topology);
    const flowNodes: Node[] = topology.nodes.map((n) => ({
      id: n.id,
      type: "archNode",
      position: positions.get(n.id) ?? { x: 0, y: 0 },
      data: {
        label: n.label,
        nodeType: n.node_type,
        inferred: n.inferred,
        confidence: n.confidence,
        lightMode,
      },
    }));
    const flowEdges: Edge[] = topology.edges.map((e) => {
      const style = edgeStyle(e.inferred, e.confidence);
      const stroke = lightMode
        ? e.inferred || e.confidence < 0.5
          ? "#94A3B8"
          : "#7C3AED"
        : style.stroke;
      return {
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.label ?? undefined,
        animated: lightMode ? false : style.animated,
        style: {
          stroke,
          strokeWidth: 2,
          strokeDasharray: style.strokeDasharray,
        },
        markerEnd: { type: MarkerType.ArrowClosed, color: stroke },
      };
    });
    return { nodes: flowNodes, edges: flowEdges };
  }, [topology, lightMode]);

  if (nodes.length === 0) {
    return (
      <p className="text-sm text-[var(--alf-text-muted)] py-8 text-center">
        Architecture topology not available — run generation first.
      </p>
    );
  }

  return (
    <div
      style={{ height }}
      className={`w-full rounded-lg border overflow-hidden ${
        lightMode
          ? "border-[#E5E7EB] bg-[#F8FAFC]"
          : "border-[var(--alf-border)] bg-[var(--alf-bg-subtle,#f8fafc)]"
      }`}
    >
      {showDebug && topology.warnings.length > 0 && (
        <ul className="text-xs text-amber-700 px-3 py-2 border-b bg-amber-50">
          {topology.warnings.slice(0, 3).map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        minZoom={0.3}
        maxZoom={1.5}
        nodesDraggable={false}
        nodesConnectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Background gap={16} color={lightMode ? "#E5E7EB" : "var(--alf-border, #e2e8f0)"} />
        <Controls showInteractive={false} />
        <MiniMap pannable zoomable />
      </ReactFlow>
    </div>
  );
}

export const ArchitectureGraph = memo(ArchitectureGraphInner);
