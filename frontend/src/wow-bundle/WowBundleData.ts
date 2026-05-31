/**
 * Bundle data contract for the Interactive WOW Bundle (Stage P.7.2).
 *
 * Mirrors the backend mapper (`backend/app/services/export/wow_bundle_data.py`).
 * The standalone React/R3F app reads this payload from an embedded
 * `<script id="wow-data" type="application/json">` tag (or `window.__WOW_LANDING_DATA__`),
 * so the exported bundle runs fully offline with no backend and no CDN.
 *
 * This module has NO dependency on Next.js, the API client or `@/lib` so it can
 * be bundled standalone with esbuild.
 */

export interface WowBundleProject {
  title: string;
  subtitle?: string;
  client?: string;
  lead?: string;
  period?: string;
}

export interface WowBundleMetric {
  value: string;
  label: string;
  hint?: string;
}

export interface WowBundlePipelineStage {
  title: string;
  description?: string;
  tags?: string[];
}

export interface WowBundleModule {
  title: string;
  description?: string;
  type?: string;
}

export interface WowBundleStackGroup {
  group: string;
  items: string[];
}

export interface WowBundleTeamMember {
  name: string;
  role?: string;
  area?: string;
}

export interface WowBundleLinks {
  demo_url?: string;
  showcase_url?: string;
  landing_url?: string;
}

export interface WowBundleTheme {
  profile: string;
  accent?: string;
  mode?: "dark" | "light";
}

export interface WowBundleData {
  version: string;
  project: WowBundleProject;
  metrics: WowBundleMetric[];
  pipeline: WowBundlePipelineStage[];
  modules: WowBundleModule[];
  stack: WowBundleStackGroup[];
  team: WowBundleTeamMember[];
  links: WowBundleLinks;
  theme: WowBundleTheme;
}

export const DEFAULT_ACCENT = "#7c8bff";

const SAFE_URL_RE = /^(https?:\/\/|\/|\.\/|#)/i;

/** Keep only http(s)/relative URLs; drop javascript:/data:/file: and similar. */
export function safeLink(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined;
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  if (!SAFE_URL_RE.test(trimmed)) return undefined;
  return trimmed;
}

function str(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function optStr(value: unknown): string | undefined {
  const s = str(value).trim();
  return s ? s : undefined;
}

function strArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((v) => str(v).trim()).filter(Boolean);
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

/**
 * Normalize an untrusted payload into a complete `WowBundleData`.
 * Always returns a renderable object (never throws), so a malformed embed still
 * yields a usable hero rather than a blank screen.
 */
export function normalizeWowBundleData(raw: unknown): WowBundleData {
  const root = isRecord(raw) ? raw : {};
  const projectRaw = isRecord(root.project) ? root.project : {};
  const themeRaw = isRecord(root.theme) ? root.theme : {};
  const linksRaw = isRecord(root.links) ? root.links : {};

  const project: WowBundleProject = {
    title: optStr(projectRaw.title) ?? "AI-проект",
    subtitle: optStr(projectRaw.subtitle),
    client: optStr(projectRaw.client),
    lead: optStr(projectRaw.lead),
    period: optStr(projectRaw.period),
  };

  const metrics: WowBundleMetric[] = (Array.isArray(root.metrics) ? root.metrics : [])
    .filter(isRecord)
    .map((m) => ({
      value: str(m.value) || "0",
      label: str(m.label) || "—",
      hint: optStr(m.hint),
    }));

  const pipeline: WowBundlePipelineStage[] = (
    Array.isArray(root.pipeline) ? root.pipeline : []
  )
    .filter(isRecord)
    .map((p) => ({
      title: str(p.title) || "Этап",
      description: optStr(p.description),
      tags: strArray(p.tags),
    }));

  const modules: WowBundleModule[] = (Array.isArray(root.modules) ? root.modules : [])
    .filter(isRecord)
    .map((m) => ({
      title: str(m.title) || "Модуль",
      description: optStr(m.description),
      type: optStr(m.type),
    }));

  const stack: WowBundleStackGroup[] = (Array.isArray(root.stack) ? root.stack : [])
    .filter(isRecord)
    .map((s) => ({ group: str(s.group) || "Стек", items: strArray(s.items) }))
    .filter((s) => s.items.length > 0);

  const team: WowBundleTeamMember[] = (Array.isArray(root.team) ? root.team : [])
    .filter(isRecord)
    .map((t) => ({ name: str(t.name), role: optStr(t.role), area: optStr(t.area) }))
    .filter((t) => t.name.length > 0);

  const links: WowBundleLinks = {
    demo_url: safeLink(linksRaw.demo_url),
    showcase_url: safeLink(linksRaw.showcase_url),
    landing_url: safeLink(linksRaw.landing_url),
  };

  const accentRaw = str(themeRaw.accent).trim();
  const theme: WowBundleTheme = {
    profile: str(themeRaw.profile) || "tech",
    accent: /^#(?:[0-9a-f]{3}|[0-9a-f]{6}|[0-9a-f]{8})$/i.test(accentRaw)
      ? accentRaw
      : DEFAULT_ACCENT,
    mode: themeRaw.mode === "light" ? "light" : "dark",
  };

  return {
    version: str(root.version) || "1",
    project,
    metrics,
    pipeline,
    modules,
    stack,
    team,
    links,
    theme,
  };
}

/** Read the embedded payload from the DOM / window, normalized and safe. */
export function readEmbeddedBundleData(): WowBundleData {
  let raw: unknown = undefined;
  if (typeof document !== "undefined") {
    const el = document.getElementById("wow-data");
    if (el?.textContent) {
      try {
        raw = JSON.parse(el.textContent);
      } catch {
        raw = undefined;
      }
    }
  }
  if (raw === undefined && typeof window !== "undefined") {
    raw = (window as unknown as { __WOW_LANDING_DATA__?: unknown }).__WOW_LANDING_DATA__;
  }
  return normalizeWowBundleData(raw);
}

export type WowNodeKind = "data" | "ml" | "service" | "ui" | "storage" | "core";

const KIND_KEYWORDS: ReadonlyArray<readonly [WowNodeKind, readonly string[]]> = [
  ["data", ["data", "источник", "парс", "ingest", "scrap", "crawl", "telegram", "rss"]],
  ["ml", ["ml", "ai", "модел", "embed", "эмбед", "llm", "gpt", "bert", "ner", "semant", "семант", "класс", "rerank", "vlm"]],
  ["storage", ["storage", "хран", "qdrant", "neo4j", "postgres", "redis", "vector", "граф", "graph", "kafka", "s3", "elastic", "clickhouse", "база"]],
  ["ui", ["ui", "dashboard", "дашборд", "frontend", "интерфейс", "report", "отчёт", "digest", "дайджест", "bot", "бот"]],
  ["service", ["service", "api", "backend", "сервис", "оркестр", "pipeline", "обработк", "очеред"]],
];

export const NODE_KIND_COLOR: Record<WowNodeKind, string> = {
  data: "#38bdf8",
  ml: "#a855f7",
  service: "#6366f1",
  ui: "#22d3ee",
  storage: "#818cf8",
  core: "#c084fc",
};

/** Classify a label into a coarse module kind for 3D coloring. */
export function classifyKind(text: string, fallback: WowNodeKind = "service"): WowNodeKind {
  const lowered = text.toLowerCase();
  for (const [kind, keywords] of KIND_KEYWORDS) {
    if (keywords.some((kw) => lowered.includes(kw))) return kind;
  }
  return fallback;
}

export interface WowSceneNode {
  id: string;
  label: string;
  kind: WowNodeKind;
}

const MAX_SCENE_NODES = 8;

/** Build the orbiting scene nodes from modules / stack groups (deterministic). */
export function buildSceneNodes(data: WowBundleData): WowSceneNode[] {
  const nodes: WowSceneNode[] = [];
  const seen = new Set<string>();
  const push = (label: string) => {
    const clean = label.trim();
    if (!clean) return;
    const key = clean.toLowerCase();
    if (seen.has(key) || nodes.length >= MAX_SCENE_NODES) return;
    seen.add(key);
    nodes.push({
      id: `node-${nodes.length}`,
      label: clean.length > 26 ? `${clean.slice(0, 25)}\u2026` : clean,
      kind: classifyKind(clean),
    });
  };

  for (const m of data.modules) push(m.title);
  if (nodes.length < 3) {
    for (const s of data.stack) push(s.group);
  }
  if (nodes.length === 0) {
    nodes.push({ id: "node-0", label: "Источники", kind: "data" });
    nodes.push({ id: "node-1", label: "AI-обработка", kind: "ml" });
    nodes.push({ id: "node-2", label: "Хранилище", kind: "storage" });
    nodes.push({ id: "node-3", label: "Продукт", kind: "ui" });
  }
  return nodes;
}
