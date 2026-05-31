/**
 * VR/AR Showcase builder types and pure helpers (Stage P.5 MVP).
 *
 * Mirrors the backend `ShowcaseConfig` contract. URL validation here is a UX
 * convenience only; the backend re-validates and sanitizes everything.
 */

import { resolveApiBaseUrl } from "./api";

export type ShowcaseLayout = "gallery_arc" | "grid_hall" | "circle_booths";
export type ShowcaseMode = "web3d" | "vr_ready";
export type ShowcaseTheme = "university" | "tech" | "dark";

export interface ShowcaseProjectInput {
  id: string;
  title: string;
  description: string;
  landing_url?: string;
  demo_url?: string;
  demo_label?: string;
  category?: string;
  tags?: string[];
  accent?: string;
  source_project_id?: string;
}

export interface ShowcaseConfigInput {
  title: string;
  subtitle?: string;
  organization?: string;
  layout: ShowcaseLayout;
  mode: ShowcaseMode;
  theme: ShowcaseTheme;
  projects: ShowcaseProjectInput[];
}

export interface ShowcaseExportResult {
  html: string;
  project_count: number;
  mode: string;
  warnings: string[];
}

const DANGEROUS_SCHEME = /^\s*(?:javascript|data|vbscript|file|blob|about)\s*:/i;
const SAFE_ABSOLUTE = /^\s*https?:\/\//i;
const SCHEME_LIKE = /^\s*[a-zA-Z][a-zA-Z0-9+.\-]*:/;

/** Returns true if the URL is safe to attach (http(s) or relative path). */
export function isSafeShowcaseUrl(value: string | undefined | null): boolean {
  if (!value) return true; // empty is allowed (optional field)
  const candidate = value.trim();
  if (!candidate) return true;
  if (DANGEROUS_SCHEME.test(candidate)) return false;
  if (SAFE_ABSOLUTE.test(candidate)) return true;
  if (candidate.includes("://")) return false;
  if (SCHEME_LIKE.test(candidate)) return false;
  return true;
}

let idCounter = 0;

/** Create an empty draft project with a locally-unique id. */
export function createEmptyProject(): ShowcaseProjectInput {
  idCounter += 1;
  return {
    id: `item-${Date.now()}-${idCounter}`,
    title: "",
    description: "",
    demo_url: "",
    landing_url: "",
    category: "",
  };
}

export interface ShowcaseValidationResult {
  ok: boolean;
  errors: string[];
}

/** Validate a draft config before export. */
export function validateShowcaseConfig(
  config: ShowcaseConfigInput,
): ShowcaseValidationResult {
  const errors: string[] = [];
  if (!config.title.trim()) {
    errors.push("Укажите название витрины.");
  }
  if (config.projects.length === 0) {
    errors.push("Добавьте хотя бы один проект.");
  }
  config.projects.forEach((project, index) => {
    const label = project.title.trim() || `Проект ${index + 1}`;
    if (!project.title.trim()) {
      errors.push(`${label}: укажите название.`);
    }
    if (!isSafeShowcaseUrl(project.demo_url)) {
      errors.push(`${label}: небезопасный demo URL.`);
    }
    if (!isSafeShowcaseUrl(project.landing_url)) {
      errors.push(`${label}: небезопасный landing URL.`);
    }
  });
  return { ok: errors.length === 0, errors };
}

function trimmedOrUndefined(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

/** Build the request payload, stripping empty optional fields. */
export function toShowcasePayload(config: ShowcaseConfigInput): ShowcaseConfigInput {
  return {
    title: config.title.trim(),
    subtitle: trimmedOrUndefined(config.subtitle),
    organization: trimmedOrUndefined(config.organization),
    layout: config.layout,
    mode: config.mode,
    theme: config.theme,
    projects: config.projects.map((project) => ({
      id: project.id,
      title: project.title.trim(),
      description: project.description.trim(),
      demo_url: trimmedOrUndefined(project.demo_url),
      landing_url: trimmedOrUndefined(project.landing_url),
      demo_label: trimmedOrUndefined(project.demo_label),
      category: trimmedOrUndefined(project.category),
      tags: project.tags?.filter((t) => t.trim()),
      accent: trimmedOrUndefined(project.accent),
      source_project_id: project.source_project_id,
    })),
  };
}

/** Call the backend showcase HTML export endpoint. */
export async function exportShowcase(
  config: ShowcaseConfigInput,
): Promise<ShowcaseExportResult> {
  const base = resolveApiBaseUrl();
  const res = await fetch(`${base}/showcase/export-html`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toShowcasePayload(config)),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as ShowcaseExportResult;
}

export const SHOWCASE_ZIP_EXPORT_PATH = "/showcase/export-zip";
export const SHOWCASE_ZIP_DEFAULT_FILENAME = "ai-showcase.zip";

/** Suggested download filename for portable showcase ZIP bundles. */
export function showcaseZipFilename(): string {
  return SHOWCASE_ZIP_DEFAULT_FILENAME;
}

// ---------------------------------------------------------------------------
// Stage P.6 — Registry types and pure helpers
// ---------------------------------------------------------------------------

/** A persisted exhibit inside a saved showcase (mirrors backend ShowcaseProject). */
export interface ShowcaseProject {
  id: string;
  title: string;
  description: string;
  landing_url?: string | null;
  demo_url?: string | null;
  demo_label?: string | null;
  category?: string | null;
  tags: string[];
  accent?: string | null;
  source_project_id?: string | null;
  order_index: number;
}

/** A persisted showcase (mirrors backend ShowcaseConfig). */
export interface ShowcaseConfig {
  id: string;
  title: string;
  subtitle?: string | null;
  organization?: string | null;
  layout: ShowcaseLayout;
  mode: ShowcaseMode;
  theme: ShowcaseTheme;
  projects: ShowcaseProject[];
  created_at?: string | null;
  updated_at?: string | null;
}

/** Lightweight list-view entry. */
export interface ShowcaseSummary {
  id: string;
  title: string;
  project_count: number;
  updated_at?: string | null;
  created_at?: string | null;
}

export interface ShowcaseCreateRequest {
  title: string;
  subtitle?: string;
  organization?: string;
  layout?: ShowcaseLayout;
  mode?: ShowcaseMode;
  theme?: ShowcaseTheme;
}

export interface ShowcaseUpdateRequest {
  title?: string;
  subtitle?: string;
  organization?: string;
  layout?: ShowcaseLayout;
  mode?: ShowcaseMode;
  theme?: ShowcaseTheme;
}

export interface ShowcaseProjectRequest {
  title: string;
  description?: string;
  landing_url?: string;
  demo_url?: string;
  demo_label?: string;
  category?: string;
  tags?: string[];
  accent?: string;
  source_project_id?: string;
}

/** An existing landing project that can be attached to a showcase. */
export interface LandingCandidate {
  project_id: string;
  title: string;
  client?: string | null;
  description?: string | null;
  landing_url?: string | null;
  export_available: boolean;
  updated_at?: string | null;
}

/** Move a project up (-1) or down (+1) within the list (pure helper). */
export function moveProjectInList<T>(
  items: T[],
  index: number,
  direction: -1 | 1,
): T[] {
  const target = index + direction;
  if (index < 0 || index >= items.length) return items;
  if (target < 0 || target >= items.length) return items;
  const next = [...items];
  [next[index], next[target]] = [next[target], next[index]];
  return next;
}

/** Build an "add project" request prefilled from an existing landing candidate. */
export function candidateToProjectRequest(
  candidate: LandingCandidate,
): ShowcaseProjectRequest {
  return {
    title: candidate.title,
    description: candidate.description ?? "",
    landing_url: candidate.landing_url ?? undefined,
    source_project_id: candidate.project_id,
    category: candidate.client ?? undefined,
  };
}

/** Validate a manual "add project" form (UX convenience; backend re-validates). */
export function validateProjectRequest(
  request: ShowcaseProjectRequest,
): ShowcaseValidationResult {
  const errors: string[] = [];
  if (!request.title.trim()) {
    errors.push("Укажите название проекта.");
  }
  if (!isSafeShowcaseUrl(request.demo_url)) {
    errors.push("Небезопасная ссылка на демо.");
  }
  if (!isSafeShowcaseUrl(request.landing_url)) {
    errors.push("Небезопасная ссылка на ленд.");
  }
  return { ok: errors.length === 0, errors };
}

/** Call the backend showcase ZIP export endpoint. */
export async function exportShowcaseZip(
  config: ShowcaseConfigInput,
): Promise<{ blob: Blob; filename: string }> {
  const base = resolveApiBaseUrl();
  const res = await fetch(`${base}${SHOWCASE_ZIP_EXPORT_PATH}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(toShowcasePayload(config)),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1]?.endsWith(".zip")
    ? match[1]
    : showcaseZipFilename();
  return { blob, filename };
}
