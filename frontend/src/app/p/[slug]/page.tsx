import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { CatLogoLink } from "@/components/shell/AppHeader";
import { formatDate, hasRole, type LibraryCard } from "@/lib/platform";
import { backendFetch, requireUser } from "@/lib/session.server";

type Props = { params: Promise<{ slug: string }> };

async function loadCard(slug: string): Promise<LibraryCard | null> {
  const res = await backendFetch(`/library/${encodeURIComponent(slug)}`, { signal: AbortSignal.timeout(10_000) });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Library card request failed: HTTP ${res.status}`);
  return (await res.json()) as LibraryCard;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const card = await loadCard(slug).catch(() => null);
  return { title: card ? `${card.title} — Ленд` : "Лендинг — Ленд" };
}

/** Опубликованный лендинг: узкая полоса библиотеки сверху, сама страница в изолированной рамке. */
export default async function PublishedPage({ params }: Props) {
  const { slug } = await params;
  const user = await requireUser(`/p/${slug}`);
  const card = await loadCard(slug);
  if (!card) notFound();

  const byline = [card.published_by_name, formatDate(card.published_at)].filter(Boolean).join(", ");
  const raw = `/p/${encodeURIComponent(card.slug)}/raw`;

  return (
    <div className="flex h-screen flex-col bg-paper">
      <header className="border-b border-grid bg-white">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-2 px-6 py-2.5">
          <CatLogoLink compact />
          <Link href="/" className="text-[15px] text-scheme no-underline hover:text-scheme-hover">
            Библиотека
          </Link>
          <div className="flex min-w-0 flex-[1_1_240px] flex-col">
            <span className="truncate text-[15px] font-semibold">{card.title}</span>
            {byline && <span className="truncate text-[13px] text-fur">Опубликовано: {byline}</span>}
          </div>
          <div className="flex flex-wrap items-center gap-2.5">
            {hasRole(user, "editor") && (
              <Link
                href={`/editor/${card.project_id}`}
                className="inline-flex h-10 items-center rounded-[10px] border border-field bg-white px-4 text-[15px] text-ink no-underline hover:bg-paper"
              >
                Править в студии
              </Link>
            )}
            <a
              href={raw}
              target="_blank"
              rel="noopener"
              className="inline-flex h-10 items-center rounded-[10px] border border-field bg-white px-4 text-[15px] text-ink no-underline hover:bg-paper"
            >
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
  );
}
