"use client";

import { useEffect, useState } from "react";
import { listLandingCandidates } from "@/lib/showcaseApi";
import {
  candidateToProjectRequest,
  type LandingCandidate,
  type ShowcaseProjectRequest,
} from "@/lib/showcase";

export function LandingCandidatePicker({
  onPick,
  onClose,
  busy,
}: {
  onPick: (request: ShowcaseProjectRequest) => void;
  onClose: () => void;
  busy?: boolean;
}) {
  const [candidates, setCandidates] = useState<LandingCandidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listLandingCandidates()
      .then((items) => {
        if (!cancelled) setCandidates(items);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Ошибка загрузки лендов.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-3 rounded-lg border border-dashed p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold">Добавить из лендов</h3>
        <button
          type="button"
          onClick={onClose}
          className="text-sm text-muted-foreground hover:underline"
        >
          Закрыть
        </button>
      </div>

      {loading && <p className="text-sm text-muted-foreground">Загрузка…</p>}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {!loading && !error && candidates.length === 0 && (
        <p className="text-sm text-muted-foreground">
          Готовых лендов пока нет.
        </p>
      )}

      <ul className="space-y-2">
        {candidates.map((candidate) => (
          <li
            key={candidate.project_id}
            className="flex items-center justify-between gap-3 rounded-md border p-2"
          >
            <div className="min-w-0">
              <p className="truncate text-sm font-medium">{candidate.title}</p>
              {candidate.client && (
                <p className="truncate text-xs text-muted-foreground">
                  {candidate.client}
                </p>
              )}
            </div>
            <button
              type="button"
              disabled={busy}
              onClick={() => onPick(candidateToProjectRequest(candidate))}
              className="shrink-0 rounded-md border px-3 py-1 text-sm hover:bg-muted disabled:opacity-50"
            >
              Добавить
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}
