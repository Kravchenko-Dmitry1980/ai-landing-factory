"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { formatDate, type PublicationInfo, type PublicationState } from "@/lib/platform";
import { copyPublicLink, publicLandingUrl } from "@/lib/public-link";

export type PublicationLoad =
  | { status: "loading" }
  | { status: "ok"; info: PublicationInfo | null }
  | { status: "error"; message: string };

/** Keep older publications private until an editor explicitly creates their share link. */
export function publishButtonLabel(state: PublicationState, needsPublicLink = false): string | null {
  if (state === "published") return needsPublicLink ? "Создать ссылку для стажёра" : null;
  if (state === "outdated") return "Обновить в библиотеке";
  return "Опубликовать";
}

function byline(info: PublicationInfo): string {
  return [formatDate(info.published_at), info.published_by_name].filter(Boolean).join(", ");
}

/** Публикация, ссылка для стажёра и снятие страницы с публикации. */
export function PublishPanel({
  load,
  state,
  busy,
  error,
  justPublished,
  onPublish,
  onWithdraw,
  onRetry,
}: {
  load: PublicationLoad;
  state: PublicationState;
  busy: "publish" | "withdraw" | null;
  error: string | null;
  justPublished: boolean;
  onPublish: () => void;
  onWithdraw: () => void;
  onRetry: () => void;
}) {
  const info = load.status === "ok" ? load.info : null;
  const publicPath = info?.status === "published" ? info.public_path : null;
  const [origin, setOrigin] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "copied" | "manual">("idle");
  const [copyBusy, setCopyBusy] = useState(false);
  const linkInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    setOrigin(window.location.origin);
  }, []);
  useEffect(() => {
    setCopyState("idle");
  }, [publicPath]);
  const publicUrl = publicLandingUrl(publicPath, origin);

  async function copyLink() {
    if (!publicUrl || copyBusy) return;
    setCopyBusy(true);
    const copied = await copyPublicLink(publicUrl);
    setCopyBusy(false);
    setCopyState(copied ? "copied" : "manual");
    if (!copied) {
      linkInput.current?.focus();
      linkInput.current?.select();
    }
  }
  return (
    <section aria-labelledby="publish-title" className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-5">
      <h2 id="publish-title" className="font-display text-[19px] font-semibold">
        Публикация и ссылка
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
              Сейчас лендинг видят только редакторы в студии. После публикации появится ссылка для стажёров: по ней страницу можно открыть без пароля.
            </p>
          )}
          {info && state === "published" && (
            <>
              {justPublished && <p className="font-semibold text-ok">Опубликовано. Можно отправить ссылку стажёру.</p>}
              <p className="text-fur">
                В библиотеке версия {info.version} от {byline(info)}. Она совпадает с тем, что на экране.
              </p>
            </>
          )}
          {info && state === "outdated" && (
            <p className="rounded-lg bg-marker px-3 py-2 text-ink">
              {publicPath ? "В библиотеке и по ссылке" : "В библиотеке"} версия от {formatDate(info.published_at)}. Последние правки появятся после обновления публикации.
            </p>
          )}
          {info && state === "withdrawn" && (
            <p className="text-fur">
              Снят с публикации{info.withdrawn_at ? ` ${formatDate(info.withdrawn_at)}` : ""}. Ссылка для стажёров больше не открывается. При повторной публикации появится новая ссылка.
            </p>
          )}
          {info && state !== "withdrawn" && (
            <>
            {publicUrl && (
              <div className="flex flex-col gap-2 rounded-xl border border-line bg-paper p-3">
                <label htmlFor="public-landing-link" className="font-semibold text-ink">Ссылка для стажёра</label>
                <input
                  ref={linkInput}
                  id="public-landing-link"
                  type="url"
                  readOnly
                  value={publicUrl}
                  onFocus={(event) => event.currentTarget.select()}
                  aria-describedby="public-link-help"
                  className="min-w-0 w-full rounded-lg border border-field bg-white px-2.5 py-2 text-[14px] text-ink"
                />
                <button
                  type="button"
                  onClick={() => void copyLink()}
                  disabled={copyBusy || busy !== null}
                  className="rounded-lg bg-scheme px-3 py-2 font-semibold text-white hover:bg-scheme-hover disabled:opacity-60"
                >
                  {copyBusy ? "Копирую…" : "Скопировать ссылку"}
                </button>
                <p id="public-link-help" className="text-[14px] text-fur">Откроется без пароля у любого, кому передадут эту ссылку. Библиотека и редактор остаются закрытыми.</p>
                <a href={publicUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-scheme">Открыть страницу ↗</a>
                <p role="status" className={`text-[14px] ${copyState === "copied" ? "text-ok" : "text-fur"}`}>
                  {copyState === "copied" && "Ссылка скопирована. Отправьте её стажёру."}
                  {copyState === "manual" && "Ссылка выделена. Нажмите Ctrl+C или выберите «Копировать» в меню поля."}
                </p>
              </div>
            )}
            {!publicPath && (
              <div className="flex flex-col gap-2 rounded-xl bg-marker p-3">
                <p>Эта публикация пока доступна только сотрудникам. Создайте ссылку, чтобы стажёры могли открыть страницу без пароля.</p>
                <button type="button" onClick={onPublish} disabled={busy !== null} className="rounded-lg bg-scheme px-3 py-2 font-semibold text-white hover:bg-scheme-hover disabled:opacity-60">
                  {busy === "publish" ? "Публикую…" : state === "outdated" ? "Обновить и создать ссылку" : "Создать ссылку для стажёра"}
                </button>
              </div>
            )}
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
            </>
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
