import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

const LONG_TEXT_CHARS = 320;

export function EssenceSection({ section, plan, index }: SectionRenderProps) {
  const { body } = plan.profile.typography;
  const text = section.body?.trim() ?? "";
  const isLong = text.length > LONG_TEXT_CHARS;

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="essence" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Summary" />
      {text &&
        (isLong ? (
          <details className="alf-collapsible max-w-4xl rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)] p-4">
            <summary className="text-sm">Показать полностью</summary>
            <p className={`${body} mt-3 text-[var(--alf-text)]`}>{text}</p>
          </details>
        ) : (
          <p className={`${body} max-w-4xl text-[var(--alf-text)]`}>{text}</p>
        ))}
    </SectionShell>
  );
}
