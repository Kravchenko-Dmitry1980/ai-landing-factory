"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { plural } from "@/lib/plural";
import {
  formatYear,
  platformErrorMessage,
  searchLibrary,
  type LibraryHit,
  type LibrarySearch,
  type LibraryShelves,
} from "@/lib/platform";
import { Shelf } from "./Shelf";

const SEARCH_DELAY_MS = 250;
const RESULTS_FIRST = 8;
/** The backend reads this much of a query; the field stops there too. */
export const MAX_QUERY_CHARS = 200;
const SEARCH_FAILED = "Не удалось выполнить поиск. Попробуйте ещё раз через минуту.";

/** What the search found, said once for the eyes and once for screen readers. */
export function resultsHeading(search: Pick<LibrarySearch, "query" | "direct_total" | "related_total" | "terms" | "hits">): string {
  const { query, direct_total: direct, related_total: related } = search;
  if (search.terms === 0) {
    return `В запросе «${query}» нет слов для поиска. Напишите слово из названия, фамилию или тему.`;
  }
  if (direct === 0 && related === 0) {
    return `По запросу «${query}» ничего не нашлось. Попробуйте фамилию, заказчика или тему, например «видео» или «медицина».`;
  }
  let text: string;
  if (direct === 0) {
    text = `Точных совпадений с «${query}» нет. Проекты на похожую тему: ${related}.`;
  } else {
    const verb = plural(direct, "нашёлся", "нашлось", "нашлось");
    text = `По запросу «${query}» ${verb} ${direct} ${plural(direct, "проект", "проекта", "проектов")}`;
    text += related > 0 ? `, ещё ${related} на похожую тему.` : ".";
  }
  const shown = search.hits.length;
  return shown < direct + related ? `${text} Показаны первые ${shown}.` : text;
}

function hitMeta(hit: LibraryHit): string {
  const { card } = hit;
  return [card.topics[0]?.label, card.customer, formatYear(card.published_at)].filter(Boolean).join(", ");
}

function SearchResults({ search, busy }: { search: LibrarySearch; busy: boolean }) {
  const [showAll, setShowAll] = useState(false);
  const list = useRef<HTMLUListElement>(null);
  const shown = showAll ? search.hits : search.hits.slice(0, RESULTS_FIRST);

  // The button disappears when pressed: keyboard focus moves on to the first result it revealed.
  useEffect(() => {
    if (showAll) list.current?.querySelectorAll("a")[RESULTS_FIRST]?.focus();
  }, [showAll]);

  return (
    <div
      role="region"
      aria-label="Результаты поиска"
      aria-busy={busy}
      className={`mt-2.5 rounded-2xl border border-night-rim bg-night-panel p-2 transition-opacity ${busy ? "opacity-60" : ""}`}
    >
      <p className="px-4 py-2.5 text-[15px] text-night-soft">{resultsHeading(search)}</p>
      {shown.length > 0 && (
        <ul ref={list} className="flex flex-col">
          {shown.map((hit) => (
            <li key={hit.card.slug}>
              <Link
                href={hit.card.path}
                className="flex flex-wrap items-center justify-between gap-x-4 gap-y-1.5 rounded-[10px] px-4 py-3 text-night-ink no-underline hover:bg-night-card focus-visible:bg-night-card"
              >
                <span className="flex min-w-0 flex-[1_1_320px] flex-col gap-0.5">
                  <span className="font-semibold">{hit.card.title}</span>
                  <span className="text-sm text-night-muted">{hitMeta(hit)}</span>
                </span>
                <span className="flex flex-wrap gap-1.5">
                  {hit.reasons.map((reason) => (
                    <span
                      key={reason}
                      className={`rounded-full px-2.5 py-1 text-[13px] ${
                        hit.similar_topic ? "border border-dashed border-[#3FDCFF]/45 text-night-chip" : "bg-[#3FDCFF]/[.12] text-night-chip"
                      }`}
                    >
                      {reason}
                    </span>
                  ))}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      )}
      {!showAll && search.hits.length > RESULTS_FIRST && (
        <button
          type="button"
          onClick={() => setShowAll(true)}
          className="m-2 rounded-lg border border-night-rim px-3 py-1.5 text-[15px] text-night-ink hover:border-[#3FDCFF]"
        >
          Показать все {search.hits.length}
        </button>
      )}
    </div>
  );
}

function Notice({ text, action, onAction }: { text: string; action: string; onAction: () => void }) {
  return (
    <div
      role="alert"
      className="flex max-w-[860px] flex-wrap items-center gap-3 rounded-xl border border-night-rim bg-night-panel px-5 py-4 text-[15px] text-night-ink"
    >
      <span>{text}</span>
      <button type="button" onClick={onAction} className="rounded-lg border border-night-rim px-3 py-1.5 hover:border-[#3FDCFF]">
        {action}
      </button>
    </div>
  );
}

/**
 * Библиотека: поиск с причиной каждого совпадения, кнопки тем и карусели «Новые проекты», по темам
 * и «Другие проекты». Адрес страницы помнит запрос (?q=), чтобы им можно было поделиться.
 */
export function LibraryView({
  initialQuery,
  initialSearch,
  initialSearchFailed,
  shelves,
  canEdit,
}: {
  initialQuery: string;
  initialSearch: LibrarySearch | null;
  initialSearchFailed: boolean;
  /** null: the carousels did not load (the search may still work). */
  shelves: LibraryShelves | null;
  canEdit: boolean;
}) {
  const searchId = useId();
  const [query, setQuery] = useState(initialQuery);
  const [search, setSearch] = useState(initialSearch);
  const [searchError, setSearchError] = useState<string | null>(initialSearchFailed ? SEARCH_FAILED : null);
  const [busy, setBusy] = useState(false);
  const [retry, setRetry] = useState(0);
  const handledRetry = useRef(0);
  const request = useRef(0);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      // Cleared: no results panel, no old error, and an answer still on its way is for an old query.
      request.current += 1;
      setSearch(null);
      setSearchError(null);
      setBusy(false);
      if (window.location.search) window.history.replaceState(null, "", "/");
      return;
    }
    if (search && q === search.query && retry === handledRetry.current) {
      request.current += 1;
      setBusy(false);
      return;
    }
    handledRetry.current = retry;
    const timer = setTimeout(async () => {
      const id = ++request.current;
      setBusy(true);
      setSearchError(null);
      try {
        const found = await searchLibrary(q);
        if (id !== request.current) return;
        setSearch({ ...found, query: q });
        window.history.replaceState(null, "", `/?q=${encodeURIComponent(q)}`);
      } catch (err) {
        if (id !== request.current) return;
        console.error("Library search failed", err);
        // Old results under a new query would read as its answer.
        setSearch(null);
        setSearchError(platformErrorMessage(err, "Не удалось выполнить поиск"));
      } finally {
        if (id === request.current) setBusy(false);
      }
    }, SEARCH_DELAY_MS);
    return () => clearTimeout(timer);
    // `search` is read as the last answer; it must not restart the search.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, retry]);

  const total = shelves?.total ?? search?.total ?? null;
  const empty = total === 0;
  const picked = query.trim().toLowerCase();
  // One live region that stays in the page: screen readers miss regions that appear with their text.
  const announcement = busy ? "" : (searchError ?? (search && query.trim() ? resultsHeading(search) : ""));

  return (
    <main className="pb-20">
      <p className="sr-only" aria-live="polite">
        {announcement}
      </p>
      <section aria-labelledby={`${searchId}-title`} className="mx-auto flex max-w-[1240px] flex-col gap-[22px] px-6 pb-6 pt-14">
        <h1
          id={`${searchId}-title`}
          className="font-display text-[clamp(40px,6vw,56px)] font-bold leading-[1.02] tracking-[-0.03em] text-night-ink"
        >
          Библиотека проектов
        </h1>
        <p className="max-w-[620px] text-[19px] leading-[1.55] text-night-soft">
          {total ? `${total} ${plural(total, "готовая страница", "готовые страницы", "готовых страниц")} проектов УИИ. ` : ""}
          Ищите по названию, теме, участнику или заказчику.
        </p>

        {!empty && (
          <div className="max-w-[860px]">
            <label htmlFor={searchId} className="sr-only">
              Поиск проектов
            </label>
            <div className="flex h-[62px] items-center gap-3 rounded-2xl bg-white px-5 text-ink shadow-[0_24px_60px_-30px_rgba(63,220,255,.45)] focus-within:ring-2 focus-within:ring-[#3FDCFF]">
              <svg aria-hidden="true" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#5F6673" strokeWidth="2" strokeLinecap="round">
                <circle cx="11" cy="11" r="7" />
                <path d="M20 20l-4-4" />
              </svg>
              <input
                id={searchId}
                type="search"
                value={query}
                maxLength={MAX_QUERY_CHARS}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Название, тема, фамилия участника или заказчик"
                autoComplete="off"
                className="h-full min-w-0 flex-1 border-0 bg-transparent text-lg text-ink outline-none placeholder:text-fur"
              />
            </div>
            {search && query.trim() && <SearchResults key={search.query} search={search} busy={busy} />}
            {searchError && (
              <div className="mt-2.5">
                <Notice text={searchError} action="Повторить поиск" onAction={() => setRetry((n) => n + 1)} />
              </div>
            )}
          </div>
        )}

        {shelves && shelves.topics.length > 0 && (
          // Phones: one row that scrolls sideways instead of half a screen of buttons.
          <div
            role="group"
            aria-label="Темы"
            className="-mx-6 flex gap-2.5 overflow-x-auto px-6 py-1 [scrollbar-width:none] sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 [&::-webkit-scrollbar]:hidden"
          >
            {shelves.topics.map((topic) => (
              <button
                key={topic.key}
                type="button"
                aria-pressed={picked === topic.label.toLowerCase()}
                onClick={() => setQuery(picked === topic.label.toLowerCase() ? "" : topic.label)}
                className="h-[38px] flex-none rounded-full border border-night-rim bg-night-panel px-4 text-sm text-night-ink transition-colors hover:border-[#3FDCFF] aria-pressed:border-[#3FDCFF] aria-pressed:bg-[#3FDCFF]/10"
              >
                {topic.label} <span className="text-night-muted">{topic.count}</span>
              </button>
            ))}
          </div>
        )}
      </section>

      {!shelves && (
        <div className="mx-auto max-w-[1240px] px-6 pt-6">
          <Notice
            text="Не удалось загрузить подборки библиотеки. Поиск работает, а подборки появятся после обновления страницы."
            action="Обновить страницу"
            onAction={() => window.location.reload()}
          />
        </div>
      )}

      {empty && (
        <div className="mx-auto flex max-w-[1240px] flex-col items-start gap-4 px-6 text-[17px] leading-relaxed text-night-soft">
          <p className="max-w-[620px]">
            В библиотеке пока нет проектов. Они появятся здесь, когда редакторы опубликуют первые страницы.
          </p>
          {canEdit && (
            <Link
              href="/studio"
              className="inline-flex h-11 items-center rounded-[10px] bg-[#3FDCFF] px-5 text-[15px] font-semibold text-[#04202A] no-underline hover:bg-[#7FE8FF]"
            >
              Открыть студию
            </Link>
          )}
        </div>
      )}

      {shelves && shelves.fresh.length > 0 && (
        <Shelf title="Новые проекты" note="Последние опубликованные страницы" cards={shelves.fresh} size="large" />
      )}
      {shelves?.shelves.map((shelf) => <Shelf key={shelf.key} title={shelf.label} note={shelf.note} cards={shelf.cards} />)}
    </main>
  );
}
