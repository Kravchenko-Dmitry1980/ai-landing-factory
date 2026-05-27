import { buildSectionNavItems } from "@/rendering/sectionAnchors";
import type { RenderPlan } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
}

export function SectionAnchorNav({ plan }: Props) {
  const items = buildSectionNavItems(plan.sections);
  if (items.length === 0) return null;

  return (
    <nav
      className="alf-section-nav sticky top-0 z-10 mx-auto flex max-w-7xl flex-wrap gap-x-3 gap-y-2 border-b border-[var(--alf-border)] bg-[color-mix(in_srgb,var(--alf-bg)_92%,transparent)] px-4 py-3 backdrop-blur-sm md:px-8"
      aria-label="Навигация по разделам"
    >
      {items.map((item) => (
        <a
          key={item.id}
          href={`#${item.id}`}
          className="rounded-md px-2.5 py-1 text-sm font-medium text-[var(--alf-text-muted)] transition-colors hover:bg-[var(--alf-accent-muted)] hover:text-[var(--alf-accent)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--alf-accent)]"
        >
          {item.label}
        </a>
      ))}
    </nav>
  );
}
