"use client";

import type { ShowcaseProject } from "@/lib/showcase";

function demoStatusLabel(demoUrl: string | null | undefined): string {
  if (!demoUrl?.trim()) return "Demo-ссылка не добавлена";
  const lower = demoUrl.toLowerCase();
  if (lower.includes("aistudio.google.com")) {
    return "Демо: AI Google Studio";
  }
  return "Демо: внешняя ссылка";
}

function isExternalUrl(url: string): boolean {
  return /^https?:\/\//i.test(url.trim());
}

export function ShowcaseProjectCard({
  project,
  index,
  total,
  onEdit,
  onDelete,
  onMoveUp,
  onMoveDown,
  busy,
}: {
  project: ShowcaseProject;
  index: number;
  total: number;
  onEdit: () => void;
  onDelete: () => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  busy?: boolean;
}) {
  const hasDemo = Boolean(project.demo_url?.trim());
  const hasLanding = Boolean(project.landing_url?.trim());
  const demoExternal = hasDemo && isExternalUrl(project.demo_url!);

  return (
    <div className="space-y-3 rounded-lg border bg-card p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 space-y-1">
          <h3 className="font-semibold">{project.title}</h3>
          {project.category && (
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {project.category}
            </p>
          )}
          {project.tags && project.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {project.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
          {project.source_project_id && (
            <p className="text-xs text-muted-foreground">
              Источник: {project.source_project_id}
            </p>
          )}
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button
            type="button"
            aria-label="Выше"
            disabled={busy || index === 0}
            onClick={onMoveUp}
            className="rounded-md border px-2 py-1 text-sm disabled:opacity-30"
          >
            ↑
          </button>
          <button
            type="button"
            aria-label="Ниже"
            disabled={busy || index === total - 1}
            onClick={onMoveDown}
            className="rounded-md border px-2 py-1 text-sm disabled:opacity-30"
          >
            ↓
          </button>
        </div>
      </div>

      {project.description && (
        <p className="text-sm text-muted-foreground">{project.description}</p>
      )}

      <div className="grid gap-2 rounded-md bg-muted/40 p-3 text-sm">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-muted-foreground">
            {hasLanding
              ? `Ленд: ${project.landing_url}`
              : "Ленд: ссылка не указана"}
          </span>
          {hasLanding && (
            <a
              href={project.landing_url!}
              className="rounded-md border px-2 py-1 text-xs hover:bg-background"
            >
              Открыть ленд
            </a>
          )}
        </div>
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span
            className={
              hasDemo ? "text-muted-foreground" : "text-amber-700"
            }
          >
            {demoStatusLabel(project.demo_url)}
          </span>
          {hasDemo && (
            <a
              href={project.demo_url!}
              target={demoExternal ? "_blank" : undefined}
              rel={demoExternal ? "noopener noreferrer" : undefined}
              className="rounded-md border px-2 py-1 text-xs hover:bg-background"
            >
              Открыть демо ↗
            </a>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-3 text-sm">
        <button
          type="button"
          onClick={onEdit}
          disabled={busy}
          className="font-medium hover:underline disabled:opacity-50"
        >
          Редактировать
        </button>
        <button
          type="button"
          onClick={onDelete}
          disabled={busy}
          className="text-red-600 hover:underline disabled:opacity-50"
        >
          Удалить
        </button>
      </div>
    </div>
  );
}
