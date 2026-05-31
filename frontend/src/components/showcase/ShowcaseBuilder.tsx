"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  addShowcaseProject,
  deleteShowcaseProject,
  getShowcase,
  reorderShowcaseProjects,
  updateShowcase,
  updateShowcaseProject,
} from "@/lib/showcaseApi";
import {
  moveProjectInList,
  type ShowcaseConfig,
  type ShowcaseProject,
  type ShowcaseProjectRequest,
  type ShowcaseUpdateRequest,
} from "@/lib/showcase";
import { ShowcaseSettingsPanel } from "@/components/showcase/ShowcaseSettingsPanel";
import { ShowcaseProjectCard } from "@/components/showcase/ShowcaseProjectCard";
import { ShowcaseProjectForm } from "@/components/showcase/ShowcaseProjectForm";
import { LandingCandidatePicker } from "@/components/showcase/LandingCandidatePicker";
import { ShowcaseExportActions } from "@/components/showcase/ShowcaseExportActions";

function projectToRequest(project: ShowcaseProject): ShowcaseProjectRequest {
  return {
    title: project.title,
    description: project.description,
    demo_url: project.demo_url ?? "",
    landing_url: project.landing_url ?? "",
    demo_label: project.demo_label ?? undefined,
    category: project.category ?? "",
    tags: project.tags,
    accent: project.accent ?? undefined,
    source_project_id: project.source_project_id ?? undefined,
  };
}

export function ShowcaseBuilder({ showcaseId }: { showcaseId: string }) {
  const [config, setConfig] = useState<ShowcaseConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showPicker, setShowPicker] = useState(false);
  const [addFormInitial, setAddFormInitial] = useState<
    ShowcaseProjectRequest | undefined
  >();
  const [landingAutofillHint, setLandingAutofillHint] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const settingsTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let cancelled = false;
    getShowcase(showcaseId)
      .then((c) => {
        if (!cancelled) setConfig(c);
      })
      .catch((err) => {
        if (!cancelled)
          setError(err instanceof Error ? err.message : "Витрина не найдена.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [showcaseId]);

  function handleSettingsChange(patch: ShowcaseUpdateRequest) {
    setConfig((prev) => (prev ? { ...prev, ...patch } : prev));
    if (settingsTimer.current) clearTimeout(settingsTimer.current);
    settingsTimer.current = setTimeout(() => {
      updateShowcase(showcaseId, patch)
        .then((c) => setConfig(c))
        .catch((err) =>
          setError(err instanceof Error ? err.message : "Ошибка сохранения."),
        );
    }, 500);
  }

  async function withBusy(action: () => Promise<ShowcaseConfig>) {
    setBusy(true);
    setError(null);
    try {
      setConfig(await action());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка операции.");
    } finally {
      setBusy(false);
    }
  }

  async function handleAdd(request: ShowcaseProjectRequest) {
    await withBusy(() => addShowcaseProject(showcaseId, request));
    setShowAddForm(false);
    setShowPicker(false);
    setAddFormInitial(undefined);
    setLandingAutofillHint(false);
  }

  function handleCandidatePick(request: ShowcaseProjectRequest) {
    setShowPicker(false);
    setShowAddForm(true);
    setAddFormInitial(request);
    setLandingAutofillHint(Boolean(request.landing_url?.trim()));
  }

  function openManualAddForm() {
    setShowAddForm((v) => !v);
    setShowPicker(false);
    setAddFormInitial(undefined);
    setLandingAutofillHint(false);
  }

  async function handleEdit(projectId: string, request: ShowcaseProjectRequest) {
    await withBusy(() => updateShowcaseProject(showcaseId, projectId, request));
    setEditingId(null);
  }

  async function handleDelete(projectId: string) {
    await withBusy(() => deleteShowcaseProject(showcaseId, projectId));
  }

  async function handleMove(index: number, direction: -1 | 1) {
    if (!config) return;
    const reordered = moveProjectInList(config.projects, index, direction);
    if (reordered === config.projects) return;
    await withBusy(() =>
      reorderShowcaseProjects(
        showcaseId,
        reordered.map((p) => p.id),
      ),
    );
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">Загрузка витрины…</p>;
  }
  if (error && !config) {
    return <p className="text-sm text-red-600">{error}</p>;
  }
  if (!config) return null;

  return (
    <div className="space-y-6">
      <Link href="/showcase" className="text-sm text-muted-foreground hover:underline">
        ← Все витрины
      </Link>

      <ShowcaseSettingsPanel
        config={config}
        onChange={handleSettingsChange}
        disabled={busy}
      />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">Проекты витрины</h2>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={openManualAddForm}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
            >
              Добавить проект
            </button>
            <button
              type="button"
              onClick={() => {
                setShowPicker((v) => !v);
                setShowAddForm(false);
              }}
              className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
            >
              Добавить из лендов
            </button>
          </div>
        </div>

        {showAddForm && (
          <ShowcaseProjectForm
            key={
              addFormInitial?.source_project_id
                ? `candidate-${addFormInitial.source_project_id}`
                : "manual-add"
            }
            initial={addFormInitial}
            landingAutofillHint={landingAutofillHint}
            submitLabel="Добавить"
            onSubmit={handleAdd}
            onCancel={() => {
              setShowAddForm(false);
              setAddFormInitial(undefined);
              setLandingAutofillHint(false);
            }}
            busy={busy}
          />
        )}

        {showPicker && (
          <LandingCandidatePicker
            onPick={handleCandidatePick}
            onClose={() => setShowPicker(false)}
            busy={busy}
          />
        )}

        {config.projects.length === 0 ? (
          <p className="rounded-md border border-dashed p-6 text-center text-sm text-muted-foreground">
            Пока в витрине нет проектов. Добавьте проект вручную или выберите
            готовый ленд.
          </p>
        ) : (
          <div className="space-y-3">
            {config.projects.map((project, index) =>
              editingId === project.id ? (
                <ShowcaseProjectForm
                  key={project.id}
                  initial={projectToRequest(project)}
                  submitLabel="Сохранить"
                  onSubmit={(request) => handleEdit(project.id, request)}
                  onCancel={() => setEditingId(null)}
                  busy={busy}
                />
              ) : (
                <ShowcaseProjectCard
                  key={project.id}
                  project={project}
                  index={index}
                  total={config.projects.length}
                  onEdit={() => setEditingId(project.id)}
                  onDelete={() => handleDelete(project.id)}
                  onMoveUp={() => handleMove(index, -1)}
                  onMoveDown={() => handleMove(index, 1)}
                  busy={busy}
                />
              ),
            )}
          </div>
        )}
      </section>

      <section className="space-y-3 rounded-lg border p-4">
        <h2 className="text-lg font-semibold">Экспорт</h2>
        <ShowcaseExportActions showcaseId={showcaseId} />
      </section>

      {error && config && (
        <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
