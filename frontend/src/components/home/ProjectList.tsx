"use client";

import Link from "next/link";
import { useCallback, useEffect, useId, useMemo, useState } from "react";
import { listProjects } from "@/lib/api";
import { PUBLICATION_STATE_LABELS, publicationState } from "@/lib/platform";
import { formatEditedAt, staffErrorMessage } from "@/lib/staff";
import type { ProjectSummary } from "@/lib/types";

const PAGE = 12;
/** The backend caps the list at 200; we ask for all of it and say so when the cap is reached. */
const LIST_LIMIT = 200;

/** "Ваши лендинги": every project, newest first, with a name search. */
export function ProjectList() {
  const searchId = useId();
  const [projects, setProjects] = useState<ProjectSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [shown, setShown] = useState(PAGE);

  const load = useCallback(async () => {
    setError(null);
    try {
      setProjects(await listProjects(LIST_LIMIT));
    } catch (err) {
      console.error("Project list failed to load", err);
      setError(staffErrorMessage(err, "Не удалось загрузить список лендингов"));
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return (projects ?? []).filter((p) => !q || p.name.toLowerCase().includes(q));
  }, [projects, query]);

  return (
    <section aria-labelledby={`${searchId}-title`} className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <h2 id={`${searchId}-title`} className="font-display text-[30px] font-semibold">
          Ваши лендинги
          {projects && projects.length > 0 && (
            <span className="ml-3 align-middle text-base font-normal text-fur">{projects.length}</span>
          )}
        </h2>
        {projects && projects.length > 0 && (
          <div className="flex flex-col gap-1.5">
            <label htmlFor={searchId} className="text-sm text-fur">
              Найти по названию
            </label>
            <input
              id={searchId}
              type="search"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setShown(PAGE);
              }}
              placeholder="контроль кассы"
              className="h-10 w-[260px] max-w-full rounded-[10px] border border-field bg-white px-3 text-[15px]"
            />
          </div>
        )}
      </div>

      {error && (
        <div role="alert" className="flex flex-wrap items-center gap-3 rounded-xl border border-line bg-white px-5 py-4 text-[15px]">
          <span>{error}</span>
          <button type="button" onClick={() => void load()} className="rounded-lg border border-field px-3 py-1.5 hover:bg-paper">
            Повторить
          </button>
        </div>
      )}

      {!error && projects === null && <p className="text-fur">Загружаю список…</p>}

      {projects && projects.length === 0 && (
        <p className="max-w-[560px] text-[17px] leading-relaxed text-fur">
          Здесь появятся ваши лендинги. Загрузите материалы проекта выше, и первая страница будет готова через несколько
          секунд.
        </p>
      )}

      {projects && projects.length >= LIST_LIMIT && (
        <p className="text-[15px] text-fur">
          Показаны последние {LIST_LIMIT} лендингов. Более старые в этот список и в поиск не попадают.
        </p>
      )}

      {projects && projects.length > 0 && filtered.length === 0 && (
        <p className="text-[17px] text-fur">Лендингов с названием «{query.trim()}» нет. Проверьте написание.</p>
      )}

      {filtered.length > 0 && (
        <ul className="grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-6">
          {filtered.slice(0, shown).map((p) => (
            <li key={p.id}>
              <ProjectCard project={p} />
            </li>
          ))}
        </ul>
      )}

      {filtered.length > shown && (
        <div>
          <button
            type="button"
            onClick={() => setShown((n) => n + PAGE)}
            className="h-11 rounded-[10px] border border-field bg-white px-5 text-[15px] hover:bg-paper"
          >
            Показать ещё {Math.min(PAGE, filtered.length - shown)}
          </button>
        </div>
      )}
    </section>
  );
}

const STATE_STYLES = {
  published: "bg-[#E7F4EC] text-ok",
  outdated: "bg-marker text-ink",
  withdrawn: "bg-grid-soft text-fur",
} as const;

function ProjectCard({ project }: { project: ProjectSummary }) {
  const state = publicationState(project.publication_status, project.published_contract_version, project.version);
  return (
    <Link href={`/editor/${project.id}`} className="group flex flex-col gap-3 text-ink no-underline">
      <div
        aria-hidden="true"
        className="flex h-[170px] gap-3.5 overflow-hidden rounded-[14px] border border-line bg-white bg-grid-paper bg-cell-sm p-[18px] transition-colors group-hover:border-scheme-line"
      >
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <span className="line-clamp-4 font-display text-[15px] font-semibold leading-tight">{project.name}</span>
          <span className="h-[5px] w-4/5 rounded bg-grid" />
          <span className="h-[5px] w-3/5 rounded bg-grid" />
        </div>
        <div className="flex w-10 flex-col items-center gap-1.5 pt-0.5">
          <span className="h-3 w-3 rounded-full border-2 border-scheme bg-white" />
          <span className="h-[18px] w-0.5 bg-scheme" />
          <span className="h-3 w-3 rounded-full border-2 border-scheme bg-white" />
          <span className="h-[18px] w-0.5 bg-scheme" />
          <span className="h-3 w-3 rounded-full border-2 border-scheme bg-glow" />
        </div>
      </div>
      <div className="flex flex-col gap-1">
        <span className="line-clamp-2 text-base font-semibold leading-snug group-hover:text-scheme">{project.name}</span>
        <span className="text-sm text-fur">{formatEditedAt(project.updated_at)}</span>
        {state !== "none" && (
          <span className={`w-fit rounded-md px-2 py-0.5 text-[13px] font-semibold ${STATE_STYLES[state]}`}>
            {PUBLICATION_STATE_LABELS[state]}
          </span>
        )}
      </div>
    </Link>
  );
}
