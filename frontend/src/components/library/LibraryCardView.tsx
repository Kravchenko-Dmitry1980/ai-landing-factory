import Link from "next/link";
import { plural } from "@/lib/plural";
import { formatYear, type LibraryCard } from "@/lib/platform";

export type CardSize = "large" | "regular";

const SIZES: Record<CardSize, { card: string; cover: string; title: string; cat: string }> = {
  large: {
    card: "w-[min(520px,84vw)]",
    cover: "h-[260px]",
    title: "text-[clamp(20px,2.4vw,24px)] line-clamp-4",
    cat: "h-16 w-16 bottom-9",
  },
  regular: {
    card: "w-[min(340px,78vw)]",
    cover: "h-[200px]",
    title: "text-[19px] line-clamp-3",
    cat: "h-12 w-12 bottom-8",
  },
};

/** Под обложкой: участники, если они есть на странице, иначе заказчик. */
export function cardExtra(card: LibraryCard): string {
  const n = card.people.length;
  if (n > 0) return `${n} ${plural(n, "участник", "участника", "участников")}`;
  return card.customer;
}

/**
 * Обложка повторяет тему страницы: ночной «монитор» со свечением или светлый лист.
 * Полосы внизу — тот же жест, что прогресс этапов на самом лендинге.
 */
function Cover({ card, size }: { card: LibraryCard; size: CardSize }) {
  const night = card.theme !== "light";
  const s = SIZES[size];
  return (
    <div
      aria-hidden="true"
      className={`relative flex flex-col justify-between overflow-hidden rounded-[20px] border p-[18px] transition-colors ${s.cover} ${
        night
          ? "border-night-edge bg-night-card text-night-ink shadow-[0_24px_50px_-30px_rgba(0,0,0,.8)] group-hover:border-[#3FDCFF]/60"
          : "border-line bg-paper bg-grid-paper bg-cell-sm text-ink group-hover:border-scheme-line"
      }`}
    >
      <div className={`flex items-center justify-between gap-3 text-xs ${night ? "text-[#8FA0BF]" : "text-fur"}`}>
        <span className="min-w-0 truncate">{card.customer}</span>
        <span className="flex flex-none items-center gap-1.5">
          <span className={`h-[7px] w-[7px] rounded-full ${night ? "bg-[#3FDCFF] shadow-[0_0_8px_#3FDCFF]" : "bg-scheme"}`} />
          {formatYear(card.published_at)}
        </span>
      </div>
      <span className={`pr-14 font-display font-bold leading-[1.08] tracking-[-0.015em] ${s.title}`}>{card.title}</span>
      <div className="flex flex-col gap-1.5">
        <span className={`h-[5px] w-full rounded ${night ? "bg-[#3FDCFF] shadow-[0_0_10px_rgba(63,220,255,.6)]" : "bg-scheme"}`} />
        <span className={`h-[5px] w-[72%] rounded ${night ? "bg-[#3FDCFF]/55" : "bg-scheme/50"}`} />
        <span className={`h-[5px] w-[48%] rounded ${night ? "bg-night-edge" : "bg-grid"}`} />
      </div>
      {/* eslint-disable-next-line @next/next/no-img-element -- статичный логотип, оптимизирован заранее */}
      <img src="/brand/cat-mark.webp" alt="" className={`absolute right-2.5 object-contain ${s.cat}`} />
    </div>
  );
}

export function LibraryCardView({ card, size = "regular" }: { card: LibraryCard; size?: CardSize }) {
  const topic = card.topics[0]?.label;
  const extra = cardExtra(card);
  return (
    <Link href={card.path} className={`group flex flex-none flex-col gap-3 text-night-ink no-underline ${SIZES[size].card}`}>
      <Cover card={card} size={size} />
      {/* The cover is decoration for screen readers: what it shows is said here in words. */}
      <span className="sr-only">
        {[card.title, card.customer, formatYear(card.published_at), card.has_demo ? "есть демо" : ""].filter(Boolean).join(", ")}
      </span>
      <span className="flex flex-wrap items-center gap-2.5">
        {card.has_demo && <span className="rounded-full border border-scheme px-2.5 py-1 text-[13px] text-scheme">Демо</span>}
        {topic && <span className="rounded-full border border-night-rim px-2.5 py-1 text-[13px] text-night-soft">{topic}</span>}
        {extra && <span className="text-[13px] text-night-muted">{extra}</span>}
      </span>
    </Link>
  );
}
