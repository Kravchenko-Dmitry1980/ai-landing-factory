"use client";

import type { ShowcaseProject } from "@/lib/showcase";

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
  return (
    <div className="space-y-2 rounded-lg border p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-medium">{project.title}</h3>
          {project.category && (
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              {project.category}
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

      <div className="flex flex-wrap gap-3 text-xs">
        {project.demo_url && (
          <a
            href={project.demo_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Демо ↗
          </a>
        )}
        {project.landing_url && (
          <a
            href={project.landing_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Ленд ↗
          </a>
        )}
      </div>

      <div className="flex gap-3 pt-1 text-sm">
        <button
          type="button"
          onClick={onEdit}
          disabled={busy}
          className="text-muted-foreground hover:underline disabled:opacity-50"
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
