"use client";

import Link from "next/link";
import { useEffect } from "react";
import { AppHeader } from "@/components/shell/AppHeader";

export default function EditorRouteError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Editor route failed", error);
  }, [error]);

  return (
    <>
      <AppHeader />
      <main className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-16">
        <h1 className="font-display text-3xl font-semibold">Не удалось открыть лендинг</h1>
        <p className="text-[17px] text-fur">Сервер не ответил. Проверьте подключение и попробуйте ещё раз.</p>
        {error.digest && <p className="text-xs text-fur">Код для разработчика: {error.digest}</p>}
        <div className="flex flex-wrap gap-3">
          <button
            type="button"
            onClick={() => reset()}
            className="h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover"
          >
            Повторить
          </button>
          <Link
            href="/"
            className="inline-flex h-11 items-center rounded-[10px] border border-field bg-white px-5 text-[15px] text-ink no-underline hover:bg-paper"
          >
            Ваши лендинги
          </Link>
        </div>
      </main>
    </>
  );
}
