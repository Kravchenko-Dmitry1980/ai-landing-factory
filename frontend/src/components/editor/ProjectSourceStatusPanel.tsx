"use client";

import type { EvidenceVisibility, GeneratedLanding, LandingContract } from "@/lib/types";
import { formatCoverageStatus } from "@/lib/evidence-format";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  contract: LandingContract | null;
  evidence: EvidenceVisibility | null;
  landing: GeneratedLanding | null;
}

function teamCoverage(
  contract: LandingContract | null,
  evidence: EvidenceVisibility | null,
): string {
  const fromEvidence = evidence?.field_sources?.team?.coverage;
  if (fromEvidence) return fromEvidence;
  const count = contract?.fidelity?.team_structured?.length ?? 0;
  if (count > 0) return "strong";
  if (contract?.fidelity?.missing_fields?.includes("team")) return "missing";
  return "missing";
}

function landingHasTeam(landing: GeneratedLanding | null): boolean {
  if (!landing) return false;
  const block = landing.blocks.find((b) => b.key === "team");
  if (!block) return false;
  return Boolean(block.bullets?.length || block.body?.trim());
}

export function ProjectSourceStatusPanel({ contract, evidence, landing }: Props) {
  if (!contract && !evidence) return null;

  const sourceCount = evidence?.source_count ?? contract?.fidelity?.source_count ?? 0;
  const coverage = teamCoverage(contract, evidence);
  const teamCount = contract?.fidelity?.team_structured?.length ?? 0;
  const version = contract?.version ?? 1;
  const buildLabel = landing?.generated_at
    ? new Date(landing.generated_at).toLocaleString("ru-RU")
    : contract?.updated_at
      ? new Date(contract.updated_at).toLocaleString("ru-RU")
      : "—";

  const contractUpdated = contract?.updated_at ? new Date(contract.updated_at) : null;
  const landingGenerated = landing?.generated_at ? new Date(landing.generated_at) : null;
  const stale =
    Boolean(contractUpdated && landingGenerated && contractUpdated > landingGenerated) ||
    (teamCount > 0 && landing && !landingHasTeam(landing));

  return (
    <Card className="border-dashed">
      <CardHeader className="pb-2">
        <CardTitle className="text-base">Project source status</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <div className="flex flex-wrap gap-x-6 gap-y-1">
          <div>
            <span className="text-muted-foreground">Файлов загружено: </span>
            <span className="font-medium">{sourceCount}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Последняя сборка: </span>
            <span className="font-medium">
              v{version} · {buildLabel}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Команда: </span>
            <span
              className={
                coverage === "strong"
                  ? "font-medium text-emerald-700"
                  : coverage === "weak"
                    ? "font-medium text-amber-700"
                    : "font-medium text-slate-700"
              }
            >
              {formatCoverageStatus(coverage)}
              {teamCount > 0 ? ` (${teamCount})` : ""}
            </span>
          </div>
        </div>

        {sourceCount === 1 && (
          <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
            Загружен только один файл. Для полного ленда обычно нужен комплект: PPTX + DOCX/TXT.
          </p>
        )}

        {coverage === "missing" && (
          <p className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-slate-800">
            Для команды загрузите DOCX/TXT или PPTX со слайдом «Команда проекта».
          </p>
        )}

        {stale && (
          <p className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-red-900">
            Preview/export может быть устаревшим. Нажмите «Перепарсить» для обновления.
          </p>
        )}
      </CardContent>
    </Card>
  );
}
