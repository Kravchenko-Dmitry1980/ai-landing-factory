"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  createShowcase,
  deleteShowcase,
  exportShowcaseZip,
  listShowcases,
} from "@/lib/showcaseApi";
import type { ShowcaseSummary } from "@/lib/showcase";
import {
  createDefaultShowcaseTemplate,
  createEmptyShowcaseRequest,
} from "@/lib/showcaseTemplates";

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  URL.revokeObjectURL(url);
}

export function ShowcaseList() {
  const router = useRouter();
  const [items, setItems] = useState<ShowcaseSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      setItems(await listShowcases());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки витрин.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function handleCreate(body: Parameters<typeof createShowcase>[0]) {
    setBusy(true);
    setError(null);
    try {
      const created = await createShowcase(body);
      router.push(`/showcase/${created.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось создать витрину.");
      setBusy(false);
    }
  }

  async function handleCreateTemplate() {
    await handleCreate(createDefaultShowcaseTemplate("uii_ai_projects"));
  }

  async function handleCreateEmpty() {
    await handleCreate(createEmptyShowcaseRequest());
  }

  async function handleDelete(id: string) {
    setBusy(true);
    setError(null);
    try {
      await deleteShowcase(id);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось удалить витрину.");
    } finally {
      setBusy(false);
    }
  }

  async function handleExportZip(id: string) {
    setBusy(true);
    setError(null);
    try {
      const { blob, filename } = await exportShowcaseZip(id);
      downloadBlob(blob, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка экспорта ZIP.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <section className="space-y-4 rounded-lg border bg-muted/30 p-5">
        <div>
          <h2 className="text-xl font-semibold">VR/AR витрина проектов</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Соберите интерактивный выставочный стенд из лендингов и ссылок на
            demo-проекты.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={handleCreateTemplate}
            disabled={busy}
            className="rounded-md bg-foreground px-4 py-2 text-sm font-semibold text-background disabled:opacity-50"
          >
            Создать витрину AI-проектов УИИ
          </button>
          <button
            type="button"
            onClick={handleCreateEmpty}
            disabled={busy}
            className="rounded-md border px-4 py-2 text-sm font-medium hover:bg-muted disabled:opacity-50"
          >
            Создать пустую витрину
          </button>
        </div>
      </section>

      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Загрузка…</p>
      ) : items.length === 0 ? (
        <div className="space-y-4 rounded-lg border border-dashed p-8 text-center">
          <p className="text-sm text-muted-foreground">
            Пока витрин нет. Создайте витрину AI-проектов УИИ и добавьте ленды с
            demo-ссылками.
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <button
              type="button"
              onClick={handleCreateTemplate}
              disabled={busy}
              className="rounded-md bg-foreground px-4 py-2 text-sm font-semibold text-background disabled:opacity-50"
            >
              Создать витрину AI-проектов УИИ
            </button>
            <button
              type="button"
              onClick={handleCreateEmpty}
              disabled={busy}
              className="rounded-md border px-4 py-2 text-sm hover:bg-muted disabled:opacity-50"
            >
              Создать пустую витрину
            </button>
          </div>
        </div>
      ) : (
        <ul className="space-y-3">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex flex-wrap items-center justify-between gap-3 rounded-lg border p-4"
            >
              <div className="min-w-0">
                <p className="truncate font-medium">{item.title}</p>
                <p className="text-xs text-muted-foreground">
                  Проектов: {item.project_count}
                  {item.updated_at
                    ? ` · обновлено ${new Date(item.updated_at).toLocaleString("ru-RU")}`
                    : ""}
                </p>
              </div>
              <div className="flex shrink-0 flex-wrap gap-2">
                <Link
                  href={`/showcase/${item.id}`}
                  className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted"
                >
                  Открыть
                </Link>
                <button
                  type="button"
                  onClick={() => handleExportZip(item.id)}
                  disabled={busy}
                  className="rounded-md border px-3 py-1.5 text-sm hover:bg-muted disabled:opacity-50"
                >
                  Экспорт ZIP
                </button>
                <button
                  type="button"
                  onClick={() => handleDelete(item.id)}
                  disabled={busy}
                  className="rounded-md border px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 disabled:opacity-50"
                >
                  Удалить
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
