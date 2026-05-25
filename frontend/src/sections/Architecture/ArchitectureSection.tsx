import { ArchitectureCanvas } from "@/components/architecture/ArchitectureCanvas";
import { LayerDiagram } from "@/components/architecture/LayerDiagram";
import { PipelineFlow } from "@/components/architecture/PipelineFlow";
import { DataFlowGraph } from "@/components/architecture/DataFlowGraph";
import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import { ArchitectureFlow } from "@/components/diagrams/ArchitectureFlow";
import type { SectionRenderProps } from "@/rendering/types";

function TopologyDiagram({
  plan,
  showDebug,
}: {
  plan: SectionRenderProps["plan"];
  showDebug?: boolean;
}) {
  const topo = plan.architecture;
  if (!topo || topo.nodes.length === 0) return null;
  const dt = topo.diagram_type;
  if (dt === "layered") {
    return <LayerDiagram topology={topo} showDebug={showDebug} />;
  }
  if (dt === "pipeline") {
    return <PipelineFlow topology={topo} showDebug={showDebug} />;
  }
  if (dt === "dashboard_flow") {
    return <DataFlowGraph topology={topo} showDebug={showDebug} />;
  }
  return (
    <ArchitectureCanvas
      topology={topo}
      showDebug={showDebug}
      profileId={plan.profileId}
    />
  );
}

export function ArchitectureSection({ section, plan, index }: SectionRenderProps) {
  const inputs = section.sourceKeys.includes("inputs")
    ? section.bullets.filter((_, i) => i < section.bullets.length / 2)
    : section.bullets.slice(0, Math.ceil(section.bullets.length / 2));
  const outputs = section.bullets.slice(inputs.length);
  const hasTopology = Boolean(plan.architecture?.nodes.length);

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="architecture" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="System design" />
      {hasTopology ? (
        <TopologyDiagram plan={plan} />
      ) : (
        plan.layout.diagramPlacement !== "sidebar" && (
          <ArchitectureFlow
            plan={plan}
            inputs={inputs.length ? inputs : ["Documents", "APIs"]}
            outputs={outputs.length ? outputs : ["LandingContract", "Preview"]}
          />
        )
      )}
      {section.body && (
        <p className="mt-6 max-w-4xl text-sm leading-relaxed text-[var(--alf-text-muted)]">
          {section.body}
        </p>
      )}
    </SectionShell>
  );
}
