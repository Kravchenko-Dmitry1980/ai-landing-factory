import type {
  ArchitectureResponse,
  DomainIntelligenceReport,
  EnrichmentResponse,
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
  LandingStyleConfig,
  PIIReportPublic,
  PiiCleanupResponse,
  PrivacyStatusResponse,
  ProjectResponse,
  ProjectKnowledgeGraph,
  SafeCloudPayloadPreview,
  SemanticDebugResponse,
  SemanticGenerationResponse,
  SourceStructureReport,
  ContractCompletenessReport,
  EvidenceVisibility,
  TeamReviewData,
  TeamReviewActionResult,
  UnifiedGenerateResponse,
  UploadResponse,
} from "./types";
import { formatApiError } from "./api-errors";

/** Base URL including /api/v1 — paths are relative, e.g. /projects/privacy */
export function resolveApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL?.trim();
  if (raw) {
    return raw.replace(/\/$/, "");
  }
  return "http://127.0.0.1:8001/api/v1";
}

const API_BASE_URL = resolveApiBaseUrl();

export { formatApiError };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  const url = `${API_BASE_URL}${normalizedPath}`;
  const method = init?.method ?? "GET";

  if (process.env.NODE_ENV === "development") {
    console.info("[API]", method, url);
  }

  let res: Response;
  try {
    res = await fetch(url, init);
  } catch {
    throw new Error(formatApiError(new Error("Failed to fetch")));
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(formatApiError(new Error(text || `HTTP ${res.status}`)));
  }

  return res.json() as Promise<T>;
}

export async function createProject(
  name: string,
  description?: string,
): Promise<ProjectResponse> {
  return request<ProjectResponse>("/projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, description: description ?? null }),
  });
}

export async function uploadMaterials(
  projectId: string,
  files: File[],
  description?: string,
): Promise<UploadResponse> {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  if (description) form.append("description", description);
  return request<UploadResponse>(`/projects/${projectId}/upload`, {
    method: "POST",
    body: form,
  });
}

export async function getContract(projectId: string): Promise<LandingContract> {
  return request<LandingContract>(`/projects/${projectId}/contract`);
}

export async function patchStyleConfig(
  projectId: string,
  styleConfig: LandingStyleConfig,
): Promise<{ project_id: string; style_config: LandingStyleConfig }> {
  return request<{ project_id: string; style_config: LandingStyleConfig }>(
    `/projects/${projectId}/style-config`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        profile: styleConfig.profile,
        custom_style_prompt: styleConfig.custom_style_prompt ?? null,
        theme_tokens: styleConfig.theme_tokens ?? null,
      }),
    },
  );
}

export async function updateContract(
  projectId: string,
  payload: Partial<
    Pick<
      LandingContract,
      "style" | "blocks" | "client" | "goals" | "presentation_style" | "style_config"
    >
  >,
): Promise<LandingContract> {
  return request<LandingContract>(`/projects/${projectId}/contract`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function getLanding(projectId: string): Promise<GeneratedLanding> {
  return request<GeneratedLanding>(`/projects/${projectId}/landing`);
}

export async function enrichContract(projectId: string): Promise<EnrichmentResponse> {
  return request<EnrichmentResponse>(`/projects/${projectId}/contract/enrich`, {
    method: "POST",
  });
}

export async function semanticGenerate(
  projectId: string,
): Promise<SemanticGenerationResponse> {
  return request<SemanticGenerationResponse>(
    `/projects/${projectId}/semantic-generate`,
    { method: "POST" },
  );
}

export async function getSemanticLanding(
  projectId: string,
): Promise<GeneratedSemanticLanding> {
  return request<GeneratedSemanticLanding>(`/projects/${projectId}/semantic-landing`);
}

export async function getArchitecture(
  projectId: string,
): Promise<ArchitectureResponse> {
  return request<ArchitectureResponse>(`/projects/${projectId}/architecture`);
}

export async function getSemanticDebug(
  projectId: string,
): Promise<SemanticDebugResponse> {
  return request<SemanticDebugResponse>(`/projects/${projectId}/semantic-debug`);
}

export async function analyzeDomain(projectId: string): Promise<DomainIntelligenceReport> {
  return request<DomainIntelligenceReport>(`/projects/${projectId}/domain-analyze`, {
    method: "POST",
  });
}

export async function getDomainReport(projectId: string): Promise<DomainIntelligenceReport> {
  return request<DomainIntelligenceReport>(`/projects/${projectId}/domain-report`);
}

export async function getKnowledgeGraph(projectId: string): Promise<ProjectKnowledgeGraph> {
  return request<ProjectKnowledgeGraph>(`/projects/${projectId}/knowledge-graph`);
}

export async function generateLanding(
  projectId: string,
  options?: { enrich?: boolean; mode?: "full" | "stub" },
): Promise<UnifiedGenerateResponse> {
  return request<UnifiedGenerateResponse>(`/projects/${projectId}/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      enrich: options?.enrich ?? false,
      mode: options?.mode ?? "full",
    }),
  });
}

/** @deprecated Use generateLanding — kept for save/stub regen */
export async function regenerateLanding(
  projectId: string,
): Promise<GeneratedLanding> {
  const result = await generateLanding(projectId, { mode: "stub" });
  return result.landing;
}

export async function getPrivacyConfig(): Promise<PrivacyStatusResponse> {
  return request<PrivacyStatusResponse>("/projects/privacy");
}

export async function getPrivacyStatus(): Promise<PrivacyStatusResponse> {
  return getPrivacyConfig();
}

export async function getPiiReport(projectId: string): Promise<PIIReportPublic> {
  return request<PIIReportPublic>(`/projects/${projectId}/pii-report`);
}

export async function runPiiPrescan(projectId: string): Promise<PIIReportPublic> {
  return request<PIIReportPublic>(`/projects/${projectId}/pii-prescan`, {
    method: "POST",
  });
}

export async function getSafeCloudPayload(
  projectId: string,
): Promise<SafeCloudPayloadPreview> {
  return request<SafeCloudPayloadPreview>(
    `/projects/${projectId}/safe-cloud-payload`,
  );
}

export async function runPiiCleanup(): Promise<PiiCleanupResponse> {
  return request<PiiCleanupResponse>("/projects/privacy/cleanup", {
    method: "POST",
  });
}

export type LandingExportMode = "standard" | "wow";
export type Wow3dRuntime = "none" | "aframe";

export async function exportHtml(
  projectId: string,
  options?: {
    theme?: string;
    styleConfig?: LandingStyleConfig;
    mode?: LandingExportMode;
    wow3dRuntime?: Wow3dRuntime;
  },
): Promise<string> {
  const params = new URLSearchParams();
  const theme = options?.theme ?? "university_platform";
  if (theme) params.set("theme", theme);
  if (options?.styleConfig) {
    params.set("style_config", JSON.stringify(options.styleConfig));
  }
  if (options?.mode && options.mode !== "standard") {
    params.set("mode", options.mode);
  }
  if (options?.mode === "wow" && options.wow3dRuntime) {
    params.set("wow_3d_runtime", options.wow3dRuntime);
  }
  const qs = params.toString();
  const data = await request<{ html: string }>(
    `/projects/${projectId}/export/html${qs ? `?${qs}` : ""}`,
  );
  return data.html;
}

export const WOW_BUNDLE_ZIP_FILENAME = "ai-wow-landing.zip";

/**
 * Export the Interactive WOW Bundle as a portable ZIP (Stage P.7.2).
 *
 * Returns the raw blob + suggested filename. The ZIP ships a standalone React/R3F
 * app that opens offline (no backend, no CDN). Separate from the HTML exports.
 */
export async function exportWowBundleZip(
  projectId: string,
  options?: { demoUrl?: string; showcaseUrl?: string },
): Promise<{ blob: Blob; filename: string }> {
  const params = new URLSearchParams();
  if (options?.demoUrl) params.set("demo_url", options.demoUrl);
  if (options?.showcaseUrl) params.set("showcase_url", options.showcaseUrl);
  const qs = params.toString();
  const url = `${API_BASE_URL}/projects/${projectId}/export/wow-bundle${qs ? `?${qs}` : ""}`;

  let res: Response;
  try {
    res = await fetch(url);
  } catch {
    throw new Error(formatApiError(new Error("Failed to fetch")));
  }
  if (!res.ok) {
    const text = await res.text();
    throw new Error(formatApiError(new Error(text || `HTTP ${res.status}`)));
  }
  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") ?? "";
  const match = disposition.match(/filename="?([^";]+)"?/i);
  const filename = match?.[1]?.endsWith(".zip") ? match[1] : WOW_BUNDLE_ZIP_FILENAME;
  return { blob, filename };
}

export async function getContractCompleteness(
  projectId: string,
): Promise<ContractCompletenessReport> {
  return request<ContractCompletenessReport>(
    `/projects/${projectId}/contract-completeness`,
  );
}

export async function getSourceStructure(
  projectId: string,
): Promise<SourceStructureReport> {
  return request<SourceStructureReport>(
    `/projects/${projectId}/source-structure`,
  );
}

export async function getEvidenceReport(
  projectId: string,
): Promise<EvidenceVisibility> {
  return request<EvidenceVisibility>(`/projects/${projectId}/evidence-report`);
}

export async function getTeamReview(projectId: string): Promise<TeamReviewData> {
  return request<TeamReviewData>(`/projects/${projectId}/team-review`);
}

export async function teamReviewBulkAction(
  projectId: string,
  action: "accept_all" | "keep_verified_only" | "reset_to_auto",
): Promise<TeamReviewActionResult> {
  return request<TeamReviewActionResult>(
    `/projects/${projectId}/team-review/bulk-action`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    },
  );
}

export async function teamReviewManualText(
  projectId: string,
  text: string,
): Promise<TeamReviewActionResult> {
  return request<TeamReviewActionResult>(
    `/projects/${projectId}/team-review/manual-text`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    },
  );
}

export async function reparseStructuredLanding(
  projectId: string,
): Promise<LandingContract> {
  return request<LandingContract>(
    `/projects/${projectId}/reparse-structured-landing`,
    { method: "POST" },
  );
}
