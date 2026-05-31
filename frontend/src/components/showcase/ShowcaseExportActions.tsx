"use client";

import { useState } from "react";
import { exportShowcaseHtml, exportShowcaseZip } from "@/lib/showcaseApi";

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

export function ShowcaseExportActions({
  showcaseId,
  projectCount,
}: {
  showcaseId: string;
  projectCount: number;
}) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const emptyShowcase = projectCount === 0;

  async function handleHtml() {
    if (emptyShowcase) {
      setError("Витрина пустая. Добавьте проекты перед демонстрацией.");
      return;
    }
    setBusy(true);
    setStatus(null);
    setError(null);
    try {
      const result = await exportShowcaseHtml(showcaseId);
      downloadBlob(
        new Blob([result.html], { type: "text/html" }),
        "showcase.html",
      );
      setStatus(
        `HTML экспортирован: ${result.project_count} проект(ов). Для офлайн-демо используйте ZIP.`,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка экспорта HTML.");
    } finally {
      setBusy(false);
    }
  }

  async function handleZip() {
    if (emptyShowcase) {
      setError("Витрина пустая. Добавьте проекты перед демонстрацией.");
      return;
    }
    setBusy(true);
    setStatus(null);
    setError(null);
    try {
      const { blob, filename } = await exportShowcaseZip(showcaseId);
      downloadBlob(blob, filename);
      setStatus(`ZIP экспортирован (${filename}). Распакуйте и откройте showcase.html.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка экспорта ZIP.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-3">
      {emptyShowcase && (
        <p className="rounded-md border border-amber-200 bg-amber-50 p-2 text-sm text-amber-900">
          Витрина пустая. Добавьте проекты перед демонстрацией.
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={handleHtml}
          disabled={busy}
          className="rounded-md border px-4 py-2 text-sm font-semibold disabled:opacity-50"
        >
          {busy ? "Экспорт…" : "Экспорт HTML"}
        </button>
        <button
          type="button"
          onClick={handleZip}
          disabled={busy}
          className="rounded-md bg-foreground px-4 py-2 text-sm font-semibold text-background disabled:opacity-50"
        >
          {busy ? "Экспорт…" : "Экспорт ZIP для офлайн-демо"}
        </button>
      </div>
      <p className="text-xs text-muted-foreground">
        ZIP содержит showcase.html и локальный A-Frame runtime. После распаковки
        откройте showcase.html. 3D-стенд работает офлайн; demo-ссылки требуют
        интернет.
      </p>
      {status && (
        <p className="rounded-md border border-green-300 bg-green-50 p-2 text-sm text-green-700">
          {status}
        </p>
      )}
      {error && (
        <p className="rounded-md border border-red-300 bg-red-50 p-2 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}
