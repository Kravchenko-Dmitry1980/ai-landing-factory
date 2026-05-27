import { heroModeClass } from "@/design/applyThemeTokens";
import { SectionShell } from "@/components/grids/SectionShell";
import { NodeBlock } from "@/components/diagrams/NodeBlock";
import type { SectionRenderProps } from "@/rendering/types";

export function HeroSection({ section, plan, index }: SectionRenderProps) {
  const { hero, body, caption } = plan.profile.typography;
  const isUniversity = plan.profileId === "university_platform";
  const heroBorder = isUniversity
    ? "border-b border-[#111111] pb-8 md:pb-10"
    : "border-b border-[var(--alf-border)] pb-8 md:pb-10";
  const heroMode = heroModeClass(plan.themeTokens.hero_mode);
  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="hero" index={index}>
      <div id="hero" className={`alf-hero-inner ${heroBorder} ${heroMode}`}>
        <p className={caption}>
          {isUniversity ? "Платформа УИИ · проектный лендинг" : "Enterprise project landing"}
        </p>
        <h1 className={`${hero} mt-3 text-[var(--alf-text)]`}>{section.title}</h1>
        {section.body && (
          <p className={`${body} mt-4 max-w-3xl text-[var(--alf-text-muted)]`}>{section.body}</p>
        )}
        <div className="mt-6 flex flex-wrap gap-3">
          {section.meta?.timeline && (
            <NodeBlock label="Timeline" value={section.meta.timeline} />
          )}
          {section.meta?.lead && <NodeBlock label="Lead" value={section.meta.lead} />}
          {section.bullets.map((b) => (
            <span
              key={b}
              className={`rounded px-3 py-1 text-sm ${
                isUniversity
                  ? "border border-[var(--alf-border)] bg-[var(--alf-accent-muted)] text-[var(--alf-accent)] font-medium"
                  : "border border-[var(--alf-border)] text-[var(--alf-text)]"
              }`}
            >
              {b}
            </span>
          ))}
        </div>
      </div>
    </SectionShell>
  );
}
