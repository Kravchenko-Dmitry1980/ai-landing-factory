import type { ComponentType } from "react";
import { ArchitectureSection } from "@/sections/Architecture/ArchitectureSection";
import { EssenceSection } from "@/sections/Essence/EssenceSection";
import { FooterSection } from "@/sections/Footer/FooterSection";
import { HeroSection } from "@/sections/Hero/HeroSection";
import { MetricsSection } from "@/sections/Metrics/MetricsSection";
import { ModulesSection } from "@/sections/Modules/ModulesSection";
import { RoadmapSection } from "@/sections/Roadmap/RoadmapSection";
import { StackSection } from "@/sections/Stack/StackSection";
import { TeamSection } from "@/sections/Team/TeamSection";
import type { SectionRenderProps, SectionType } from "./types";

export type SectionComponent = ComponentType<SectionRenderProps>;

export const SECTION_REGISTRY: Record<SectionType, SectionComponent> = {
  hero: HeroSection,
  essence: EssenceSection,
  architecture: ArchitectureSection,
  modules: ModulesSection,
  metrics: MetricsSection,
  stack: StackSection,
  team: TeamSection,
  roadmap: RoadmapSection,
  footer: FooterSection,
};

export function resolveSectionComponent(type: SectionType): SectionComponent {
  const component = SECTION_REGISTRY[type];
  if (!component) {
    throw new Error(`No section registered for type: ${type}`);
  }
  return component;
}

export function listRegisteredSectionTypes(): SectionType[] {
  return Object.keys(SECTION_REGISTRY) as SectionType[];
}
