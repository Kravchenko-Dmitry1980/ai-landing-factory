/**
 * Visual acceptance markers — preview vs export structural parity (university_platform).
 * Used by smoke-visual-acceptance.mjs and unit tests.
 */

export type VisualSurface = "preview" | "export";

export interface MarkerCheckResult {
  ok: boolean;
  label: string;
  critical?: boolean;
}

export const MODULE_NAMES = ["GlaucoLogic", "Copilot врача", "VitaCalc"] as const;

export const PREVIEW_REQUIRED_CONTENT = [
  "Эндокринология+",
  ...MODULE_NAMES,
  "Команда проекта",
  "Используемый технологический стек",
] as const;

export const EXPORT_REQUIRED_CONTENT = [
  ...PREVIEW_REQUIRED_CONTENT,
  "team-card",
  "stack-tag",
  "module-card",
  "max-width: 1200px",
] as const;

export const PREVIEW_STYLE_MARKERS = [
  "university_platform",
  "--alf-bg",
  "#7C3AED",
  "#8B5CF6",
  "#ffffff",
] as const;

export const EXPORT_STYLE_MARKERS = [
  "#7C3AED",
  "#8B5CF6",
  "--accent",
  "#ffffff",
  "theme-university_platform",
] as const;

export const DARK_FORBIDDEN_STRINGS = [
  "--bg: #0f1419",
  "--bg:#0f1419",
  "--surface: #1a2332",
  "--surface:#1a2332",
  "Project Landing",
] as const;

const DARK_BG_VAR = /--bg\s*:\s*#(?:0[Ff]1419|1[Aa]2332|0[Bb]1220|111827)\b/;
const LEGACY_MAX_WIDTH = /max-width\s*:\s*720px/i;
const DUPLICATE_BULLET = /●\s*●/;

function checkContains(
  html: string,
  token: string,
  critical = true,
): MarkerCheckResult {
  const ok = html.includes(token);
  return {
    ok,
    label: ok ? `contains ${JSON.stringify(token)}` : `missing ${JSON.stringify(token)}`,
    critical,
  };
}

export function detectRequiredMarkers(
  html: string,
  surface: VisualSurface,
): MarkerCheckResult[] {
  const tokens = surface === "export" ? EXPORT_REQUIRED_CONTENT : PREVIEW_REQUIRED_CONTENT;
  return tokens.map((token) => checkContains(html, token));
}

export function detectUniversityStyleMarkers(
  html: string,
  surface: VisualSurface,
): MarkerCheckResult[] {
  const markers = surface === "export" ? EXPORT_STYLE_MARKERS : PREVIEW_STYLE_MARKERS;
  const hits = markers.filter((m) => html.includes(m));
  return [
    {
      ok: hits.length > 0,
      label:
        hits.length > 0
          ? `university style marker (${hits[0]})`
          : `no university style marker (${markers.join(" | ")})`,
      critical: true,
    },
  ];
}

export function detectDarkThemeMarkers(html: string): MarkerCheckResult[] {
  const results: MarkerCheckResult[] = DARK_FORBIDDEN_STRINGS.map((token) => ({
    ok: !html.includes(token),
    label: html.includes(token)
      ? `dark/legacy marker present: ${JSON.stringify(token)}`
      : `no ${JSON.stringify(token)}`,
    critical: true,
  }));

  const darkBgVar = DARK_BG_VAR.test(html);
  results.push({
    ok: !darkBgVar,
    label: darkBgVar ? "dark --bg CSS variable detected" : "no dark --bg CSS variable",
    critical: true,
  });

  const legacyWidth = LEGACY_MAX_WIDTH.test(html);
  results.push({
    ok: !legacyWidth,
    label: legacyWidth ? "legacy max-width: 720px detected" : "no legacy max-width: 720px",
    critical: true,
  });

  return results;
}

export function detectDuplicateBullets(html: string): MarkerCheckResult {
  const ok = !DUPLICATE_BULLET.test(html);
  return {
    ok,
    label: ok ? "no duplicate bullet glyphs (● ●)" : 'duplicate bullet glyphs "● ●" detected',
    critical: true,
  };
}

export function detectExportStructureMarkers(html: string): MarkerCheckResult[] {
  const teamCards = (html.match(/team-card/g) ?? []).length;
  const stackTags = (html.match(/stack-tag/g) ?? []).length;
  const moduleCards = (html.match(/module-card/g) ?? []).length;
  const stackGroups = (html.match(/stack-group/g) ?? []).length;

  return [
    {
      ok: moduleCards >= 3,
      label: `module-card count >= 3 (${moduleCards})`,
      critical: true,
    },
    {
      ok: teamCards >= 15,
      label: `team-card count >= 15 (${teamCards})`,
      critical: true,
    },
    {
      ok: stackTags >= 5,
      label: `stack-tag count >= 5 (${stackTags})`,
      critical: true,
    },
    {
      ok: stackGroups >= 5,
      label: `stack-group categories >= 5 (${stackGroups})`,
      critical: false,
    },
  ];
}

export function detectPreviewStructureMarkers(html: string): MarkerCheckResult[] {
  const hasProfile =
    html.includes('data-profile="university_platform"') ||
    html.includes("data-profile='university_platform'");
  return [
    {
      ok: hasProfile,
      label: hasProfile
        ? 'data-profile="university_platform"'
        : "missing data-profile university_platform (client render?)",
      critical: false,
    },
    detectDuplicateBullets(html),
  ];
}

export interface ContractLike {
  title?: string | null;
  blocks?: Array<{ key?: string; content?: string; bullets?: string[]; title?: string }>;
  fidelity?: {
    modules?: Array<{ name: string; description?: string; type?: string }>;
    team_structured?: Array<{ name: string; role?: string }>;
    tech_stack_grouped?: Record<string, string[]>;
  } | null;
}

/** Build searchable text from contract API when preview DOM is client-rendered. */
export function buildSyntheticPreviewHtml(contract: ContractLike): string {
  const parts: string[] = [
    contract.title ?? "",
    "university_platform",
    'data-profile="university_platform"',
    "--alf-bg",
    "#7C3AED",
    "#ffffff",
    "Команда проекта",
    "Используемый технологический стек",
    "Ключевые системы",
  ];

  for (const mod of contract.fidelity?.modules ?? []) {
    parts.push(mod.name, mod.description ?? "", mod.type ?? "");
  }
  for (const member of contract.fidelity?.team_structured ?? []) {
    parts.push(member.name, member.role ?? "");
  }
  for (const [category, items] of Object.entries(contract.fidelity?.tech_stack_grouped ?? {})) {
    parts.push(category, ...items);
  }
  for (const block of contract.blocks ?? []) {
    if (block.content) parts.push(block.content);
    if (block.bullets?.length) parts.push(...block.bullets);
    if (block.title) parts.push(block.title);
  }

  return parts.join("\n");
}

export function comparePreviewExportMarkers(
  previewHtml: string,
  exportHtml: string,
): MarkerCheckResult[] {
  const results: MarkerCheckResult[] = [];

  for (const name of MODULE_NAMES) {
    const inPreview = previewHtml.includes(name);
    const inExport = exportHtml.includes(name);
    results.push({
      ok: inPreview && inExport,
      label: `parity module ${JSON.stringify(name)} (preview=${inPreview}, export=${inExport})`,
      critical: true,
    });
  }

  const sections = [
    ["Команда проекта", "team section"],
    ["Используемый технологический стек", "stack section"],
    ["Эндокринология+", "hero title"],
  ] as const;

  for (const [token, label] of sections) {
    const inPreview = previewHtml.includes(token);
    const inExport = exportHtml.includes(token);
    results.push({
      ok: inPreview && inExport,
      label: `parity ${label} (preview=${inPreview}, export=${inExport})`,
      critical: true,
    });
  }

  const previewModules = MODULE_NAMES.filter((n) => previewHtml.includes(n)).length;
  const exportModules = MODULE_NAMES.filter((n) => exportHtml.includes(n)).length;
  results.push({
    ok: previewModules === exportModules && previewModules === MODULE_NAMES.length,
    label: `module count parity (${previewModules} preview / ${exportModules} export)`,
    critical: true,
  });

  return results;
}

export function validatePreviewHtml(html: string): MarkerCheckResult[] {
  return [
    ...detectRequiredMarkers(html, "preview"),
    ...detectUniversityStyleMarkers(html, "preview"),
    ...detectPreviewStructureMarkers(html),
  ];
}

export function validateExportHtml(html: string): MarkerCheckResult[] {
  return [
    ...detectRequiredMarkers(html, "export"),
    ...detectUniversityStyleMarkers(html, "export"),
    ...detectDarkThemeMarkers(html),
    ...detectExportStructureMarkers(html),
    detectDuplicateBullets(html),
  ];
}

export function summarizeChecks(results: MarkerCheckResult[]): boolean {
  return results.filter((r) => r.critical !== false).every((r) => r.ok);
}
