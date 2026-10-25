import Link from "next/link";
import { formatDate, type PublicationInfo, type PublicationState } from "@/lib/platform";

export type PublicationLoad =
  | { status: "loading" }
  | { status: "ok"; info: PublicationInfo | null }
  | { status: "error"; message: string };

/** Label of the main publish button for each state; null: nothing new to publish. */
export function publishButtonLabel(state: PublicationState): string | null {
  if (state === "published") return null;
  if (state === "outdated") return "Обновить в библиотеке";
  return "Опубликовать";
}

function byline(info: PublicationInfo): string {
  return [formatDate(info.published_at), info.published_by_name].filter(Boolean).join(", ");
}

/** Боковой блок редактора: есть ли лендинг в библиотеке, какая версия там видна, снять с публикации. */
export function PublishPanel({
  load,
  state,
  busy,
  error,
  justPublished,
  onWithdraw,
  onRetry,
}: {
  load: PublicationLoad;
  state: PublicationState;
  busy: "publish" | "withdraw" | null;
  error: string | null;
  justPublished: boolean;
  onWithdraw: () => void;
  onRetry: () => void;
}) {
  const info = load.status === "ok" ? load.info : null;
  return (
    <section aria-labelledby="publish-title" className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-5">
      <h2 id="publish-title" className="font-display text-[19px] font-semibold">
        Библиотека
      </h2>

      {load.status === "loading" && <p className="text-[15px] text-fur">Проверяю, опубликован ли лендинг…</p>}

      {load.status === "error" && (
        <div className="flex flex-col items-start gap-2 text-[15px]">
          <p className="text-danger">{load.message}</p>
          <button type="button" onClick={onRetry} className="font-semibold text-scheme underline">
            Повторить
          </button>
        </div>
      )}

      {load.status === "ok" && (
        <div aria-live="polite" className="flex flex-col gap-2 text-[15px] leading-relaxed">
          {state === "none" && (
            <p className="text-fur">
              Сейчас лендинг видят только редакторы в студии. После публикации его найдут все сотрудники в библиотеке.
            </p>
          )}
          {info && state === "published" && (
            <>
              {justPublished && <p className="font-semibold text-ok">Опубликовано. Коллеги уже видят лендинг.</p>}
              <p className="text-fur">
                В библиотеке версия {info.version} от {byline(info)}. Она совпадает с тем, что на экране.
              </p>
            </>
          )}
          {info && state === "outdated" && (
            <p className="rounded-lg bg-marker px-3 py-2 text-ink">
              В библиотеке версия от {formatDate(info.published_at)}. Последние правки появятся там, когда вы обновите
              публикацию.
            </p>
          )}
          {info && state === "withdrawn" && (
            <p className="text-fur">
              Снят с публикации{info.withdrawn_at ? ` ${formatDate(info.withdrawn_at)}` : ""}. Ссылка не открывается,
              пока лендинг не опубликуют снова, адрес сохранится прежним.
            </p>
          )}
          {info && state !== "withdrawn" && (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-2 pt-1">
              <Link href={info.path} className="font-semibold text-scheme">
                Открыть в библиотеке
              </Link>
              <button
                type="button"
                onClick={onWithdraw}
                disabled={busy !== null}
                className="text-fur underline hover:text-danger disabled:opacity-60"
              >
                {busy === "withdraw" ? "Снимаю…" : "Снять с публикации"}
              </button>
            </div>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="text-[15px] text-danger">
          {error}
        </p>
      )}
    </section>
  );
}
