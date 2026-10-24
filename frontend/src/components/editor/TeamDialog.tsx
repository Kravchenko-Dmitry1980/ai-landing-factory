"use client";

import { useEffect, useId, useRef, useState } from "react";

interface Props {
  open: boolean;
  initialText: string;
  busy: boolean;
  error: string | null;
  onSave: (text: string) => void;
  onClose: () => void;
}

/** Team list as plain text: one person per line, achievements as "- " lines under the person. */
export function TeamDialog({ open, initialText, busy, error, onSave, onClose }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const fieldId = useId();
  const [text, setText] = useState(initialText);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setText(initialText);
      dialog.showModal();
    }
    if (!open && dialog.open) dialog.close();
  }, [open, initialText]);

  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onClose={onClose}
      onCancel={(e) => {
        // Esc must not hide a save that is still running.
        if (busy) e.preventDefault();
      }}
      className="w-[min(720px,calc(100vw-32px))] rounded-2xl border border-line bg-white p-0 text-ink shadow-xl backdrop:bg-ink/40"
    >
      <div className="flex flex-col gap-4 p-7">
        <h2 id={titleId} className="font-display text-2xl font-semibold">
          Команда проекта
        </h2>
        <label htmlFor={fieldId} className="text-[15px] leading-relaxed text-fur">
          Каждый участник с новой строки: «Фамилия Имя — роль». Что человек сделал, можно перечислить ниже строками,
          которые начинаются с дефиса.
        </label>
        <textarea
          id={fieldId}
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={14}
          className="w-full rounded-xl border border-field bg-white p-3.5 text-[15px] leading-relaxed"
        />
        {error && (
          <p role="alert" className="text-[15px] text-danger">
            {error}
          </p>
        )}
        <div className="flex flex-wrap justify-end gap-3">
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
            onClick={() => onSave(text)}
            disabled={busy}
            aria-busy={busy}
            className="h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover disabled:cursor-wait disabled:opacity-80"
          >
            {busy ? "Сохраняю…" : "Сохранить список"}
          </button>
        </div>
      </div>
    </dialog>
  );
}
