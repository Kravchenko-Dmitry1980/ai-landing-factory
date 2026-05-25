"use client";

import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

export function StackSection({ section, plan, index }: SectionRenderProps) {
  const grouped = plan.stackGrouped;
  const categoryKeys = Object.keys(grouped).filter((k) => grouped[k]?.length);
  const useGrouped = categoryKeys.length > 0;
  const flatItems = section.bullets.length ? section.bullets : [section.body].filter(Boolean);
  const isUniversity = plan.profileId === "university_platform";

  if (!useGrouped && flatItems.length === 0) return null;

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="stack" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Technology stack" />
      {useGrouped ? (
        <div className="space-y-5">
          {categoryKeys.map((category) => (
            <div key={category}>
              <h4
                className={`mb-2 text-xs font-semibold uppercase tracking-wider ${
                  isUniversity ? "text-[var(--alf-text-muted)]" : "text-[var(--alf-accent)]"
                }`}
              >
                {category}
              </h4>
              <div className="flex flex-wrap gap-2">
                {grouped[category].map((item) => (
                  <span
                    key={item}
                    className={`rounded-full border px-3 py-1 text-sm ${
                      isUniversity
                        ? "border-[var(--alf-border)] bg-[var(--alf-accent-muted)] text-[var(--alf-accent)] font-medium"
                        : "border-[var(--alf-border)] bg-[var(--alf-surface)] text-[var(--alf-text)]"
                    }`}
                  >
                    {item}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-wrap gap-2">
          {flatItems.map((item) => (
            <span
              key={item}
              className="rounded-full border border-[var(--alf-border)] bg-[var(--alf-surface)] px-3 py-1 text-sm text-[var(--alf-text)]"
            >
              {item}
            </span>
          ))}
        </div>
      )}
    </SectionShell>
  );
}
