import type { Metadata } from "next";
import { LibraryView } from "@/components/library/LibraryView";
import { AppHeader } from "@/components/shell/AppHeader";
import { hasRole, type LibraryPage } from "@/lib/platform";
import { backendFetch, requireUser } from "@/lib/session.server";

export const metadata: Metadata = { title: "Библиотека — Ленд" };

const LIBRARY_TIMEOUT_MS = 10_000;

async function loadLibrary(query: string): Promise<LibraryPage> {
  const res = await backendFetch(`/library${query ? `?q=${encodeURIComponent(query)}` : ""}`, {
    signal: AbortSignal.timeout(LIBRARY_TIMEOUT_MS),
  });
  if (!res.ok) throw new Error(`Library request failed: HTTP ${res.status}`);
  return (await res.json()) as LibraryPage;
}

/** Главная: библиотека опубликованных лендингов, открыта любой учётной записи. */
export default async function LibraryHome({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const raw = (await searchParams).q;
  const query = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  const user = await requireUser(query ? `/?q=${encodeURIComponent(query)}` : "/");

  let library: LibraryPage | null = null;
  let error: string | null = null;
  try {
    library = await loadLibrary(query);
  } catch (err) {
    console.error("Library page: backend request failed", err);
    error = "Не удалось загрузить библиотеку. Обновите страницу через минуту.";
  }

  return (
    <>
      <AppHeader user={user} current="library" />
      <LibraryView
        initialQuery={query}
        initialCards={library?.cards ?? null}
        initialError={error}
        initialTotal={library?.total ?? null}
        canEdit={hasRole(user, "editor")}
      />
    </>
  );
}
