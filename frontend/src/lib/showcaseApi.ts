/**
 * Showcase Registry API client (Stage P.6).
 *
 * Thin fetch wrappers over the backend `/showcases` CRUD endpoints plus the
 * `/showcase/landing-candidates` helper. All payloads are re-validated and
 * sanitized server-side.
 */

import { resolveApiBaseUrl } from "./api";
import type {
  LandingCandidate,
  ShowcaseConfig,
  ShowcaseCreateRequest,
  ShowcaseProjectRequest,
  ShowcaseSummary,
  ShowcaseUpdateRequest,
} from "./showcase";

function base(): string {
  return resolveApiBaseUrl();
}

async function jsonRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base()}${path}`, init);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return (await res.json()) as T;
}

const JSON_HEADERS = { "Content-Type": "application/json" };

export async function listShowcases(): Promise<ShowcaseSummary[]> {
  return jsonRequest<ShowcaseSummary[]>("/showcases");
}

export async function createShowcase(
  body: ShowcaseCreateRequest,
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>("/showcases", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

export async function getShowcase(id: string): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}`);
}

export async function updateShowcase(
  id: string,
  body: ShowcaseUpdateRequest,
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

export async function deleteShowcase(id: string): Promise<{ deleted: boolean }> {
  return jsonRequest<{ deleted: boolean }>(`/showcases/${id}`, {
    method: "DELETE",
  });
}

export async function addShowcaseProject(
  id: string,
  body: ShowcaseProjectRequest,
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}/projects`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

export async function updateShowcaseProject(
  id: string,
  projectId: string,
  body: ShowcaseProjectRequest,
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}/projects/${projectId}`, {
    method: "PATCH",
    headers: JSON_HEADERS,
    body: JSON.stringify(body),
  });
}

export async function deleteShowcaseProject(
  id: string,
  projectId: string,
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}/projects/${projectId}`, {
    method: "DELETE",
  });
}

export async function reorderShowcaseProjects(
  id: string,
  orderedIds: string[],
): Promise<ShowcaseConfig> {
  return jsonRequest<ShowcaseConfig>(`/showcases/${id}/projects/reorder`, {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ ordered_ids: orderedIds }),
  });
}

export interface ShowcaseHtmlExportResult {
  html: string;
  project_count: number;
  mode: string;
  warnings: string[];
}

export async function exportShowcaseHtml(
  id: string,
): Promise<ShowcaseHtmlExportResult> {
  return jsonRequest<ShowcaseHtmlExportResult>(`/showcases/${id}/export-html`, {
    method: "POST",
  });
}

export const SHOWCASE_ZIP_FILENAME = "ai-showcase.zip";

export async function exportShowcaseZip(
  id: string,
): Promise<{ blob: Blob; filename: string }> {
  const res = await fetch(`${base()}/showcases/${id}/export-zip`, {
    method: "POST",
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1]?.endsWith(".zip") ? match[1] : SHOWCASE_ZIP_FILENAME;
  return { blob, filename };
}

export async function listLandingCandidates(): Promise<LandingCandidate[]> {
  return jsonRequest<LandingCandidate[]>("/showcase/landing-candidates");
}
