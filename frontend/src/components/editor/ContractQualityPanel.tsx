"use client";

import type { ContractCompletenessReport, FidelityMetadata } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface Props {
  fidelity: FidelityMetadata | null | undefined;
  completeness: ContractCompletenessReport | null;
  onReparse: () => void;
  reparsing: boolean;
}

export function ContractQualityPanel({
  fidelity,
  completeness,
  onReparse,
  reparsing,
}: Props) {
  const score = completeness?.score ?? fidelity?.completeness?.score ?? null;
  const parserMode = fidelity?.parser_mode ?? "unknown";
  const missing = completeness?.missing_fields ?? fidelity?.completeness?.missing_fields ?? [];
  const weak = completeness?.weak_fields ?? fidelity?.completeness?.weak_fields ?? [];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <CardTitle className="text-base">Качество контракта</CardTitle>
        <Button variant="outline" size="sm" onClick={onReparse} disabled={reparsing}>
          {reparsing ? "Перепарс…" : "Перепарсить как готовый ленд"}
        </Button>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        <div className="flex flex-wrap gap-4">
          {score !== null && (
            <div>
              <span className="text-muted-foreground">Completeness: </span>
              <span
                className={
                  score >= 70 ? "font-semibold text-emerald-700" : "font-semibold text-amber-700"
                }
              >
                {score}/100
              </span>
            </div>
          )}
          <div>
            <span className="text-muted-foreground">Parser mode: </span>
            <span className="font-medium">{parserMode}</span>
          </div>
        </div>

        {score !== null && score < 70 && (
          <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-amber-900">
            Ленд заполнен не полностью. Проверьте блоки:{" "}
            {missing.slice(0, 8).join(", ") || "—"}
          </p>
        )}

        {missing.length > 0 && score !== null && score >= 70 && (
          <p className="text-muted-foreground">
            Missing: {missing.join(", ")}
          </p>
        )}
        {weak.length > 0 && (
          <p className="text-muted-foreground">Weak: {weak.join(", ")}</p>
        )}
      </CardContent>
    </Card>
  );
}
