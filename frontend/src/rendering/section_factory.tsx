import { resolveSectionComponent } from "./registry";
import type { RenderPlan, SectionData } from "./types";

export function createSectionElement(
  section: SectionData,
  plan: RenderPlan,
  index: number,
) {
  const Component = resolveSectionComponent(section.type);
  return <Component key={section.id} section={section} plan={plan} index={index} />;
}

export function createSectionTree(plan: RenderPlan) {
  return plan.sections.map((section, index) =>
    createSectionElement(section, plan, index),
  );
}
