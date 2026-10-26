/**
 * Landing model: everything the v2 template shows, derived from the contract and the publishable team.
 * Pure functions, shared by the preview and the downloaded file through render.ts.
 */

import type { LandingBlock, LandingContract, LandingStyleProfile, TeamMember } from "@/lib/types";

export type LandingTheme = "night" | "light";

export interface Fact {
  label: string;
  value: string;
}

export interface Step {
  title: string;
  text: string;
}

export interface Metric {
  value: string;
  label: string;
  detail: string;
  /** Share of a full ring, 0–100, for percentages and known 0–1 quality metrics. */
  ring: number | null;
}

export interface BeforeAfter {
  label: string;
  before: number;
  after: number;
  beforeText: string;
  afterText: string;
  detail: string;
}

export interface Point {
  title: string;
  text: string;
}

export interface StackGroup {
  name: string;
  items: string[];
}

export interface Person {
  name: string;
  role: string;
  initials: string;
  contributions: string[];
  isLead: boolean;
}

export interface SectionTitles {
  results: string;
  about: string;
  purpose: string;
  inputs: string;
  outputs: string;
  work: string;
  stack: string;
  outlook: string;
}

export interface LandingModel {
  title: string;
  description: string;
  facts: Fact[];
  titles: SectionTitles;
  essence: string;
  essenceItems: string[];
  purposeIntro: string;
  purpose: Point[];
  inputs: string[];
  outputs: string[];
  workIntro: string;
  steps: Step[];
  metrics: Metric[];
  beforeAfter: BeforeAfter | null;
  resultsIntro: string;
  resultNotes: Point[];
  stack: StackGroup[];
  team: Person[];
  outlookIntro: string;
  outlook: Point[];
}

const MAX_METRICS = 6;
const LIGHT_PROFILES: string[] = ["minimal", "corporate"];

/** Titles the parser gives sections; when the editor kept them, the page uses its own shorter wording. */
const PARSER_TITLES: Record<string, string> = {
  essence: "Суть проекта",
  tasks: "Задачи проекта",
  purpose: "Для чего",
  inputs: "Вводные данные",
  outputs: "Выходные данные",
  results: "Результаты проекта",
  outlook: "Перспектива развития",
  tech_stack: "Используемый технологический стек",
};

const PAGE_TITLES: Record<string, string> = {
  essence: "О проекте",
  tasks: "Что сделали",
  purpose: "Зачем это нужно",
  inputs: "Что получает",
  outputs: "Что выдаёт",
  results: "Результаты",
  outlook: "Что дальше",
  tech_stack: "Технологии",
};

export function themeFromProfile(profile: string | null | undefined): LandingTheme {
  return profile && LIGHT_PROFILES.includes(profile) ? "light" : "night";
}

/** Theme of a project; older projects without style_config fall back to their legacy style fields. */
export function themeFromContract(contract: Pick<LandingContract, "style_config" | "presentation_style" | "style">): LandingTheme {
  return themeFromProfile(contract.style_config?.profile ?? contract.presentation_style ?? contract.style);
}

export function profileForTheme(theme: LandingTheme): LandingStyleProfile {
  return theme === "light" ? "minimal" : "tech";
}

/** Strips list markers and "1." / "2)" numbering; a minus right before a digit is a sign and stays. */
function clean(text: string): string {
  return text
    .replace(/^[\s•·*–—]+/, "")
    .replace(/^-+(?!\d)\s*/, "")
    .replace(/^\d{1,2}[.)]\s+/, "")
    .replace(/\s+/g, " ")
    .trim();
}

function lines(text: string): string[] {
  return text.split(/\r?\n/).map(clean).filter(Boolean);
}

/**
 * A block as the page shows it: the list items, plus the block text when it says something the
 * items do not (the parser often repeats the items in the text; the editor lets people write both).
 */
export function blockParts(block: LandingBlock | undefined): { text: string; items: string[] } {
  if (!block) return { text: "", items: [] };
  const bullets = block.bullets.map(clean).filter(Boolean);
  const textLines = lines(block.content);
  if (bullets.length === 0) return { text: "", items: textLines };
  const known = new Set(bullets.map((b) => b.toLowerCase()));
  const extra = textLines.filter((l) => !known.has(l.toLowerCase()));
  return { text: extra.join("\n"), items: bullets };
}

/** "Head: tail", else "Head — tail" → [head, tail]; no separator → ["", text]. A colon wins over a dash. */
export function splitHead(text: string): [string, string] {
  const colon = text.indexOf(":");
  if (colon > 0 && colon <= 80) return [text.slice(0, colon).trim(), text.slice(colon + 1).trim()];
  const dash = text.search(/\s[—–]\s/);
  if (dash > 0 && dash <= 80) return [text.slice(0, dash).trim(), text.slice(dash + 3).trim()];
  return ["", text];
}

function toNumber(raw: string): number {
  return Number(raw.replace(",", "."));
}

function ruNumber(raw: string): string {
  return raw.replace(".", ",");
}

type ParsedResult = { kind: "metric"; metric: Metric } | { kind: "change"; change: BeforeAfter };

const NUM = String.raw`\d+(?:[.,]\d+)?`;
const RANGE_TAIL = String.raw`(?:\s*[–-]\s*${NUM})?`;

/** 0–1 quality metrics that read naturally as a share of a ring. */
const SHARE_METRIC = new RegExp(
  String.raw`(?:^|[\s(,;])(m?ap\d*|accuracy|precision|recall|f1(?:-score)?|iou|auc|roc[- ]auc|точност\w*|полнот\w*)\s*[=:]\s*(0[.,]\d+)(\s*[–-]\s*0[.,]\d+)?`,
  "i",
);

/** "с 97% до менее 5%", "со 100% до 7%", "от 60% до более чем 90%", "97 % → 5 %". */
const CHANGE = new RegExp(
  String.raw`(?:(?:с|со|c|от)\s+)?(${NUM})\s*%\s*(?:до|→|->)\s*(?:(менее|ниже|меньше|более|свыше|выше|около|примерно|~)\s*(?:чем\s+)?)?(${NUM})${RANGE_TAIL}\s*%`,
  "i",
);

const PERCENT = new RegExp(String.raw`([+\-−]?)(${NUM})(\s*[–-]\s*${NUM})?\s*%`);

/** The text that is left once the figure itself is removed; "" when nothing but the figure was there. */
function detailWithout(tail: string, figure: string): string {
  const rest = tail.replace(figure, "").replace(/[\s.,;:=()]+/g, " ").trim();
  return /[a-zа-яё]{3,}/i.test(rest) ? tail : "";
}

/** Turns a result bullet with a real figure into a metric; null when the bullet has none. */
export function parseResult(bullet: string): ParsedResult | null {
  const [head, tail] = splitHead(bullet);
  if (!head || !tail) return null;

  const change = tail.match(CHANGE);
  if (change) {
    const qualifier = change[2] ? `${change[2].toLowerCase() === "~" ? "около" : change[2].toLowerCase()} ` : "";
    return {
      kind: "change",
      change: {
        label: head,
        before: toNumber(change[1]!),
        after: toNumber(change[3]!),
        beforeText: `${ruNumber(change[1]!)}%`,
        afterText: `${qualifier}${ruNumber(change[3]!)}%`,
        detail: tail,
      },
    };
  }
  // A change we could not read must not show its starting value as the result.
  if (/%[^%]*(?:\sдо\s|→|->)/i.test(tail)) return null;

  const percent = tail.match(PERCENT);
  if (percent) {
    const sign = percent[1] === "−" ? "-" : percent[1]!;
    const range = percent[3] ? percent[3].replace(/\s+/g, "").replace("-", "–") : "";
    const n = toNumber(percent[2]!);
    // Signed ("−40%") or relative ("на 40%") values and ranges are not shares of a whole.
    const relative = Boolean(sign) || Boolean(range) || /(?:^|\s)на\s*$/i.test(tail.slice(0, percent.index));
    return {
      kind: "metric",
      metric: {
        value: `${sign}${ruNumber(percent[2]!)}${ruNumber(range)}%`,
        label: head,
        detail: detailWithout(tail, percent[0]),
        ring: !relative && n <= 100 ? n : null,
      },
    };
  }

  const share = tail.match(SHARE_METRIC);
  if (share) {
    const range = share[3] ? share[3].replace(/\s+/g, "").replace("-", "–") : "";
    return {
      kind: "metric",
      metric: {
        value: `${ruNumber(share[2]!)}${ruNumber(range)}`,
        label: head,
        detail: detailWithout(tail, share[0]),
        ring: range ? null : toNumber(share[2]!) * 100,
      },
    };
  }

  // "×4" or "x4", but not a frame size like "1920 x 1080".
  const times = tail.match(new RegExp(String.raw`(?<!\d\s*)(?:^|[\s(])[×x]\s?(${NUM})(?=[\s),.;]|$)`));
  if (times) {
    return {
      kind: "metric",
      metric: { value: `×${ruNumber(times[1]!)}`, label: head, detail: detailWithout(tail, times[0]), ring: null },
    };
  }
  return null;
}

/** Splits "a, b (c, d), e" on top-level commas only; parentheses stay with their item. */
export function splitList(text: string): string[] {
  const items: string[] = [];
  let depth = 0;
  let current = "";
  for (const ch of text) {
    if (ch === "(") depth += 1;
    if (ch === ")") depth = Math.max(0, depth - 1);
    if (ch === "," && depth === 0) {
      items.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  items.push(current);
  return items.map((s) => s.replace(/[.;]$/, "").trim()).filter(Boolean);
}

function stackGroups(contract: LandingContract, block: LandingBlock | undefined): StackGroup[] {
  const grouped = contract.fidelity?.tech_stack_grouped ?? {};
  const fromFidelity = Object.entries(grouped)
    .map(([name, items]) => ({ name, items: items.map((i) => i.trim()).filter(Boolean) }))
    .filter((g) => g.items.length > 0);
  if (fromFidelity.length > 0) return fromFidelity;

  const groups: StackGroup[] = [];
  const loose: string[] = [];
  for (const item of blockParts(block).items) {
    const [head, tail] = splitHead(item);
    if (head && tail) groups.push({ name: head, items: splitList(tail) });
    else loose.push(...splitList(item));
  }
  if (loose.length > 0) groups.push({ name: "Технологии", items: loose });
  return groups.filter((g) => g.items.length > 0);
}

function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
}

function nameKey(s: string): string {
  return s
    .replace(/\s*\([^)]*\)/g, "")
    .toLowerCase()
    .replace(/ё/g, "е")
    .split(/\s+/)
    .filter(Boolean)
    .sort()
    .join(" ");
}

/** A sentence of achievements parsed into the role field, not a job title. */
function roleLooksLikeSentence(role: string): boolean {
  return role.length > 60 || (role.endsWith(".") && role.split(/\s+/).length > 4);
}

function people(members: TeamMember[], lead: string): Person[] {
  const leadKey = nameKey(lead);
  const list = members
    .filter((m) => m.name.trim())
    .map((m): Person => {
      let role = clean(m.role ?? "");
      let contributions = m.contributions.map(clean).filter(Boolean);
      if (roleLooksLikeSentence(role)) {
        contributions = [role, ...contributions];
        role = "";
      }
      return {
        name: m.name.trim(),
        role,
        initials: initials(m.name),
        contributions,
        isLead: Boolean(leadKey) && nameKey(m.name) === leadKey,
      };
    });
  return [...list.filter((p) => p.isLead), ...list.filter((p) => !p.isLead)];
}

/** "с 04 марта по 28 мая 2026 года" → "4 марта — 28 мая 2026". */
export function prettyTimeline(raw: string): string {
  const m = raw.trim().match(/^с\s+0?(\d{1,2})\s+(\S+)\s+по\s+0?(\d{1,2})\s+(\S+)\s+(\d{4})(?:\s+года?)?$/i);
  return m ? `${m[1]} ${m[2]} — ${m[3]} ${m[4]} ${m[5]}` : raw.trim();
}

function points(items: string[]): Point[] {
  return items.map((item) => {
    const [title, text] = splitHead(item);
    return title && text ? { title, text } : { title: "", text: item };
  });
}

/** A first item ending with ":" ("Создать систему, которая:") introduces the list, it is not an item. */
function introAndPoints(parts: { text: string; items: string[] }): { intro: string; points: Point[] } {
  const [first, ...rest] = parts.items;
  if (first?.endsWith(":") && rest.length > 0) {
    return { intro: [parts.text, first].filter(Boolean).join("\n"), points: points(rest) };
  }
  return { intro: parts.text, points: points(parts.items) };
}

function sectionTitle(blocks: Map<string, LandingBlock>, key: string): string {
  const own = blocks.get(key)?.title.trim() ?? "";
  return own && own !== PARSER_TITLES[key] ? own : PAGE_TITLES[key]!;
}

/**
 * Same words, ignoring case, punctuation and quotes: the parser often copies the title into the
 * description slot, and a page that says its title twice looks broken.
 */
export function sameText(a: string, b: string): boolean {
  const norm = (t: string) => t.toLowerCase().replace(/ё/g, "е").replace(/[^0-9a-zа-я]+/g, " ").trim();
  return norm(a) !== "" && norm(a) === norm(b);
}

/** The description under the title: the tagline or the quote, never a copy of the title. */
export function descriptionOf(title: string, tagline: string, quote: string): string {
  return [tagline, quote].map((t) => t.trim()).find((t) => t && !sameText(t, title)) ?? "";
}

function firstSentence(text: string, max = 220): string {
  const sentence = text.split(/(?<=[.!?])\s/)[0] ?? text;
  if (sentence.length <= max) return sentence;
  const cut = sentence.slice(0, max);
  return `${cut.slice(0, cut.lastIndexOf(" ")).replace(/[,;:]$/, "")}…`;
}

/**
 * @param publicTeam the team that passed the backend publication policy (GET /public-team);
 *   null when it could not be loaded — the page then shows no team rather than unchecked names.
 */
export function buildLandingModel(contract: LandingContract, publicTeam: TeamMember[] | null): LandingModel {
  const blocks = new Map(contract.blocks.map((b) => [b.key, b]));
  const title = (contract.title ?? "").trim() || "Проект";
  const tagline = blocks.get("tagline")?.content.trim() ?? "";
  const essence = (blocks.get("essence")?.content ?? "").trim();
  const essenceBullets = (blocks.get("essence")?.bullets ?? [])
    .map(clean)
    .filter((b) => b && !essence.includes(b));
  const opening = firstSentence(essence);
  const description = descriptionOf(title, tagline, contract.quote ?? "") || (sameText(opening, title) ? "" : opening);

  const facts: Fact[] = [
    { label: "Заказчик", value: (contract.client ?? "").trim() },
    { label: "Сроки", value: prettyTimeline(contract.timeline ?? "") },
    { label: "Руководитель", value: (contract.lead ?? "").trim() },
  ].filter((f) => f.value);

  const tasks = blockParts(blocks.get("tasks"));
  const steps = tasks.items.map((item): Step => {
    const [head, tail] = splitHead(item);
    if (head) return { title: head, text: tail };
    const words = item.split(" ");
    return { title: words.slice(0, 5).join(" "), text: words.slice(5).join(" ") };
  });

  const results = blockParts(blocks.get("results"));
  const metrics: Metric[] = [];
  const notes: string[] = [];
  let beforeAfter: BeforeAfter | null = null;
  for (const bullet of results.items) {
    const parsed = parseResult(bullet);
    if (parsed?.kind === "change" && !beforeAfter) beforeAfter = parsed.change;
    else if (parsed?.kind === "metric" && metrics.length < MAX_METRICS) metrics.push(parsed.metric);
    else notes.push(bullet);
  }

  const purpose = introAndPoints(blockParts(blocks.get("purpose")));
  const outlook = introAndPoints(blockParts(blocks.get("outlook")));
  const inputs = blockParts(blocks.get("inputs"));
  const outputs = blockParts(blocks.get("outputs"));

  return {
    title,
    description,
    facts,
    titles: {
      results: sectionTitle(blocks, "results"),
      about: sectionTitle(blocks, "essence"),
      purpose: sectionTitle(blocks, "purpose"),
      inputs: sectionTitle(blocks, "inputs"),
      outputs: sectionTitle(blocks, "outputs"),
      work: sectionTitle(blocks, "tasks"),
      stack: sectionTitle(blocks, "tech_stack"),
      outlook: sectionTitle(blocks, "outlook"),
    },
    essence: essence === description ? "" : essence,
    essenceItems: essenceBullets,
    purposeIntro: purpose.intro,
    purpose: purpose.points,
    inputs: [inputs.text, ...inputs.items].filter(Boolean),
    outputs: [outputs.text, ...outputs.items].filter(Boolean),
    workIntro: tasks.text,
    steps,
    metrics,
    beforeAfter,
    resultsIntro: results.text,
    resultNotes: points(notes),
    stack: stackGroups(contract, blocks.get("tech_stack")),
    team: people(publicTeam ?? [], contract.lead ?? ""),
    outlookIntro: outlook.intro,
    outlook: outlook.points,
  };
}
