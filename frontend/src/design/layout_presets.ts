import type { SectionType } from "@/rendering/types";

export type LayoutPresetId =
  | "architecture_first"
  | "dashboard"
  | "research_report"
  | "enterprise_overview"
  | "technical_system";

export interface LayoutPreset {
  id: LayoutPresetId;
  label: string;
  sectionOrder: SectionType[];
  sectionWidths: Partial<Record<SectionType, "full" | "wide" | "narrow" | "split">>;
  gridLogic: "single" | "two-column" | "dashboard-grid";
  diagramPlacement: "inline" | "sidebar" | "hero-adjacent";
}

export const LAYOUT_PRESETS: Record<LayoutPresetId, LayoutPreset> = {
  architecture_first: {
    id: "architecture_first",
    label: "Architecture first",
    sectionOrder: [
      "hero",
      "essence",
      "architecture",
      "modules",
      "stack",
      "metrics",
      "team",
      "roadmap",
      "footer",
    ],
    sectionWidths: {
      hero: "full",
      architecture: "wide",
      modules: "split",
      stack: "narrow",
      metrics: "wide",
    },
    gridLogic: "two-column",
    diagramPlacement: "inline",
  },
  dashboard: {
    id: "dashboard",
    label: "Dashboard",
    sectionOrder: [
      "hero",
      "metrics",
      "architecture",
      "modules",
      "stack",
      "essence",
      "team",
      "roadmap",
      "footer",
    ],
    sectionWidths: {
      hero: "full",
      metrics: "wide",
      architecture: "split",
      modules: "split",
    },
    gridLogic: "dashboard-grid",
    diagramPlacement: "sidebar",
  },
  research_report: {
    id: "research_report",
    label: "Research report",
    sectionOrder: [
      "hero",
      "essence",
      "modules",
      "architecture",
      "metrics",
      "roadmap",
      "stack",
      "team",
      "footer",
    ],
    sectionWidths: {
      hero: "full",
      essence: "wide",
      modules: "full",
      roadmap: "wide",
    },
    gridLogic: "single",
    diagramPlacement: "inline",
  },
  enterprise_overview: {
    id: "enterprise_overview",
    label: "Enterprise overview",
    sectionOrder: [
      "hero",
      "essence",
      "modules",
      "metrics",
      "team",
      "stack",
      "roadmap",
      "architecture",
      "footer",
    ],
    sectionWidths: {
      hero: "full",
      team: "wide",
      metrics: "split",
    },
    gridLogic: "two-column",
    diagramPlacement: "hero-adjacent",
  },
  technical_system: {
    id: "technical_system",
    label: "Technical system",
    sectionOrder: [
      "hero",
      "architecture",
      "stack",
      "modules",
      "essence",
      "metrics",
      "roadmap",
      "team",
      "footer",
    ],
    sectionWidths: {
      architecture: "full",
      stack: "wide",
      modules: "split",
    },
    gridLogic: "two-column",
    diagramPlacement: "inline",
  },
};

export function getLayoutPreset(id: LayoutPresetId): LayoutPreset {
  return LAYOUT_PRESETS[id];
}

export const DEFAULT_LAYOUT_PRESET: LayoutPresetId = "architecture_first";
