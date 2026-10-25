"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import type { LibraryCard } from "@/lib/platform";
import { LibraryCardView, type CardSize } from "./LibraryCardView";

/** How far an arrow moves the row: almost a screen, so the last card stays in sight as an anchor. */
const PAGE_SHARE = 0.85;
const EDGE_SLACK_PX = 4;

function ArrowButton({
  direction,
  disabled,
  label,
  onClick,
}: {
  direction: "back" | "next";
  disabled: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-disabled={disabled}
      onClick={() => !disabled && onClick()}
      className="grid h-11 w-11 place-items-center rounded-full border border-night-rim bg-night-panel text-xl text-night-ink transition-colors hover:border-[#3FDCFF] aria-disabled:cursor-default aria-disabled:opacity-35 aria-disabled:hover:border-night-rim"
    >
      <span aria-hidden="true">{direction === "back" ? "‹" : "›"}</span>
    </button>
  );
}

/**
 * Карусель библиотеки: строка карточек с прокруткой по карточке.
 * Листается стрелками, колесом, пальцем и клавишей Tab (браузер сам докручивает к ссылке).
 */
export function Shelf({
  title,
  note,
  cards,
  size = "regular",
}: {
  title: string;
  note?: string;
  cards: LibraryCard[];
  size?: CardSize;
}) {
  const headingId = useId();
  const track = useRef<HTMLUListElement>(null);
  const [edges, setEdges] = useState({ atStart: true, atEnd: true });

  const measure = useCallback(() => {
    const el = track.current;
    if (!el) return;
    const atStart = el.scrollLeft <= EDGE_SLACK_PX;
    const atEnd = el.scrollLeft + el.clientWidth >= el.scrollWidth - EDGE_SLACK_PX;
    // Scrolling fires every frame: re-render the row only when an edge is reached or left.
    setEdges((prev) => (prev.atStart === atStart && prev.atEnd === atEnd ? prev : { atStart, atEnd }));
  }, []);

  useEffect(() => {
    const el = track.current;
    if (!el) return;
    measure();
    el.addEventListener("scroll", measure, { passive: true });
    const resize = new ResizeObserver(measure);
    resize.observe(el);
    return () => {
      el.removeEventListener("scroll", measure);
      resize.disconnect();
    };
  }, [measure, cards]);

  function move(direction: 1 | -1) {
    const el = track.current;
    if (!el) return;
    const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    el.scrollBy({ left: direction * el.clientWidth * PAGE_SHARE, behavior: still ? "auto" : "smooth" });
  }

  const scrollable = !(edges.atStart && edges.atEnd);

  return (
    <section aria-labelledby={headingId} className="mx-auto max-w-[1240px] px-6 pb-2 pt-9">
      <div className="mb-[18px] flex items-end justify-between gap-4">
        <div className="flex min-w-0 flex-col gap-1">
          <h2 id={headingId} className="font-display text-[clamp(24px,3vw,30px)] font-bold tracking-[-0.02em] text-night-ink">
            {title}
          </h2>
          {note && <p className="text-[15px] text-night-muted">{note}</p>}
        </div>
        {scrollable && (
          <div className="flex flex-none gap-2.5">
            <ArrowButton direction="back" label={`Назад: ${title}`} disabled={edges.atStart} onClick={() => move(-1)} />
            <ArrowButton direction="next" label={`Дальше: ${title}`} disabled={edges.atEnd} onClick={() => move(1)} />
          </div>
        )}
      </div>
      {/* relative: hidden screen-reader text inside the cards is absolutely positioned; without a
          positioned track it escapes the scroll clipping and widens the whole page. */}
      <ul
        ref={track}
        className="relative -mx-6 flex snap-x snap-mandatory scroll-px-6 gap-5 overflow-x-auto px-6 pb-4 pt-1 [scrollbar-width:none] motion-safe:scroll-smooth [&::-webkit-scrollbar]:hidden"
      >
        {cards.map((card) => (
          <li key={card.slug} className="snap-start">
            <LibraryCardView card={card} size={size} />
          </li>
        ))}
      </ul>
    </section>
  );
}
