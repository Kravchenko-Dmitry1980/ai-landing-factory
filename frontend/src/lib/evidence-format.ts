import type {
  EvidenceCoverage,
  EvidenceVisibility,
  FidelityMetadata,
  LandingContract,
} from "./types";

const FIELD_LABELS: Record<string, string> = {
  title: "Название",
  client: "Заказчик",
  timeline: "Сроки",
  lead: "Тимлид",
  essence: "Суть проекта",
  tasks: "Задачи",
  purpose: "Для чего",
  inputs: "Вводные данные",
  outputs: "Выходные данные",
  results: "Результаты",
  outlook: "Перспектива",
  tech_stack: "Технологический стек",
  team: "Команда",
  modules: "Модули",
  quote: "Фраза проекта",
};

const ROLE_LABELS: Record<string, string> = {
  primary_project_doc: "primary_project_doc",
  module_presentation: "module_presentation",
  supporting_presentation: "supporting_presentation",
  technical_spec: "technical_spec",
  report: "report",
  team_source: "team_source",
  unknown: "unknown",
};

const PARSER_LABELS: Record<string, string> = {
  multi_source_assembly: "multi_source_assembly",
  structured: "structured",
  project_presentation: "project_presentation",
  heuristic: "heuristic",
};

const COVERAGE_LABELS: Record<EvidenceCoverage, string> = {
  strong: "strong",
  weak: "weak",
  missing: "missing",
};

export function formatFieldName(field: string): string {
  return FIELD_LABELS[field] ?? field;
}

export function formatCoverageStatus(status: EvidenceCoverage | string): string {
  if (status in COVERAGE_LABELS) {
    return COVERAGE_LABELS[status as EvidenceCoverage];
  }
  return status;
}

export function formatSourceRole(role: string): string {
  return ROLE_LABELS[role] ?? role;
}

export function formatParserMode(mode: string): string {
  return PARSER_LABELS[mode] ?? mode;
}

export function coverageBadgeClass(status: EvidenceCoverage | string): string {
  switch (status) {
    case "strong":
      return "bg-emerald-100 text-emerald-900 border-emerald-300";
    case "weak":
      return "bg-amber-100 text-amber-900 border-amber-300";
    default:
      return "bg-slate-100 text-slate-700 border-slate-300";
  }
}

export function sourceStatusBadgeClass(status: string): string {
  switch (status) {
    case "used":
      return "bg-emerald-100 text-emerald-900";
    case "weak":
      return "bg-amber-100 text-amber-900";
    case "ignored":
      return "bg-slate-100 text-slate-700";
    default:
      return "bg-red-50 text-red-800";
  }
}

export function parseSourceRef(ref: string): { filename: string; location: string } {
  const hash = ref.indexOf("#");
  if (hash === -1) {
    return { filename: ref, location: "" };
  }
  const filename = ref.slice(0, hash);
  const loc = ref.slice(hash + 1);
  const [locType, locIndex] = loc.split(":");
  let location = locType;
  if (locIndex) {
    if (locType === "slide") location = `slide ${locIndex}`;
    else if (locType === "page") location = `page ${locIndex}`;
    else if (locType === "section") location = `section ${locIndex}`;
    else location = `${locType} ${locIndex}`;
  }
  return { filename, location };
}

export function extractEvidenceVisibility(
  contract: LandingContract | null | undefined,
): EvidenceVisibility | null {
  if (!contract?.fidelity) return null;
  const fidelity = contract.fidelity;
  const report = fidelity.evidence_report;
  if (!report && !fidelity.field_sources?.length && !fidelity.source_count) {
    return null;
  }
  return {
    project_id: contract.project_id,
    parser_mode: fidelity.parser_mode,
    source_count: fidelity.source_count ?? report?.sources.length ?? 0,
    evidence_count: fidelity.evidence_count ?? report?.total_evidence_items ?? 0,
    assembly_confidence: fidelity.assembly_confidence ?? report?.confidence ?? 0,
    sources: [],
    field_sources: {},
    missing_fields: fidelity.missing_fields ?? report?.missing_fields ?? [],
    weak_fields: fidelity.weak_fields ?? report?.weak_fields ?? [],
    strong_fields: report?.strong_fields ?? [],
    warnings: report?.warnings ?? [],
    improvement_hints: [],
  };
}

export function hasEvidenceData(
  evidence: EvidenceVisibility | null | undefined,
  fidelity: FidelityMetadata | null | undefined,
): boolean {
  if (evidence && (evidence.sources.length > 0 || evidence.source_count > 0)) {
    return true;
  }
  if (fidelity?.evidence_report) return true;
  if ((fidelity?.source_count ?? 0) > 0) return true;
  if ((fidelity?.evidence_count ?? 0) > 0) return true;
  return false;
}
