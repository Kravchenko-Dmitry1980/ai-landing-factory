"use client";

import Link from "next/link";
import { useEffect } from "react";
import { CatLogoLink } from "@/components/shell/AppHeader";

/** Любая страница, которая не смогла собраться на сервере (обычно backend не ответил). */
export default function AppError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Page failed", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-grid bg-white">
        <div className="mx-auto max-w-[1200px] px-6 py-3">
          <CatLogoLink />
        </div>
      </header>
      <main className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-16">
        <h1 className="font-display text-3xl font-semibold">Страница не открылась</h1>
        <p className="text-[17px] text-fur">
          Сервер сейчас не отвечает или ответил с ошибкой. Подождите минуту и попробуйте ещё раз. Если не помогает,
          сообщите администратору.
        </p>
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
            Библиотека
          </Link>
        </div>
      </main>
    </div>
  );
}
