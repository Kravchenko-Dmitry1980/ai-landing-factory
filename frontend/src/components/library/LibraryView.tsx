"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { plural } from "@/lib/plural";
import { platformErrorMessage, searchLibrary, type LibraryCard } from "@/lib/platform";
import { LibraryCardView } from "./LibraryCardView";

const SEARCH_DELAY_MS = 250;

export function resultsHeading(query: string, count: number): string {
  if (count === 0) {
    return `По запросу «${query}» ничего не нашлось. Попробуйте фамилию, заказчика или одно слово из названия.`;
  }
  const verb = plural(count, "нашёлся", "нашлось", "нашлось");
  return `По запросу «${query}» ${verb} ${count} ${plural(count, "лендинг", "лендинга", "лендингов")}`;
}

/** Поиск по библиотеке: название, тема, заказчик, фамилии. Адрес страницы помнит запрос (?q=). */
export function LibraryView({
  initialQuery,
  initialCards,
  initialError,
  initialTotal,
  canEdit,
}: {
  initialQuery: string;
  initialCards: LibraryCard[] | null;
  initialError: string | null;
  /** How many landings the library holds, whatever the query (null if unknown). */
  initialTotal: number | null;
  canEdit: boolean;
}) {
  const searchId = useId();
  const [query, setQuery] = useState(initialQuery);
  const [cards, setCards] = useState(initialCards);
  const [total, setTotal] = useState(initialTotal);
  const [error, setError] = useState(initialError);
  const [busy, setBusy] = useState(false);
  /** The query the cards on screen answer (the input may already hold the next one). */
  const [shownQuery, setShownQuery] = useState(initialQuery.trim());
  const [retry, setRetry] = useState(0);
  const handledRetry = useRef(0);
  const request = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (q === shownQuery && retry === handledRetry.current && cards !== null) {
      // Typed back to what is on screen: an answer still on its way is for another query.
      request.current += 1;
      setBusy(false);
      return;
    }
    handledRetry.current = retry;
    const timer = setTimeout(async () => {
      const id = ++request.current;
      setBusy(true);
      try {
        const found = await searchLibrary(q);
        if (id !== request.current) return;
        setCards(found.cards);
        setTotal(found.total);
        setShownQuery(q);
        setError(null);
        window.history.replaceState(null, "", q ? `/?q=${encodeURIComponent(q)}` : "/");
      } catch (err) {
        if (id !== request.current) return;
        console.error("Library search failed", err);
        // Old cards under a new query would read as its results.
        setCards(null);
        setError(platformErrorMessage(err, "Не удалось выполнить поиск"));
      } finally {
        if (id === request.current) setBusy(false);
      }
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
    // shownQuery and cards are read as the state of the last answer; they must not restart the search.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, retry]);

  const empty = total === 0;

  return (
    <main className="mx-auto flex max-w-[1200px] flex-col gap-10 px-6 pb-20 pt-10">
      <section aria-labelledby={`${searchId}-title`} className="flex flex-col gap-5">
        <div className="flex flex-col gap-2">
          <h1 id={`${searchId}-title`} className="font-display text-[40px] font-semibold leading-tight">
            Библиотека лендингов
          </h1>
          {total !== null && total > 0 && (
            <p className="text-[17px] text-fur">
              {total} {plural(total, "проект", "проекта", "проектов")} УИИ. Ищите по названию, теме, заказчику или
              фамилии участника.
            </p>
          )}
        </div>
        {!empty && (
          <div className="max-w-[720px]">
            <label htmlFor={searchId} className="sr-only">
              Поиск по библиотеке
            </label>
            <input
              id={searchId}
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Например: контроль операций, Петрова, приёмная комиссия"
              autoComplete="off"
              className="h-14 w-full rounded-[14px] border border-field bg-white px-5 text-[17px] shadow-[0_1px_0_#E2E7F1] focus:border-scheme focus:outline-none focus:ring-2 focus:ring-scheme/25"
            />
          </div>
        )}
      </section>

      {error && (
        <div role="alert" className="flex max-w-[720px] flex-wrap items-center gap-3 rounded-xl border border-line bg-white px-5 py-4 text-[15px]">
          <span>{error}</span>
          <button
            type="button"
            onClick={() => setRetry((n) => n + 1)}
            className="rounded-lg border border-field px-3 py-1.5 hover:bg-paper"
          >
            Повторить
          </button>
        </div>
      )}

      {empty && (
        <div className="flex max-w-[620px] flex-col items-start gap-4 text-[17px] leading-relaxed text-fur">
          <p>В библиотеке пока нет лендингов. Они появятся здесь, когда редакторы опубликуют первые страницы проектов.</p>
          {canEdit && (
            <Link
              href="/studio"
              className="inline-flex h-11 items-center rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white no-underline hover:bg-scheme-hover"
            >
              Открыть студию
            </Link>
          )}
        </div>
      )}

      {!empty && cards && (
        <section aria-live="polite" aria-busy={busy} aria-label="Лендинги" className="flex flex-col gap-5">
          {shownQuery && <h2 className="text-[17px] text-fur">{resultsHeading(shownQuery, cards.length)}</h2>}
          {cards.length > 0 && (
            <ul
              className={`grid grid-cols-[repeat(auto-fill,minmax(280px,1fr))] gap-x-6 gap-y-9 transition-opacity ${
                busy ? "opacity-60" : ""
              }`}
            >
              {cards.map((card) => (
                <li key={card.slug}>
                  <LibraryCardView card={card} />
                </li>
              ))}
            </ul>
          )}
        </section>
      )}
    </main>
  );
}
