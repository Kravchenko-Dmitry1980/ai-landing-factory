import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

export function FooterSection({ section, plan, index }: SectionRenderProps) {
  const { caption, body } = plan.profile.typography;
  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="footer" index={index}>
      <footer className="border-t border-[var(--alf-border)] pt-8">
        <p className={caption}>{section.title}</p>
        <p className={`${body} mt-2 text-[var(--alf-text-muted)]`}>{section.body}</p>
        <ul className="mt-3 flex flex-wrap gap-4">
          {section.bullets.map((b) => (
            <li key={b} className="text-xs text-[var(--alf-text-muted)]">
              {b}
            </li>
          ))}
        </ul>
      </footer>
    </SectionShell>
  );
}
