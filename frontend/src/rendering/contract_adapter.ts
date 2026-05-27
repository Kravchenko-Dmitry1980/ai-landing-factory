import { normalizeBulletList } from "@/lib/normalizeBulletText";
import {
  DEFAULT_LAYOUT_PRESET,
  getLayoutPreset,
  LAYOUT_PRESETS,
  type LayoutPresetId,
} from "@/design/layout_presets";
import { runHallmarkQualityGate, runArchitectureHallmarkGate } from "@/design/hallmark_rules";
import { applyThemeTokenOverrides } from "@/design/applyThemeTokens";
import { normalizeThemeTokens } from "@/design/themeTokens";
import { getStyleProfile } from "@/design/style_profiles";
import type { StyleProfileId } from "@/design/style_profiles";
import { isStyleProfileId as isExportProfileId } from "@/design/styleProfiles";
import { coerceLegacyProfileId, isLegacyStyleProfileId } from "@/design/legacyProfileCompat";
import {
  DEFAULT_STYLE_CONFIG,
  resolveThemeTokens,
} from "@/lib/styleConfig";
import {
  resolveExportTheme as resolveExportThemeFromConfig,
  resolvePreviewProfileId,
  resolveStyleConfig,
} from "@/lib/resolveStyleConfig";
import { buildFidelityData } from "./fidelity_resolver";
import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingBlockContent,
  LandingContract,
  LandingStyleConfig,
} from "@/lib/types";
import type {
  RenderConfig,
  RenderMeta,
  RenderPlan,
  SectionData,
  SectionType,
} from "./types";
import { sectionAnchorId } from "./sectionAnchors";

export type { RenderConfig } from "./types";

export function isStyleProfileId(value: string): value is StyleProfileId {
  return isExportProfileId(value) || isLegacyStyleProfileId(value);
}

export function normalizeProfileId(value: string): StyleProfileId {
  if (isExportProfileId(value)) return value;
  return coerceLegacyProfileId(value);
}

const BLOCK_TO_SECTION: Record<string, SectionType | null> = {
  tagline: "hero",
  modules: "modules",
  essence: "essence",
  purpose: "essence",
  tasks: "modules",
  inputs: "architecture",
  outputs: "architecture",
  results: "metrics",
  stack: "stack",
  team: "team",
  outlook: "roadmap",
  tech_stack: "stack",
};

function blockToSection(block: LandingBlockContent): SectionData | null {
  const type = BLOCK_TO_SECTION[block.key];
  if (!type || type === "hero") return null;
  const hasContent = Boolean(block.body?.trim()) || block.bullets.length > 0;
  if (!hasContent) return null;
  return {
    id: sectionAnchorId(block.key, `${type}-${block.key}`),
    type,
    title: block.title,
    body: block.body ?? "",
    bullets: normalizeBulletList(block.bullets),
    sourceKeys: [block.key],
  };
}

function buildHero(
  blocks: LandingBlockContent[],
  meta: RenderMeta,
): SectionData {
  const tagline = blocks.find((b) => b.key === "tagline");
  const essence = blocks.find((b) => b.key === "essence");
  return {
    id: "hero",
    type: "hero",
    title: meta.title ?? tagline?.title ?? "Project overview",
    body:
      tagline?.body ||
      essence?.body ||
      meta.lead ||
      "Structured landing generated from LandingContract.",
    bullets: meta.client ? [`Client: ${meta.client}`] : [],
    sourceKeys: ["tagline", "essence"],
    meta: {
      timeline: meta.timeline ?? "",
      lead: meta.lead ?? "",
    },
  };
}

function buildFooter(meta: RenderMeta): SectionData {
  return {
    id: "footer-main",
    type: "footer",
    title: "Document",
    body: `AI Landing Factory · v${meta.version}`,
    bullets: [
      meta.client ? `Organization: ${meta.client}` : "",
      meta.updatedAt ? `Updated: ${new Date(meta.updatedAt).toLocaleDateString()}` : "",
    ].filter(Boolean),
    sourceKeys: [],
  };
}

function mergeArchitecture(sections: SectionData[]): SectionData[] {
  const arch = sections.filter((s) => s.type === "architecture");
  if (arch.length <= 1) return sections;
  const merged: SectionData = {
    id: "architecture-merged",
    type: "architecture",
    title: "System architecture",
    body: arch.map((a) => a.body).filter(Boolean).join("\n\n"),
    bullets: arch.flatMap((a) => a.bullets),
    sourceKeys: arch.flatMap((a) => a.sourceKeys),
    meta: {
      inputs: arch.find((a) => a.sourceKeys.includes("inputs"))?.title ?? "",
      outputs: arch.find((a) => a.sourceKeys.includes("outputs"))?.title ?? "",
    },
  };
  return [
    ...sections.filter((s) => s.type !== "architecture"),
    merged,
  ];
}

function orderSections(
  sections: SectionData[],
  order: SectionType[],
): SectionData[] {
  const map = new Map<SectionType, SectionData[]>();
  for (const s of sections) {
    const list = map.get(s.type) ?? [];
    list.push(s);
    map.set(s.type, list);
  }
  const out: SectionData[] = [];
  for (const type of order) {
    const list = map.get(type);
    if (list) out.push(...list);
  }
  for (const s of sections) {
    if (!out.includes(s)) out.push(s);
  }
  return out;
}

export function buildRenderPlan(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  config: RenderConfig,
  semantic?: GeneratedSemanticLanding | null,
): RenderPlan {
  const styleConfig = config.styleConfig ?? DEFAULT_STYLE_CONFIG;
  const profileId = resolvePreviewProfileId(styleConfig);
  const layoutId = config.layoutId;
  const themeTokens = resolveThemeTokens(styleConfig);
  const normalized = normalizeThemeTokens(styleConfig);
  const cssVars = applyThemeTokenOverrides(styleConfig);
  const profile = getStyleProfile(profileId);
  const layout = getLayoutPreset(layoutId);

  const meta: RenderMeta = {
    projectId: landing.project_id,
    title: contract?.title ?? null,
    client: contract?.client ?? null,
    timeline: contract?.timeline ?? null,
    lead: contract?.lead ?? null,
    version: contract?.version ?? 1,
    updatedAt: contract?.updated_at ?? landing.generated_at,
  };

  const fidelity = buildFidelityData(contract, semantic ?? null, landing);

  const rawSections = landing.blocks
    .map(blockToSection)
    .filter((s): s is SectionData => s !== null);

  const enrichedSections = rawSections.map((section) => {
    if (section.type === "modules" && fidelity.modules.length > 0) {
      const hasStructuredModules = (contract?.fidelity?.modules?.length ?? 0) > 0;
      const isModulesBlock = section.sourceKeys.includes("modules");
      if (hasStructuredModules || isModulesBlock) {
        return {
          ...section,
          id: "modules",
          title: "Ключевые системы",
          meta: { ...section.meta, dataSource: fidelity.diagnostics.modulesSource },
        };
      }
      return section;
    }
    if (section.type === "team" && fidelity.team.length > 0) {
      return {
        ...section,
        id: "team",
        title: "Команда проекта",
        meta: { ...section.meta, dataSource: fidelity.diagnostics.teamSource },
      };
    }
    if (section.type === "stack" && fidelity.diagnostics.stackCategoriesCount > 0) {
      return {
        ...section,
        id: "stack",
        title: "Используемый технологический стек",
        meta: { ...section.meta, dataSource: fidelity.diagnostics.stackSource },
      };
    }
    return section;
  });

  const withHero = [buildHero(landing.blocks, meta), ...mergeArchitecture(enrichedSections)];
  const withFooter = [...withHero, buildFooter(meta)];
  const ordered = orderSections(withFooter, layout.sectionOrder);

  const plan: RenderPlan = {
    meta,
    profile,
    layout,
    profileId,
    layoutId,
    themeTokens,
    normalizedTokens: normalized,
    cssVars,
    sections: ordered,
    architecture: semantic?.architecture ?? null,
    modules: fidelity.modules,
    team: fidelity.team,
    stackGrouped: fidelity.stackGrouped,
    fidelityDiagnostics: fidelity.diagnostics,
    hallmarkViolations: [],
    builtAt: Date.now(),
  };
  plan.hallmarkViolations = [
    ...runHallmarkQualityGate(plan),
    ...runArchitectureHallmarkGate(plan),
  ];
  return plan;
}

export function defaultRenderConfig(
  landing: GeneratedLanding,
  contract: LandingContract | null,
): RenderConfig {
  const styleConfig = resolveStyleConfig(contract);
  const profileId = resolvePreviewProfileId(styleConfig);
  let layoutId: LayoutPresetId = DEFAULT_LAYOUT_PRESET;
  const ps = contract?.presentation_style ?? "";
  if (ps.startsWith("layout:")) {
    const id = ps.replace("layout:", "") as LayoutPresetId;
    if (id in LAYOUT_PRESETS) layoutId = id;
  }
  if (!contract?.style_config && !contract?.presentation_style) {
    return {
      profileId: "university_platform",
      layoutId,
      styleConfig: DEFAULT_STYLE_CONFIG,
    };
  }
  return { profileId, layoutId, styleConfig };
}

export const RENDER_CONFIG_STORAGE_KEY = "alf_render_config";

export function loadRenderConfig(
  projectId: string,
  landing: GeneratedLanding,
  contract: LandingContract | null,
): RenderConfig {
  const base = defaultRenderConfig(landing, contract);
  if (typeof window === "undefined") return base;
  try {
    const raw = localStorage.getItem(`${RENDER_CONFIG_STORAGE_KEY}_${projectId}`);
    if (!raw) return base;
    const parsed = JSON.parse(raw) as Partial<RenderConfig>;
    const styleConfig = parsed.styleConfig ?? base.styleConfig;
    const profileId = styleConfig
      ? resolvePreviewProfileId(styleConfig)
      : normalizeProfileId(parsed.profileId ?? base.profileId);
    return {
      profileId,
      layoutId: parsed.layoutId ?? base.layoutId,
      styleConfig,
      showDevPanel: parsed.showDevPanel ?? false,
    };
  } catch {
    return base;
  }
}

/** Priority: URL ?style= → contract style_config → localStorage → default */
export function resolveRenderConfig(
  projectId: string,
  landing: GeneratedLanding,
  contract: LandingContract | null,
  urlStyle?: string | null,
): RenderConfig {
  let config = loadRenderConfig(projectId, landing, contract);

  const contractStyle = resolveStyleConfig(contract);
  if (contract?.style_config?.profile) {
    config = {
      ...config,
      profileId: resolvePreviewProfileId(contractStyle),
      styleConfig: contractStyle,
    };
  }

  if (urlStyle) {
    const normalized = normalizeProfileId(urlStyle);
    config = {
      ...config,
      profileId: normalized,
      styleConfig: config.styleConfig ?? contractStyle,
    };
  }

  return config;
}

export function saveRenderConfig(projectId: string, config: RenderConfig): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(
    `${RENDER_CONFIG_STORAGE_KEY}_${projectId}`,
    JSON.stringify(config),
  );
}

/** Active preview profile: URL ?style= → renderConfig → contract.style_config → default */
export function resolveActiveProfileId(
  renderConfig: RenderConfig | null | undefined,
  contract: LandingContract | null | undefined,
  urlStyle?: string | null,
  landing?: GeneratedLanding | null,
): StyleProfileId {
  if (urlStyle) {
    return normalizeProfileId(urlStyle);
  }
  if (renderConfig?.styleConfig) {
    return resolvePreviewProfileId(renderConfig.styleConfig);
  }
  if (renderConfig?.profileId) {
    return normalizeProfileId(renderConfig.profileId);
  }
  if (contract?.style_config?.profile) {
    return resolvePreviewProfileId(resolveStyleConfig(contract));
  }
  if (landing) {
    return defaultRenderConfig(landing, contract ?? null).profileId;
  }
  return "university_platform";
}

/** Backend export theme query for the active preview profile. */
export function resolveExportTheme(
  renderConfig: RenderConfig | null | undefined,
  contract: LandingContract | null | undefined,
  urlStyle?: string | null,
  landing?: GeneratedLanding | null,
): string {
  if (renderConfig?.styleConfig) {
    return resolveExportThemeFromConfig(renderConfig.styleConfig);
  }
  const fromContract = resolveStyleConfig(contract ?? null);
  if (contract?.style_config || contract?.presentation_style) {
    return resolveExportThemeFromConfig(fromContract);
  }
  const profileId = resolveActiveProfileId(
    renderConfig,
    contract,
    urlStyle,
    landing,
  );
  return profileId;
}

export function resolveExportStyleConfig(
  renderConfig: RenderConfig | null | undefined,
  contract: LandingContract | null | undefined,
): LandingStyleConfig {
  if (renderConfig?.styleConfig) {
    return renderConfig.styleConfig;
  }
  return resolveStyleConfig(contract ?? null);
}

export function buildPreviewHref(
  projectId: string,
  profileId?: StyleProfileId | string | null,
): string {
  const base = `/preview/${projectId}`;
  if (profileId) {
    const normalized = normalizeProfileId(profileId);
    return `${base}?style=${encodeURIComponent(normalized)}`;
  }
  return base;
}
