import type { ExtendedThemeVars } from "@/design/applyThemeTokens";
import type { ThemeTokens as NormalizedThemeTokens } from "@/design/themeTokens";
import type { LayoutPreset, LayoutPresetId } from "@/design/layout_presets";
import type { StyleProfile, StyleProfileId } from "@/design/style_profiles";
import type { HallmarkViolation } from "@/design/hallmark_rules";
import type {
  ArchitectureTopology,
  LandingModule,
  LandingStyleConfig,
  TeamMember,
} from "@/lib/types";
import type { ThemeTokens } from "@/lib/styleIntent";

export type FidelityDataSource = "fidelity" | "semantic" | "blocks" | "fallback";

export interface FidelityDiagnostics {
  modulesSource: FidelityDataSource;
  teamSource: FidelityDataSource;
  stackSource: FidelityDataSource;
  modulesCount: number;
  teamCount: number;
  stackCategoriesCount: number;
}

export type SectionType =
  | "hero"
  | "essence"
  | "architecture"
  | "modules"
  | "metrics"
  | "stack"
  | "team"
  | "roadmap"
  | "footer";

export interface SectionData {
  id: string;
  type: SectionType;
  title: string;
  body: string;
  bullets: string[];
  sourceKeys: string[];
  meta?: Record<string, string>;
}

export interface RenderMeta {
  projectId: string;
  title: string | null;
  client: string | null;
  timeline: string | null;
  lead: string | null;
  version: number;
  updatedAt: string | null;
}

export interface RenderPlan {
  meta: RenderMeta;
  profile: StyleProfile;
  layout: LayoutPreset;
  profileId: StyleProfileId;
  layoutId: LayoutPresetId;
  themeTokens: ThemeTokens;
  normalizedTokens: NormalizedThemeTokens;
  cssVars: ExtendedThemeVars;
  sections: SectionData[];
  architecture?: ArchitectureTopology | null;
  modules: LandingModule[];
  team: TeamMember[];
  stackGrouped: Record<string, string[]>;
  fidelityDiagnostics: FidelityDiagnostics;
  hallmarkViolations: HallmarkViolation[];
  builtAt: number;
}

export interface SectionRenderProps {
  section: SectionData;
  plan: RenderPlan;
  index: number;
}

export interface RenderConfig {
  profileId: StyleProfileId;
  layoutId: LayoutPresetId;
  styleConfig?: LandingStyleConfig;
  showDevPanel?: boolean;
}
