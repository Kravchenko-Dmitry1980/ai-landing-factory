import type { SectionData } from "./types";

export const SECTION_NAV_ORDER = [
  { id: "essence", label: "Суть" },
  { id: "tasks", label: "Задачи" },
  { id: "modules", label: "Системы" },
  { id: "stack", label: "Стек" },
  { id: "team", label: "Команда" },
  { id: "outlook", label: "Перспектива" },
] as const;

export type SectionAnchorId = (typeof SECTION_NAV_ORDER)[number]["id"];

const BLOCK_ANCHOR_IDS: Record<string, SectionAnchorId | "hero" | "io" | "results" | "purpose"> = {
  essence: "essence",
  tasks: "tasks",
  modules: "modules",
  tech_stack: "stack",
  stack: "stack",
  team: "team",
  outlook: "outlook",
  results: "results",
  purpose: "purpose",
  inputs: "io",
  outputs: "io",
};

export function sectionAnchorId(blockKey: string, fallback: string): string {
  return BLOCK_ANCHOR_IDS[blockKey] ?? fallback;
}

export function buildSectionNavItems(sections: SectionData[]) {
  const present = new Set(sections.map((s) => s.id));
  return SECTION_NAV_ORDER.filter((item) => present.has(item.id));
}
