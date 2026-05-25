import { normalizeBulletList } from "@/lib/normalizeBulletText";
import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
  LandingModule,
  TeamMember,
} from "@/lib/types";
import type { FidelityDataSource, FidelityDiagnostics } from "./types";

export interface ResolvedFidelityData {
  modules: LandingModule[];
  team: TeamMember[];
  stackGrouped: Record<string, string[]>;
  diagnostics: FidelityDiagnostics;
}

function parseBlockModule(item: string): LandingModule {
  const normalized = item.trim();
  const idx = normalized.indexOf(":");
  if (idx > 0 && idx < 60) {
    return {
      name: normalized.slice(0, idx).trim(),
      description: normalized.slice(idx + 1).trim(),
      type: "",
    };
  }
  return { name: normalized.slice(0, 80) || "Module", description: normalized, type: "" };
}

function extractSemanticModules(
  semantic: GeneratedSemanticLanding | null,
): LandingModule[] {
  if (!semantic) return [];
  const modSection = semantic.sections.find((s) => s.section_type === "modules");
  if (!modSection?.bullets.length) return [];
  return modSection.bullets.map(parseBlockModule);
}

function blockBullets(landing: GeneratedLanding, key: string): string[] {
  const block = landing.blocks.find((b) => b.key === key);
  if (!block) return [];
  const raw = block.bullets.length
    ? block.bullets
    : block.body
      ? block.body.split("\n").map((l) => l.trim()).filter(Boolean)
      : [];
  return normalizeBulletList(raw);
}

function parseBlockTeamMember(line: string): TeamMember {
  const parts = line.split(/[—–-]/);
  if (parts.length >= 2) {
    return {
      name: parts[0].trim(),
      role: parts.slice(1).join("-").trim(),
      project_area: "",
      contributions: [],
    };
  }
  return { name: line, role: "Contributor", project_area: "", contributions: [] };
}

export function resolveStructuredModules(
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
  landing: GeneratedLanding,
): { data: LandingModule[]; source: FidelityDataSource } {
  const fidelityModules = contract?.fidelity?.modules ?? [];
  if (fidelityModules.length > 0) {
    return { data: fidelityModules, source: "fidelity" };
  }

  const semanticModules = extractSemanticModules(semantic);
  if (semanticModules.length > 0) {
    return { data: semanticModules, source: "semantic" };
  }

  const taskBullets = blockBullets(landing, "tasks");
  if (taskBullets.length > 0) {
    return { data: taskBullets.map(parseBlockModule), source: "blocks" };
  }

  const moduleBullets = blockBullets(landing, "modules");
  if (moduleBullets.length > 0) {
    return { data: moduleBullets.map(parseBlockModule), source: "blocks" };
  }

  return { data: [], source: "fallback" };
}

export function resolveStructuredTeam(
  contract: LandingContract | null,
  landing: GeneratedLanding,
): { data: TeamMember[]; source: FidelityDataSource } {
  const structured = contract?.fidelity?.team_structured ?? [];
  if (structured.length > 0) {
    return { data: structured, source: "fidelity" };
  }

  const teamBullets = blockBullets(landing, "team");
  if (teamBullets.length > 0) {
    return { data: teamBullets.map(parseBlockTeamMember), source: "blocks" };
  }

  return { data: [], source: "fallback" };
}

export function resolveGroupedStack(
  contract: LandingContract | null,
  landing: GeneratedLanding,
): { data: Record<string, string[]>; source: FidelityDataSource } {
  const grouped = contract?.fidelity?.tech_stack_grouped ?? {};
  const categories = Object.keys(grouped).filter((k) => grouped[k]?.length);
  if (categories.length > 0) {
    return { data: grouped, source: "fidelity" };
  }

  const stackBullets = blockBullets(landing, "tech_stack");
  if (stackBullets.length > 0) {
    return { data: { Stack: stackBullets }, source: "blocks" };
  }

  return { data: {}, source: "fallback" };
}

export function buildFidelityData(
  contract: LandingContract | null,
  semantic: GeneratedSemanticLanding | null,
  landing: GeneratedLanding,
): ResolvedFidelityData {
  const modulesRes = resolveStructuredModules(contract, semantic, landing);
  const teamRes = resolveStructuredTeam(contract, landing);
  const stackRes = resolveGroupedStack(contract, landing);

  return {
    modules: modulesRes.data,
    team: teamRes.data,
    stackGrouped: stackRes.data,
    diagnostics: {
      modulesSource: modulesRes.source,
      teamSource: teamRes.source,
      stackSource: stackRes.source,
      modulesCount: modulesRes.data.length,
      teamCount: teamRes.data.length,
      stackCategoriesCount: Object.keys(stackRes.data).filter(
        (k) => stackRes.data[k]?.length,
      ).length,
    },
  };
}
