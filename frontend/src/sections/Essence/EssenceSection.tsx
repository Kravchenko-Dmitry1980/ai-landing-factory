import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

export function EssenceSection({ section, plan, index }: SectionRenderProps) {
  const { body } = plan.profile.typography;
  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="essence" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Summary" />
      {section.body && (
        <p className={`${body} max-w-4xl text-[var(--alf-text)]`}>{section.body}</p>
      )}
    </SectionShell>
  );
}
