"use client";

import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

function parseModuleItem(item: string): { name: string; description: string } {
  const idx = item.indexOf(":");
  if (idx > 0 && idx < 60) {
    return {
      name: item.slice(0, idx).trim(),
      description: item.slice(idx + 1).trim(),
    };
  }
  return { name: "Module", description: item };
}

export function ModulesSection({ section, plan, index }: SectionRenderProps) {
  const structured = plan.modules;
  const useStructured = structured.length > 0;
  const fallbackItems = section.bullets.length
    ? section.bullets
    : [section.body].filter(Boolean);
  const modules = useStructured
    ? structured
    : fallbackItems.map((item) => {
        const parsed = parseModuleItem(item);
        return { name: parsed.name, description: parsed.description, type: "" };
      });

  const { body, h3 } = plan.profile.typography;
  const { gridGap, cardPad } = plan.profile.spacing;
  const isUniversity = plan.profileId === "university_platform";

  if (modules.length === 0) return null;

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="modules" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Workstreams" />
      <div className={`grid ${gridGap} sm:grid-cols-2 lg:grid-cols-3`}>
        {modules.map((mod) => (
          <article
            key={mod.name}
            className={`alf-card-lift ${cardPad} rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)] ${
              isUniversity ? "shadow-none" : ""
            }`}
            style={{ borderRadius: "var(--alf-radius, 0.5rem)" }}
          >
            <h3 className={`${h3} text-[var(--alf-text)]`}>{mod.name}</h3>
            {mod.description && (
              <p className={`${body} mt-2 text-[var(--alf-text-muted)]`}>{mod.description}</p>
            )}
            {mod.type && (
              <span
                className={`mt-3 inline-block rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  isUniversity
                    ? "bg-[var(--alf-accent-muted)] text-[var(--alf-accent)]"
                    : "text-[var(--alf-accent)]"
                }`}
              >
                {mod.type}
              </span>
            )}
          </article>
        ))}
      </div>
    </SectionShell>
  );
}
