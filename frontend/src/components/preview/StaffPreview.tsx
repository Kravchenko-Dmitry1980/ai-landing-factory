"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { fetchLandingFile, landingErrorMessage, type LandingFile } from "@/lib/landingFile";
import { CatLogoLink } from "@/components/shell/AppHeader";
import { DownloadDialog, saveBlob } from "@/components/shell/DownloadDialog";

type State = { status: "loading" } | { status: "ready"; file: LandingFile } | { status: "error"; message: string };

function titleOf(html: string): string {
  return new DOMParser().parseFromString(html, "text/html").title;
}

/** The page exactly as visitors get it: the frame shows the same text that "Скачать сайт" saves. */
export function StaffPreview({ projectId }: { projectId: string }) {
  const [state, setState] = useState<State>({ status: "loading" });
  const [open, setOpen] = useState(false);

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      setState({ status: "ready", file: await fetchLandingFile(projectId) });
    } catch (err) {
      setState({ status: "error", message: landingErrorMessage(err, "Не удалось собрать страницу") });
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  const file = state.status === "ready" ? state.file : null;
  const title = file ? titleOf(file.html) : "";

  return (
    <div className="flex h-screen flex-col bg-paper">
      <header className="border-b border-grid bg-white">
        <div className="flex flex-wrap items-center gap-4 px-6 py-2.5">
          <CatLogoLink compact />
          <span className="min-w-0 flex-[1_1_200px] truncate text-[15px] text-fur">Так страницу увидят посетители</span>
          <div className="flex flex-wrap gap-2.5">
            <Link
              href={`/editor/${projectId}`}
              className="inline-flex h-10 items-center rounded-[10px] border border-field bg-white px-4 text-[15px] text-ink no-underline hover:bg-paper"
            >
              Вернуться в редактор
            </Link>
            <button
              type="button"
              onClick={() => setOpen(true)}
              disabled={!file}
              className="h-10 rounded-[10px] bg-scheme px-[18px] text-[15px] font-semibold text-white hover:bg-scheme-hover disabled:opacity-50"
            >
              Скачать сайт
            </button>
          </div>
        </div>
      </header>
      <main className="min-h-0 flex-1">
        <h1 className="sr-only">Предпросмотр лендинга{title ? ` «${title}»` : ""}</h1>
        {state.status === "loading" && <p className="px-6 py-10 text-fur">Собираю страницу…</p>}
        {state.status === "error" && (
          <div role="alert" className="mx-auto flex max-w-[640px] flex-col items-start gap-4 px-6 py-16 text-[17px]">
            <p>{state.message}</p>
            <button
              type="button"
              onClick={() => void load()}
              className="h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover"
            >
              Повторить
            </button>
          </div>
        )}
        {file && (
          // sandbox="" keeps the page script-free and isolated, exactly like an opened file.
          <iframe srcDoc={file.html} sandbox="" title="Лендинг так, как его увидят посетители" className="h-full w-full border-0" />
        )}
      </main>
      {file && (
        <DownloadDialog
          open={open}
          fileName={file.fileName}
          busy={false}
          error={null}
          onDownload={() => {
            saveBlob(new Blob([file.html], { type: "text/html;charset=utf-8" }), file.fileName);
            setOpen(false);
          }}
          onClose={() => setOpen(false)}
        />
      )}
    </div>
  );
}
