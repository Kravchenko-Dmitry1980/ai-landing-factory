/**
 * Deterministic data mapping for the WOW R3F hero (Stage P.7.1).
 *
 * Turns the landing contract / generated landing / semantic landing into a
 * compact, semantically meaningful scene description. The 3D scene must reflect
 * the *real* project structure (modules, stack, metrics, pipeline) — never
 * random geometry — so all values here are derived deterministically from the
 * project data.
 *
 * This mirrors (in a lightweight way) the backend WOW metric/pipeline logic so
 * the interactive preview stays consistent with the exported WOW HTML.
 */

import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
} from "@/lib/types";

export interface WowHeroChip {
  label: string;
  value: string;
}

export interface WowHeroMetric {
  label: string;
  value: string;
  hint?: string;
  source: "extracted" | "derived" | "fallback";
}

export interface WowHeroNode {
  id: string;
  label: string;
  /** Coarse module kind, used to color the 3D node. */
  kind: "data" | "ml" | "service" | "ui" | "storage" | "core";
}

export interface WowPipelineStage {
  id: string;
  title: string;
  tags: string[];
}

export interface WowHeroData {
  title: string;
  subtitle: string;
  status: string;
  chips: WowHeroChip[];
  metrics: WowHeroMetric[];
  nodes: WowHeroNode[];
  pipeline: WowPipelineStage[];
}

const MAX_NODES = 8;
const MIN_METRICS = 4;
const MAX_METRICS = 6;

const NUM_RE =
  /(\d{1,3}(?:[ \u00a0]\d{3})+\s*\+?|\d+(?:[.,]\d+)?\s*%|\d+\s*\+|\d+)\s*([A-Za-zА-Яа-яЁё][A-Za-zА-Яа-яЁё0-9@-]*)?/g;

const CONTEXT_UNITS: ReadonlyArray<readonly [string, string]> = [
  ["постов", "постов"],
  ["пост", "постов"],
  ["post", "posts"],
  ["сообщени", "сообщений"],
  ["message", "messages"],
  ["модел", "AI-моделей"],
  ["model", "AI models"],
  ["тем", "тем / кластеров"],
  ["topic", "topics"],
  ["кластер", "кластеров"],
  ["cluster", "clusters"],
  ["канал", "каналов"],
  ["channel", "channels"],
  ["источник", "источников"],
  ["source", "sources"],
  ["сервис", "сервисов"],
  ["service", "services"],
  ["контейнер", "контейнеров"],
  ["container", "containers"],
  ["пользовател", "пользователей"],
  ["user", "users"],
  ["документ", "документов"],
  ["document", "documents"],
];

const KIND_KEYWORDS: ReadonlyArray<readonly [WowHeroNode["kind"], readonly string[]]> = [
  ["data", ["data", "источник", "парс", "ingest", "scrap", "crawl", "telegram", "rss"]],
  ["ml", ["ml", "ai", "модел", "embedding", "эмбед", "llm", "gpt", "bert", "ner", "semantic", "семант", "classif", "класс", "rerank", "vlm"]],
  ["storage", ["storage", "хран", "qdrant", "neo4j", "postgres", "redis", "vector", "граф", "graph", "kafka", "s3", "elastic", "clickhouse", "база"]],
  ["ui", ["ui", "dashboard", "дашборд", "frontend", "интерфейс", "виджет", "report", "отчёт", "отчет", "digest", "дайджест", "bot", "бот"]],
  ["service", ["service", "api", "backend", "сервис", "оркестр", "pipeline", "обработк", "очеред"]],
];

const STAGE_KEYWORDS: ReadonlyArray<readonly [string, string, readonly string[]]> = [
  ["sources", "Источники", ["telegram", "tgstat", "telethon", "twitter", "rss", "vk", "источник", "scraper", "crawler", "парс"]],
  ["processing", "Обработка", ["parser", "parsing", "парсинг", "очистк", "cleaning", "normaliz", "нормализ", "preprocess", "etl", "tokeniz"]],
  ["intelligence", "AI-анализ", ["embedding", "эмбеддинг", "bert", "e5", "llm", "gpt", "semantic", "семантик", "ner", "classif", "классифик", "vlm", "rerank"]],
  ["storage", "Хранилище", ["qdrant", "neo4j", "postgres", "redis", "elasticsearch", "clickhouse", "vector", "граф", "graph", "kafka", "s3"]],
  ["output", "Продукт", ["digest", "дайджест", "dashboard", "дашборд", "analytics", "аналитик", "отчёт", "report", "api", "bot", "бот"]],
];

const GENERIC_PIPELINE: ReadonlyArray<WowPipelineStage> = [
  { id: "sources", title: "Источники", tags: ["Data"] },
  { id: "processing", title: "Обработка", tags: ["Pipeline"] },
  { id: "intelligence", title: "AI-анализ", tags: ["ML"] },
  { id: "service", title: "Логика", tags: ["Service"] },
  { id: "output", title: "Продукт", tags: ["UI"] },
];

function nonEmpty(...candidates: Array<string | null | undefined>): string {
  for (const c of candidates) {
    if (c && c.trim()) return c.trim();
  }
  return "";
}

function clampText(text: string, max: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  return `${clean.slice(0, max - 1).trimEnd()}…`;
}

function blockMap(landing: GeneratedLanding): Map<string, { body: string; bullets: string[]; title: string }> {
  const map = new Map<string, { body: string; bullets: string[]; title: string }>();
  for (const b of landing.blocks ?? []) {
    map.set(b.key, { body: b.body ?? "", bullets: b.bullets ?? [], title: b.title ?? "" });
  }
  return map;
}

function collectText(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): string {
  const parts: string[] = [];
  if (contract?.title) parts.push(contract.title);
  for (const b of landing.blocks ?? []) {
    if (b.title) parts.push(b.title);
    if (b.body) parts.push(b.body);
    parts.push(...(b.bullets ?? []));
  }
  const fidelity = contract?.fidelity;
  if (fidelity) {
    for (const m of fidelity.modules ?? []) {
      parts.push(m.name, m.description);
    }
    for (const items of Object.values(fidelity.tech_stack_grouped ?? {})) {
      parts.push(...items);
    }
  }
  for (const s of semantic?.sections ?? []) {
    parts.push(...(s.metrics ?? []));
  }
  return parts.filter(Boolean).join("\n");
}

function numericWeight(value: string): number {
  const digits = value.replace(/[^\d.]/g, "");
  const n = Number.parseFloat(digits);
  return Number.isFinite(n) ? n : 0;
}

function normalizeValue(raw: string): string {
  return raw
    .replace(/\u00a0/g, " ")
    .replace(/\s+\+/g, "+")
    .replace(/\s+%/g, "%")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function extractedMetrics(text: string): WowHeroMetric[] {
  const found = new Map<string, WowHeroMetric>();
  for (const match of text.matchAll(NUM_RE)) {
    const unit = match[2];
    if (!unit) continue;
    const lowered = unit.toLowerCase();
    const hit = CONTEXT_UNITS.find(([stem]) => lowered.startsWith(stem));
    if (!hit) continue;
    const value = normalizeValue(match[1]);
    if (numericWeight(value) < 3 && !value.includes("%")) continue;
    const label = hit[1];
    const prev = found.get(label);
    if (!prev || numericWeight(value) > numericWeight(prev.value)) {
      found.set(label, { label, value, source: "extracted" });
    }
  }
  return [...found.values()].sort((a, b) => numericWeight(b.value) - numericWeight(a.value));
}

function derivedMetrics(
  landing: GeneratedLanding,
  contract: LandingContract | null,
): WowHeroMetric[] {
  const fidelity = contract?.fidelity;
  const blocks = blockMap(landing);
  const out: WowHeroMetric[] = [];

  const modules = fidelity?.modules?.length ?? 0;
  if (modules) out.push({ label: "Подсистем", value: String(modules), hint: "ключевых модулей", source: "derived" });

  const team = fidelity?.team_structured?.length ?? 0;
  if (team) out.push({ label: "Команда", value: String(team), hint: "участников", source: "derived" });

  const stack = Object.values(fidelity?.tech_stack_grouped ?? {}).reduce((n, v) => n + v.length, 0);
  if (stack) out.push({ label: "Технологий", value: String(stack), hint: "в стеке", source: "derived" });

  const tasks = blocks.get("tasks")?.bullets?.length ?? 0;
  if (tasks) out.push({ label: "Задач", value: String(tasks), hint: "в дорожной карте", source: "derived" });

  const results = blocks.get("results")?.bullets?.length ?? 0;
  if (results) out.push({ label: "Результатов", value: String(results), hint: "достигнуто", source: "derived" });

  return out;
}

function fallbackMetrics(
  landing: GeneratedLanding,
  contract: LandingContract | null,
): WowHeroMetric[] {
  const fidelity = contract?.fidelity;
  const blocks = blockMap(landing);
  return [
    { label: "Подсистем", value: String(fidelity?.modules?.length ?? 0), source: "fallback" },
    { label: "Команда", value: String(fidelity?.team_structured?.length ?? 0), source: "fallback" },
    {
      label: "Технологий",
      value: String(Object.values(fidelity?.tech_stack_grouped ?? {}).reduce((n, v) => n + v.length, 0)),
      source: "fallback",
    },
    { label: "Задач", value: String(blocks.get("tasks")?.bullets?.length ?? 0), source: "fallback" },
  ];
}

function buildMetrics(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): WowHeroMetric[] {
  const text = collectText(landing, contract, semantic);
  const metrics: WowHeroMetric[] = [];
  const seen = new Set<string>();
  const add = (items: WowHeroMetric[]) => {
    for (const m of items) {
      if (seen.has(m.label)) continue;
      seen.add(m.label);
      metrics.push(m);
    }
  };
  add(extractedMetrics(text));
  add(derivedMetrics(landing, contract));
  if (metrics.length < MIN_METRICS) add(fallbackMetrics(landing, contract));
  return metrics.slice(0, MAX_METRICS);
}

function classifyKind(text: string, fallback: WowHeroNode["kind"]): WowHeroNode["kind"] {
  const lowered = text.toLowerCase();
  for (const [kind, keywords] of KIND_KEYWORDS) {
    if (keywords.some((kw) => lowered.includes(kw))) return kind;
  }
  return fallback;
}

function buildNodes(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): WowHeroNode[] {
  const fidelity = contract?.fidelity;
  const nodes: WowHeroNode[] = [];
  const seen = new Set<string>();
  const push = (label: string, kind: WowHeroNode["kind"]) => {
    const clean = label.trim();
    if (!clean) return;
    const key = clean.toLowerCase();
    if (seen.has(key) || nodes.length >= MAX_NODES) return;
    seen.add(key);
    nodes.push({ id: `node-${nodes.length}`, label: clampText(clean, 28), kind });
  };

  for (const m of fidelity?.modules ?? []) {
    push(m.name, classifyKind(`${m.name} ${m.description} ${m.type ?? ""}`, "service"));
  }
  if (nodes.length < 3) {
    for (const node of semantic?.architecture?.nodes ?? []) {
      push(node.label, classifyKind(`${node.label} ${node.node_type ?? ""}`, "service"));
    }
  }
  if (nodes.length < 3 && fidelity?.tech_stack_grouped) {
    for (const [group, items] of Object.entries(fidelity.tech_stack_grouped)) {
      push(group, classifyKind(`${group} ${items.join(" ")}`, "service"));
    }
  }
  if (nodes.length === 0) {
    push("Источники данных", "data");
    push("AI-обработка", "ml");
    push("Хранилище", "storage");
    push("Продукт", "ui");
  }
  return nodes;
}

function buildPipeline(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): WowPipelineStage[] {
  const text = collectText(landing, contract, semantic).toLowerCase();
  const tokens: string[] = [];
  const fidelity = contract?.fidelity;
  if (fidelity) {
    for (const items of Object.values(fidelity.tech_stack_grouped ?? {})) tokens.push(...items);
    for (const m of fidelity.modules ?? []) tokens.push(m.name);
  }

  const stages: WowPipelineStage[] = [];
  let matched = 0;
  for (const [id, title, keywords] of STAGE_KEYWORDS) {
    const tags: string[] = [];
    for (const tok of tokens) {
      const low = tok.toLowerCase();
      if (keywords.some((kw) => low.includes(kw)) && tags.length < 3 && !tags.includes(tok)) {
        tags.push(tok);
      }
    }
    if (tags.length === 0) {
      const kw = keywords.find((k) => k.length >= 4 && text.includes(k));
      if (kw) tags.push(kw.charAt(0).toUpperCase() + kw.slice(1));
    }
    if (tags.length) matched += 1;
    stages.push({ id, title, tags: tags.length ? tags : [title] });
  }

  if (matched < 3) return [...GENERIC_PIPELINE];
  return stages;
}

function buildChips(
  landing: GeneratedLanding,
  contract: LandingContract | null,
): WowHeroChip[] {
  const chips: WowHeroChip[] = [];
  if (contract?.client) chips.push({ label: "Клиент", value: clampText(contract.client, 40) });
  const timeline = nonEmpty(contract?.timeline);
  if (timeline) chips.push({ label: "Период", value: clampText(timeline, 40) });
  if (contract?.lead) chips.push({ label: "Лид", value: clampText(contract.lead, 40) });
  void landing;
  return chips;
}

function buildSubtitle(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): string {
  const blocks = blockMap(landing);
  const candidate = nonEmpty(
    semantic?.narrative?.system,
    blocks.get("essence")?.body,
    contract?.quote,
    blocks.get("hero")?.body,
    landing.blocks?.[0]?.body,
  );
  return clampText(candidate || "Интеллектуальная система, собранная из проектных материалов.", 180);
}

/** Build the deterministic WOW hero scene description from project data. */
export function buildWowHeroData(
  landing: GeneratedLanding,
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
): WowHeroData {
  const blocks = blockMap(landing);
  const title = clampText(
    nonEmpty(
      contract?.title,
      blocks.get("hero")?.title,
      landing.blocks?.[0]?.title,
      "AI-проект",
    ),
    90,
  );

  return {
    title,
    subtitle: buildSubtitle(landing, contract, semantic),
    status: nonEmpty(contract?.status) || "ready",
    chips: buildChips(landing, contract),
    metrics: buildMetrics(landing, contract, semantic),
    nodes: buildNodes(landing, contract, semantic),
    pipeline: buildPipeline(landing, contract, semantic),
  };
}

/** Accent colors per node kind (hex), used by the 3D scene. */
export const NODE_KIND_COLOR: Record<WowHeroNode["kind"], string> = {
  data: "#38bdf8",
  ml: "#a855f7",
  service: "#6366f1",
  ui: "#22d3ee",
  storage: "#818cf8",
  core: "#c084fc",
};
