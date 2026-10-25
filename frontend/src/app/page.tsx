import type { Metadata } from "next";
import { LibraryView, MAX_QUERY_CHARS } from "@/components/library/LibraryView";
import { AppHeader } from "@/components/shell/AppHeader";
import { hasRole, type LibrarySearch, type LibraryShelves } from "@/lib/platform";
import { backendFetch, requireUser } from "@/lib/session.server";

export const metadata: Metadata = { title: "Библиотека — Ленд" };

const LIBRARY_TIMEOUT_MS = 10_000;

async function loadJson<T>(path: string, what: string): Promise<T> {
  const res = await backendFetch(path, { signal: AbortSignal.timeout(LIBRARY_TIMEOUT_MS) });
  // `what`, not the path: the path carries the search query, which may hold a person's name.
  if (!res.ok) throw new Error(`Library ${what}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

/** Главная: библиотека опубликованных лендингов, открыта любой учётной записи. */
export default async function LibraryHome({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const raw = (await searchParams).q;
  const query = ((Array.isArray(raw) ? raw[0] : raw) ?? "").trim().slice(0, MAX_QUERY_CHARS);
  const user = await requireUser(query ? `/?q=${encodeURIComponent(query)}` : "/");

  // Independent: a failed search must not take the carousels with it, nor the other way round.
  const [shelvesResult, searchResult] = await Promise.allSettled([
    loadJson<LibraryShelves>("/library/_shelves", "shelves"),
    query ? loadJson<LibrarySearch>(`/library?q=${encodeURIComponent(query)}`, "search") : Promise.resolve(null),
  ]);
  if (shelvesResult.status === "rejected") console.error("Library page: shelves failed", shelvesResult.reason);
  if (searchResult.status === "rejected") console.error("Library page: search failed", searchResult.reason);

  return (
    <div className="min-h-screen bg-night-bg bg-[linear-gradient(rgba(122,164,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(122,164,255,0.05)_1px,transparent_1px)] bg-[length:32px_32px] text-night-ink">
      <AppHeader user={user} current="library" tone="night" />
      <LibraryView
        initialQuery={query}
        initialSearch={searchResult.status === "fulfilled" ? searchResult.value : null}
        initialSearchFailed={searchResult.status === "rejected"}
        shelves={shelvesResult.status === "fulfilled" ? shelvesResult.value : null}
        canEdit={hasRole(user, "editor")}
      />
    </div>
  );
}
