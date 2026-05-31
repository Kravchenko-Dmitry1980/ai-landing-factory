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

/** Call the backend showcase export endpoint. */
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
