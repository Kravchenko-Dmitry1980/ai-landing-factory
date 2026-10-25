import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CatLogoLink } from "@/components/shell/AppHeader";
import { formatDate, hasRole, type LibraryCard, type SimilarCard } from "@/lib/platform";
import { backendFetch, requireUser } from "@/lib/session.server";

type Props = { params: Promise<{ slug: string }> };

const BUTTON =
  "inline-flex h-10 items-center rounded-[10px] border border-night-rim px-4 text-[15px] text-night-ink no-underline hover:border-[#3FDCFF]";

async function loadCard(slug: string): Promise<LibraryCard | null> {
  const res = await backendFetch(`/library/${encodeURIComponent(slug)}`, { signal: AbortSignal.timeout(10_000) });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Library card request failed: HTTP ${res.status}`);
  const card = (await res.json()) as LibraryCard;
  // Anything else under /library/… (a future route) must not pass for a landing.
  if (card?.slug !== slug) {
    console.error("Published page: the library answered with something else for", slug);
    return null;
  }
  return card;
}

/** Neighbours are a suggestion: without them the page still works, so a failure only hides the block. */
async function loadSimilar(slug: string): Promise<SimilarCard[]> {
  try {
    const res = await backendFetch(`/library/${encodeURIComponent(slug)}/similar`, { signal: AbortSignal.timeout(10_000) });
    // A withdrawn or mistyped address: the page itself says so, nothing to report here.
    if (res.status === 404) return [];
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return (await res.json()) as SimilarCard[];
  } catch (err) {
    console.error("Published page: similar landings unavailable", slug, err);
    return [];
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const card = await loadCard(slug).catch((err: unknown) => {
    console.error("Published page: title unavailable", slug, err);
    return null;
  });
  return { title: card ? `${card.title} — Ленд` : "Лендинг — Ленд" };
}

/**
 * Опубликованный лендинг: полоса библиотеки, сама страница в изолированной рамке на весь экран
 * и под ней «Похоже на…» — дочитав страницу, посетитель прокручивает дальше прямо к соседям.
 */
export default async function PublishedPage({ params }: Props) {
  const { slug } = await params;
  const user = await requireUser(`/p/${slug}`);
  const [card, similar] = await Promise.all([loadCard(slug), loadSimilar(slug)]);
  if (!card) notFound();

  const byline = [card.published_by_name, formatDate(card.published_at)].filter(Boolean).join(", ");
  const raw = `/p/${encodeURIComponent(card.slug)}/raw`;

  return (
    <div className="bg-night-bg text-night-ink">
      <div className="flex h-[100dvh] flex-col">
        <header className="border-b border-night-line bg-night-bg">
          <div className="flex flex-wrap items-center gap-x-5 gap-y-2 px-6 py-2.5">
            <CatLogoLink compact night />
            <Link href="/" className="text-[15px] text-[#7AA4FF] no-underline hover:text-[#A9C4FF]">
              Библиотека
            </Link>
            <div className="flex min-w-0 flex-[1_1_240px] flex-col">
              <span className="truncate text-[15px] font-semibold">{card.title}</span>
              {byline && <span className="truncate text-[13px] text-night-muted">Опубликовано: {byline}</span>}
            </div>
            <div className="flex flex-wrap items-center gap-2.5">
              {similar.length > 0 && (
                <a href="#similar" className={BUTTON}>
                  Похожие проекты
                </a>
              )}
              {hasRole(user, "editor") && (
                <Link href={`/editor/${card.project_id}`} className={BUTTON}>
                  Править в студии
                </Link>
              )}
              <a href={raw} target="_blank" rel="noopener" className={BUTTON}>
                Открыть во весь экран
              </a>
            </div>
          </div>
        </header>
        <main className="min-h-0 flex-1">
          <h1 className="sr-only">{card.title}</h1>
          {/* sandbox="": the published page runs no scripts and gets no access to this site. */}
          <iframe src={raw} sandbox="" title={`Лендинг «${card.title}»`} className="h-full w-full border-0" />
        </main>
      </div>

      {similar.length > 0 && (
        <section id="similar" aria-labelledby="similar-title" className="mx-auto max-w-[1240px] scroll-mt-4 px-6 pb-[72px] pt-12">
          <div className="flex flex-col gap-4 rounded-[22px] border border-night-line bg-night-panel p-7">
            <h2 id="similar-title" className="font-display text-[26px] font-bold leading-tight">
              Похоже на «{card.title}»
            </h2>
            <p className="text-[15px] text-night-muted">Подобраны по теме, заказчику и общим словам в тексте.</p>
            <ul className="flex flex-wrap gap-3">
              {similar.map(({ card: other, reason }) => (
                <li key={other.slug}>
                  <Link
                    href={other.path}
                    className="flex flex-col gap-0.5 rounded-xl border border-night-rim px-3.5 py-2.5 text-[15px] text-night-ink no-underline hover:border-[#3FDCFF]"
                  >
                    <span className="font-semibold">{other.title}</span>
                    <span className="text-night-chip">{reason}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
}
