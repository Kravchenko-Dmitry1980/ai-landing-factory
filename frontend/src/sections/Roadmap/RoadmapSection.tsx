import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

export function RoadmapSection({ section, plan, index }: SectionRenderProps) {
  const phases = section.bullets.length
    ? section.bullets
    : section.body
      ? section.body.split(/\n+/).filter(Boolean)
      : ["Phase 1", "Phase 2"];

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="roadmap" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Roadmap" />
      <ol className="relative border-l border-[var(--alf-border)] pl-6">
        {phases.map((phase, i) => (
          <li key={phase} className="mb-8 last:mb-0">
            <span
              className="absolute -left-[5px] mt-1.5 h-2.5 w-2.5 rounded-full border-2 border-[var(--alf-accent)] bg-[var(--alf-bg)]"
              aria-hidden
            />
            <p className="text-xs font-medium text-[var(--alf-accent)]">Step {i + 1}</p>
            <p className="mt-1 text-sm text-[var(--alf-text)]">{phase}</p>
          </li>
        ))}
      </ol>
    </SectionShell>
  );
}
