import Link from "next/link";
import { formatDate, type LibraryCard } from "@/lib/platform";

const MAX_PEOPLE = 3;

const NIGHT_GRID = {
  backgroundImage:
    "linear-gradient(rgba(122,164,255,.06) 1px, transparent 1px), linear-gradient(90deg, rgba(122,164,255,.06) 1px, transparent 1px)",
  backgroundSize: "16px 16px",
};

/** Обложка повторяет тему лендинга: ночной «монитор» или светлый лист, со схемой этапов справа. */
function Cover({ card }: { card: LibraryCard }) {
  const night = card.theme !== "light";
  return (
    <div
      aria-hidden="true"
      style={night ? NIGHT_GRID : undefined}
      className={`flex h-[168px] gap-4 overflow-hidden rounded-[14px] border p-5 transition-colors ${
        night
          ? "border-[#1C2841] bg-[#0C1222] text-[#EEF2FA] group-hover:border-[#2A3A5C]"
          : "border-line bg-paper bg-grid-paper bg-cell-sm text-ink group-hover:border-scheme-line"
      }`}
    >
      <span className="line-clamp-4 min-w-0 flex-1 font-display text-[17px] font-semibold leading-tight">{card.title}</span>
      <span className="flex w-6 flex-col items-center gap-1.5 pt-1">
        {[0, 1, 2].map((i) => (
          <span key={i} className="flex flex-col items-center gap-1.5">
            {i > 0 && <span className={`h-4 w-0.5 ${night ? "bg-[#3FDCFF]/50" : "bg-scheme/60"}`} />}
            <span
              className={`h-3 w-3 rounded-full border-2 ${night ? "border-[#3FDCFF]" : "border-scheme"} ${
                i === 2 ? (night ? "bg-[#3FDCFF]" : "bg-glow") : night ? "bg-[#0C1222]" : "bg-white"
              }`}
            />
          </span>
        ))}
      </span>
    </div>
  );
}

export function LibraryCardView({ card }: { card: LibraryCard }) {
  const people = card.people.slice(0, MAX_PEOPLE);
  const more = card.people.length - people.length;
  return (
    <Link href={card.path} className="group flex flex-col gap-3 text-ink no-underline">
      <Cover card={card} />
      <div className="flex flex-col gap-1.5">
        <h3 className="line-clamp-2 text-[17px] font-semibold leading-snug group-hover:text-scheme">{card.title}</h3>
        {card.summary && <p className="line-clamp-2 text-[15px] leading-snug text-fur">{card.summary}</p>}
        <dl className="mt-1 flex flex-col gap-0.5 text-sm">
          {card.customer && (
            <div className="flex gap-1.5">
              <dt className="shrink-0 text-fur">Заказчик:</dt>
              <dd className="min-w-0 truncate">{card.customer}</dd>
            </div>
          )}
          {people.length > 0 && (
            <div className="flex gap-1.5">
              <dt className="shrink-0 text-fur">Команда:</dt>
              <dd className="min-w-0 truncate">
                {people.join(", ")}
                {more > 0 && ` и ещё ${more}`}
              </dd>
            </div>
          )}
          <div className="flex gap-1.5">
            <dt className="shrink-0 text-fur">Опубликован</dt>
            <dd>{formatDate(card.published_at)}</dd>
          </div>
        </dl>
      </div>
    </Link>
  );
}
