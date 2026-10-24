"use client";

import { useEffect, useId, useRef } from "react";

interface Props {
  open: boolean;
  fileName: string;
  busy: boolean;
  error: string | null;
  onDownload: () => void;
  onClose: () => void;
}

/** "Скачать сайт": one file, plain words about what to do with it. */
export function DownloadDialog({ open, fileName, busy, error, onDownload, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onCancel={(e) => {
        // Esc must not hide a file that is still being prepared.
        if (busy) e.preventDefault();
      }}
      className="w-[min(520px,calc(100vw-32px))] rounded-2xl border border-line bg-white p-0 text-ink shadow-xl backdrop:bg-ink/40"
    >
      <div className="flex flex-col gap-4 p-7">
        <h2 id={titleId} className="font-display text-2xl font-semibold">
          Скачать сайт
        </h2>
        <p className="text-base leading-relaxed">
          Получится один файл <span className="font-semibold">{fileName}</span>. Он открывается в любом браузере, интернет
          не нужен.
        </p>
        <p className="text-[15px] leading-relaxed text-fur">
          Чтобы страница появилась на сайте университета, передайте этот файл администратору сайта.
        </p>
        {error && (
          <p role="alert" className="text-[15px] text-danger">
            {error}
          </p>
        )}
        <div className="flex flex-wrap justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            disabled={busy}
            className="h-11 rounded-[10px] border border-field bg-white px-5 text-[15px] hover:bg-paper disabled:opacity-50"
          >
            Отмена
          </button>
          <button
            type="button"
            onClick={onDownload}
            disabled={busy}
            aria-busy={busy}
            className="h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover disabled:cursor-wait disabled:opacity-80"
          >
            {busy ? "Готовлю файл…" : "Скачать файл"}
          </button>
        </div>
      </div>
    </dialog>
  );
}

/** Saves a string as a file through a temporary link. */
export function saveTextFile(text: string, fileName: string, type = "text/html") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  a.click();
  // Revoke later: some browsers start reading the blob after click() returns.
  setTimeout(() => URL.revokeObjectURL(url), 10_000);
}
