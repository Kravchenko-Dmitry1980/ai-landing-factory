"use client";

interface Props {
  hints: string[];
  warnings: string[];
  parserMode: string;
}

export function EvidenceHints({ hints, warnings, parserMode }: Props) {
  const showHeuristicWarning =
    parserMode === "heuristic" &&
    !warnings.some((w) => w.includes("fallback-эвристику"));

  if (hints.length === 0 && warnings.length === 0 && !showHeuristicWarning) {
    return null;
  }

  return (
    <div className="space-y-2">
      {showHeuristicWarning && (
        <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          Система использовала fallback-эвристику. Добавьте больше структурированных
          материалов или нажмите reparse после загрузки дополнительных файлов.
        </p>
      )}

      {warnings.map((warning) => (
        <p
          key={warning}
          className="rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800"
        >
          {warning}
        </p>
      ))}

      {hints.length > 0 && (
        <div>
          <p className="mb-1 text-sm font-medium">Что улучшить</p>
          <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
            {hints.map((hint) => (
              <li key={hint}>{hint}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
