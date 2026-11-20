"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  getContract,
  getTeamReview,
  patchStyleConfig,
  teamReviewManualText,
  updateContract,
} from "@/lib/api";
import { getApiErrorStatus } from "@/lib/api-errors";
import { fetchLandingFile, landingErrorMessage } from "@/lib/landingFile";
import {
  apiDetail,
  getPublication,
  platformErrorMessage,
  publicationState,
  publishLanding,
  withdrawPublication,
} from "@/lib/platform";
import { descriptionOf, profileForTheme, themeFromContract, type LandingTheme } from "@/landing/model";
import {
  blockHint,
  editableBlocks,
  insertAfter,
  isBlockEmpty,
  isRetryableError,
  isSuspectRole,
  removeAt,
  replaceAt,
  slugifyRu,
  staffErrorMessage,
} from "@/lib/staff";
import type { LandingBlock, LandingContract, TeamReviewData } from "@/lib/types";
import { CatLogoLink } from "@/components/shell/AppHeader";
import { DownloadDialog, saveBlob } from "@/components/shell/DownloadDialog";
import { InlineText } from "./InlineText";
import { PublishPanel, publishButtonLabel, type PublicationLoad } from "./PublishPanel";
import { TeamDialog } from "./TeamDialog";

const SAVE_DELAY_MS = 900;
const SAVE_FAILED_FOR_OUTPUT =
  "Изменения не сохранились, поэтому страница не обновлена. Проверьте подключение и попробуйте ещё раз.";

type SaveState = "idle" | "saving" | "saved" | "error";
type TeamStatus = "loading" | "ok" | "error";

interface Header {
  title: string;
  quote: string;
  client: string;
  timeline: string;
  lead: string;
}

interface Todo {
  label: string;
  targetId: string;
}

/**
 * The hero description is what the site shows under the title. Preview and export read it from the
 * "tagline" block, so the editor shows that block and writes both places on save.
 */
function headerFrom(c: LandingContract): Header {
  const tagline = c.blocks.find((b) => b.key === "tagline")?.content.trim() ?? "";
  const title = c.title ?? "";
  return {
    title,
    // A description that only repeats the title shows as empty, with a marker and a to-do.
    quote: descriptionOf(title, c.quote ?? "", tagline),
    client: c.client ?? "",
    timeline: c.timeline ?? "",
    lead: c.lead ?? "",
  };
}

function blocksWithTagline(blocks: LandingBlock[], quote: string): LandingBlock[] {
  const text = quote.trim();
  // An emptied description must disappear from the page too, not fall back to the old tagline.
  if (!text) return blocks.map((b) => (b.key === "tagline" ? { ...b, content: "" } : b));
  if (blocks.some((b) => b.key === "tagline")) {
    return blocks.map((b) => (b.key === "tagline" ? { ...b, content: text } : b));
  }
  return [...blocks, { key: "tagline", title: "Фраза проекта", content: text, bullets: [] }];
}

function timeLabel(d: Date): string {
  return d.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
}

/** The staff editor: the page itself, edited in place, plus a narrow rail with what to fill in. */
export function StaffEditor({ projectId, projectName = "" }: { projectId: string; projectName?: string }) {
  const router = useRouter();
  const [contract, setContract] = useState<LandingContract | null>(null);
  const [header, setHeader] = useState<Header | null>(null);
  const [blocks, setBlocks] = useState<LandingBlock[]>([]);
  const [team, setTeam] = useState<TeamReviewData | null>(null);
  const [teamStatus, setTeamStatus] = useState<TeamStatus>("loading");
  const [loadError, setLoadError] = useState<{ message: string; noMaterials: boolean } | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  /** stale: someone else saved this landing first; only a reload can bring their text in. */
  const [saveError, setSaveError] = useState<{ message: string; retryable: boolean; stale?: boolean } | null>(null);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [leaving, setLeaving] = useState(false);
  const [downloadOpen, setDownloadOpen] = useState(false);
  const [downloadBusy, setDownloadBusy] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [teamOpen, setTeamOpen] = useState(false);
  const [teamBusy, setTeamBusy] = useState(false);
  const [teamError, setTeamError] = useState<string | null>(null);
  const [themeBusy, setThemeBusy] = useState(false);
  const [themeError, setThemeError] = useState<string | null>(null);
  const [publication, setPublication] = useState<PublicationLoad>({ status: "loading" });
  const [publishBusy, setPublishBusy] = useState<"publish" | "withdraw" | null>(null);
  const [publishError, setPublishError] = useState<string | null>(null);
  const [justPublished, setJustPublished] = useState(false);

  const [editTick, setEditTick] = useState(0);
  const handledTick = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const saveChain = useRef<Promise<boolean>>(Promise.resolve(true));
  const latest = useRef<{ header: Header; blocks: LandingBlock[] } | null>(null);
  /** Edits on screen that the server has not confirmed yet (also true after a failed save). */
  const dirty = useRef(false);
  /** The contract version the screen is based on; every change sends it and gets the next one back. */
  const version = useRef<number | null>(null);
  /**
   * The screen no longer matches the server (someone else saved, or the team changed but did not
   * reload here). Saving it would undo newer text, so saves stop until the page is reloaded.
   */
  const screenStale = useRef(false);

  const adoptVersion = useCallback((next: number | null | undefined) => {
    if (typeof next !== "number") return;
    version.current = next;
    setContract((prev) => (prev ? { ...prev, version: next } : prev));
  }, []);

  const loadPublication = useCallback(async () => {
    setPublication({ status: "loading" });
    try {
      setPublication({ status: "ok", info: await getPublication(projectId) });
    } catch (err) {
      console.error("Publication status failed to load", projectId, err);
      setPublication({ status: "error", message: platformErrorMessage(err, "Не удалось узнать, опубликован ли лендинг") });
    }
  }, [projectId]);

  const loadTeam = useCallback(async () => {
    setTeamStatus("loading");
    try {
      setTeam(await getTeamReview(projectId));
      setTeamStatus("ok");
    } catch (err) {
      console.error("Team review failed to load", projectId, err);
      setTeamStatus("error");
    }
  }, [projectId]);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const data = await getContract(projectId);
      const loaded = headerFrom(data);
      version.current = data.version;
      setContract(data);
      setBlocks(data.blocks);
      if (!loaded.title.trim() && projectName.trim()) {
        // The parser found no title: start from the name the user typed on the home page and save it.
        setHeader({ ...loaded, title: projectName.trim() });
        setEditTick((t) => t + 1);
      } else {
        setHeader(loaded);
      }
    } catch (err) {
      console.error("Contract failed to load", projectId, err);
      // The route already checked that the project exists: a missing contract means no materials.
      const noMaterials = getApiErrorStatus(err) === 404;
      setLoadError({ message: staffErrorMessage(err, "Не удалось открыть лендинг"), noMaterials });
      return;
    }
    void loadTeam();
    void loadPublication();
  }, [projectId, projectName, loadTeam, loadPublication]);

  useEffect(() => {
    void load();
  }, [load]);

  /** Queues a save of the latest committed edits; saves run one after another, never out of order. */
  const persist = useCallback(
    (keepalive = false): Promise<boolean> => {
      const run = async (): Promise<boolean> => {
        const snapshot = latest.current;
        if (!snapshot) return true;
        if (screenStale.current) {
          setSaveError((prev) =>
            prev?.stale
              ? prev
              : { message: "Страница устарела: обновите её, прежде чем править дальше.", retryable: false, stale: true },
          );
          setSaveState("error");
          return false;
        }
        setSaveState("saving");
        try {
          const updated = await updateContract(
            projectId,
            {
              ...snapshot.header,
              blocks: blocksWithTagline(snapshot.blocks, snapshot.header.quote),
              expected_version: version.current ?? undefined,
            },
            { keepalive },
          );
          if (latest.current === snapshot) dirty.current = false;
          version.current = updated.version;
          setContract(updated);
          setSaveState("saved");
          setSaveError(null);
          setActionError(null);
          setSavedAt(new Date());
          return true;
        } catch (err) {
          console.error("Autosave failed", projectId, err);
          const stale = getApiErrorStatus(err) === 409;
          if (stale) screenStale.current = true;
          setSaveError({
            message: stale
              ? (apiDetail(err) ?? "Этот лендинг изменил другой сотрудник. Обновите страницу.")
              : staffErrorMessage(err, "Изменения не сохранились"),
            retryable: !stale && isRetryableError(err),
            stale,
          });
          setSaveState("error");
          return false;
        }
      };
      saveChain.current = saveChain.current.then(run, run);
      return saveChain.current;
    },
    [projectId],
  );

  // After each committed edit: remember exactly what is on screen and restart the save timer.
  useEffect(() => {
    if (editTick === handledTick.current || !header) return;
    handledTick.current = editTick;
    latest.current = { header, blocks };
    dirty.current = true;
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => {
      timer.current = null;
      void persist();
    }, SAVE_DELAY_MS);
  }, [editTick, header, blocks, persist]);

  /** Saves everything not yet confirmed (retrying a failed save); resolves false if it still fails. */
  const flushSave = useCallback((): Promise<boolean> => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    return dirty.current ? persist() : saveChain.current;
  }, [persist]);

  // Closing the tab or reloading: send what is pending and ask the browser to confirm leaving.
  useEffect(() => {
    const onBeforeUnload = (e: BeforeUnloadEvent) => {
      if (!dirty.current) return;
      void persist(true);
      e.preventDefault();
      e.returnValue = "";
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => window.removeEventListener("beforeunload", onBeforeUnload);
  }, [persist]);

  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
      if (dirty.current) void persist(true);
    },
    [persist],
  );

  async function leaveTo(href: string) {
    if (await flushSave()) return router.push(href);
    if (window.confirm("Последние изменения не сохранились. Всё равно уйти со страницы?")) router.push(href);
  }

  function editHeader(patch: Partial<Header>) {
    setHeader((prev) => (prev ? { ...prev, ...patch } : prev));
    setEditTick((t) => t + 1);
  }

  function editBlocks(update: (prev: LandingBlock[]) => LandingBlock[]) {
    setBlocks(update);
    setEditTick((t) => t + 1);
  }

  function editBlock(index: number, patch: Partial<LandingBlock>) {
    editBlocks((prev) => replaceAt(prev, index, { ...prev[index], ...patch }));
  }

  // The page is rendered from the saved contract, so saving pending edits is all it takes.
  async function openPreview() {
    if (leaving) return;
    setLeaving(true);
    setActionError(null);
    if (!(await flushSave())) {
      setActionError(SAVE_FAILED_FOR_OUTPUT);
      setLeaving(false);
      return;
    }
    router.push(`/preview/${projectId}`);
  }

  const fileName = `${slugifyRu(header?.title || contract?.title || "landing")}.html`;

  async function download() {
    if (downloadBusy) return;
    setDownloadBusy(true);
    setDownloadError(null);
    try {
      if (!(await flushSave())) {
        setDownloadError(SAVE_FAILED_FOR_OUTPUT);
        return;
      }
      const file = await fetchLandingFile(projectId);
      saveBlob(new Blob([file.html], { type: "text/html;charset=utf-8" }), file.fileName);
      setDownloadOpen(false);
    } catch (err) {
      console.error("Export failed", projectId, err);
      setDownloadError(landingErrorMessage(err, "Не удалось собрать файл сайта"));
    } finally {
      setDownloadBusy(false);
    }
  }

  /** Saves pending edits, then renders and publishes exactly what is saved. */
  async function publish() {
    if (publishBusy) return;
    setPublishBusy("publish");
    setPublishError(null);
    setJustPublished(false);
    try {
      if (!(await flushSave())) {
        setPublishError(SAVE_FAILED_FOR_OUTPUT);
        return;
      }
      setPublication({ status: "ok", info: await publishLanding(projectId, version.current) });
      setJustPublished(true);
    } catch (err) {
      console.error("Publish failed", projectId, err);
      setPublishError(platformErrorMessage(err, "Не удалось опубликовать лендинг"));
      // A timeout or a lost answer may still have published: show what the library really has.
      void loadPublication();
    } finally {
      setPublishBusy(null);
    }
  }

  async function withdraw() {
    if (publishBusy) return;
    const sure = window.confirm(
      "Снять лендинг с публикации? Он пропадёт из библиотеки, а ссылка для стажёров перестанет открываться. При повторной публикации появится новая ссылка.",
    );
    if (!sure) return;
    setPublishBusy("withdraw");
    setPublishError(null);
    setJustPublished(false);
    try {
      setPublication({ status: "ok", info: await withdrawPublication(projectId) });
    } catch (err) {
      console.error("Withdraw failed", projectId, err);
      setPublishError(platformErrorMessage(err, "Не удалось снять лендинг с публикации"));
    } finally {
      setPublishBusy(null);
    }
  }

  /** After a conflict the screen holds an old version: only a fresh load shows the colleague's text. */
  function reloadAfterConflict() {
    dirty.current = false;
    window.location.reload();
  }

  const theme = contract ? themeFromContract(contract) : "night";

  /**
   * The style endpoint rewrites the whole contract on the server, so it runs in the save queue:
   * after pending text edits, and before any edit typed later.
   */
  async function chooseTheme(next: LandingTheme) {
    if (!contract || themeBusy || next === theme) return;
    setThemeBusy(true);
    setThemeError(null);
    if (!(await flushSave())) {
      setThemeError("Сначала должны сохраниться правки текста, а они не сохранились. Попробуйте ещё раз.");
      setThemeBusy(false);
      return;
    }
    const run = async (): Promise<boolean> => {
      try {
        const result = await patchStyleConfig(
          projectId,
          {
            ...(contract.style_config ?? { profile: profileForTheme(next) }),
            profile: profileForTheme(next),
          },
          version.current ?? undefined,
        );
        setContract((prev) => (prev ? { ...prev, style_config: result.style_config } : prev));
        adoptVersion(result.contract_version);
        return true;
      } catch (err) {
        console.error("Theme change failed", projectId, err);
        setThemeError(
          getApiErrorStatus(err) === 409
            ? (apiDetail(err) ?? "Этот лендинг изменил другой сотрудник. Обновите страницу.")
            : staffErrorMessage(err, "Не удалось сменить оформление"),
        );
        return false;
      }
    };
    saveChain.current = saveChain.current.then(run, run);
    await saveChain.current;
    setThemeBusy(false);
  }

  async function saveTeam(text: string) {
    if (teamBusy) return;
    setTeamBusy(true);
    setTeamError(null);
    // Text edits go first: a pending snapshot saved later would carry the old team block back.
    if (!(await flushSave())) {
      setTeamError("Сначала должны сохраниться правки текста, а они не сохранились. Попробуйте ещё раз.");
      setTeamBusy(false);
      return;
    }
    let failure: unknown = null;
    // In the save queue too: the team change bumps the version that the next text save must send.
    const run = async (): Promise<boolean> => {
      try {
        const result = await teamReviewManualText(projectId, text, version.current ?? undefined);
        adoptVersion(result.contract_version);
        return true;
      } catch (err) {
        failure = err;
        return false;
      }
    };
    saveChain.current = saveChain.current.then(run, run);
    if (!(await saveChain.current)) {
      console.error("Team save failed", projectId, failure);
      setTeamError(
        getApiErrorStatus(failure) === 409
          ? (apiDetail(failure) ?? "Этот лендинг изменил другой сотрудник. Обновите страницу.")
          : staffErrorMessage(failure, "Не удалось сохранить список команды"),
      );
      setTeamBusy(false);
      return;
    }
    setTeamBusy(false);
    setTeamOpen(false);
    try {
      const [review, fresh] = await Promise.all([getTeamReview(projectId), getContract(projectId)]);
      setTeam(review);
      setTeamStatus("ok");
      const freshTeam = fresh.blocks.find((b) => b.key === "team");
      if (freshTeam) setBlocks((prev) => prev.map((b) => (b.key === "team" ? freshTeam : b)));
    } catch (err) {
      console.error("Team refresh failed", projectId, err);
      // The old team block is still on screen; saving it would undo the new team.
      screenStale.current = true;
      setActionError("Команда сохранена, но страница не обновилась. Обновите страницу, прежде чем править дальше.");
    }
  }

  const visible = useMemo(() => editableBlocks(blocks), [blocks]);
  const members = useMemo(
    () => (team?.candidates ?? []).filter((c) => c.status !== "rejected"),
    [team],
  );

  const todos = useMemo((): Todo[] => {
    const list: Todo[] = [];
    if (header && !header.title.trim()) list.push({ label: "Нет заголовка страницы", targetId: "field-title" });
    if (header && !header.quote.trim()) {
      list.push({ label: "Нет короткого описания под заголовком", targetId: "field-quote" });
    }
    for (const { block } of visible) {
      if (isBlockEmpty(block)) {
        list.push({ label: `Раздел «${block.title || "Без названия"}» пустой`, targetId: `block-${block.key}-content` });
      }
    }
    if (teamStatus === "error") {
      list.push({ label: "Команда не загрузилась, проверить её нельзя", targetId: "team-retry" });
    }
    const suspects = members.filter((m) => isSuspectRole(m.role)).map((m) => m.display_name);
    if (suspects.length > 0) {
      list.push({ label: `Проверьте роль: ${suspects.join(", ")}`, targetId: "team-edit" });
    }
    return list;
  }, [header, visible, members, teamStatus]);

  if (loadError) {
    return (
      <div className="min-h-screen">
        <TopBar onLeave={(href) => router.push(href)} />
        <main className="mx-auto flex max-w-[720px] flex-col gap-4 px-6 py-16">
          <h1 className="font-display text-3xl font-semibold">
            {loadError.noMaterials ? "У этого лендинга нет материалов" : "Не удалось открыть лендинг"}
          </h1>
          <p className="text-[17px] text-fur">
            {loadError.noMaterials
              ? "Похоже, загрузка файлов не завершилась. Загрузите материалы проекта заново на главной."
              : loadError.message}
          </p>
          <div className="flex flex-wrap gap-3">
            <Link href="/studio" className="inline-flex h-11 items-center rounded-[10px] border border-field bg-white px-5 text-[15px] text-ink no-underline hover:bg-paper">
              {loadError.noMaterials ? "Загрузить материалы" : "Ваши лендинги"}
            </Link>
            {!loadError.noMaterials && (
              <button type="button" onClick={() => void load()} className="h-11 rounded-[10px] bg-scheme px-5 text-[15px] font-semibold text-white hover:bg-scheme-hover">
                Повторить
              </button>
            )}
          </div>
        </main>
      </div>
    );
  }

  if (!contract || !header) {
    return (
      <div className="min-h-screen">
        <TopBar onLeave={(href) => router.push(href)} />
        <main className="mx-auto max-w-[1200px] px-6 py-16 text-fur">Открываю лендинг…</main>
      </div>
    );
  }

  const publicationInfo = publication.status === "ok" ? publication.info : null;
  const pubState = publicationState(publicationInfo?.status, publicationInfo?.contract_version, contract.version);
  const publishLabel = publishButtonLabel(pubState, Boolean(publicationInfo && !publicationInfo.public_path));

  return (
    <div className="min-h-screen bg-[#EEF1F7]">
      <TopBar title={header.title || contract.title || ""} onLeave={(href) => void leaveTo(href)}>
        {saveState === "error" && (
          <span role="alert" className="flex items-center gap-2 rounded-lg bg-marker px-3 py-1.5 text-sm text-ink">
            {saveError?.stale ? "Лендинг изменил другой сотрудник" : "Изменения не сохранились"}
            {saveError?.stale ? (
              <button type="button" onClick={reloadAfterConflict} className="font-semibold underline">
                Обновить страницу
              </button>
            ) : (
              saveError?.retryable !== false && (
                <button type="button" onClick={() => void persist()} className="font-semibold underline">
                  Повторить
                </button>
              )
            )}
          </span>
        )}
        <button
          type="button"
          onClick={() => void openPreview()}
          disabled={leaving}
          className="h-10 rounded-[10px] border border-field bg-white px-4 text-[15px] text-ink hover:bg-paper disabled:cursor-wait disabled:opacity-70"
        >
          {leaving ? "Сохраняю…" : "Посмотреть как посетитель"}
        </button>
        <button
          type="button"
          onClick={() => {
            setDownloadError(null);
            setDownloadOpen(true);
          }}
          className="h-10 rounded-[10px] border border-field bg-white px-4 text-[15px] text-ink hover:bg-paper"
        >
          Скачать сайт
        </button>
        <button
          type="button"
          onClick={() => void publish()}
          disabled={publishBusy !== null || publishLabel === null}
          className="h-10 rounded-[10px] bg-scheme px-[18px] text-[15px] font-semibold text-white hover:bg-scheme-hover disabled:cursor-default disabled:opacity-60"
        >
          {publishBusy === "publish" ? "Публикую…" : (publishLabel ?? "Опубликовано")}
        </button>
      </TopBar>

      <main>
        <h1 className="sr-only">Редактор лендинга «{header.title || contract.title || "без названия"}»</h1>
        {actionError && (
          <p role="alert" className="mx-4 mt-4 rounded-xl border border-marker-line bg-white px-5 py-3 text-[15px] text-danger sm:mx-6">
            {actionError}
          </p>
        )}

        <div className="flex flex-wrap items-start gap-6 p-4 sm:p-6">
          <article aria-label="Страница лендинга" className="min-w-0 flex-[999_1_640px] overflow-hidden rounded-2xl border border-line bg-white">
            <div className="flex items-center gap-2 border-b border-grid-soft px-6 py-3.5 text-[13px] text-fur sm:px-8">
              {/* eslint-disable-next-line @next/next/no-img-element -- статичный логотип */}
              <img src="/brand/cat-mark.webp" alt="" width={24} height={24} />
              Проект на платформе УИИ
            </div>

            <header className="flex flex-col gap-5 bg-grid-paper bg-cell px-6 pb-8 pt-10 sm:px-12">
              <InlineText
                id="field-title"
                label="Заголовок страницы"
                value={header.title}
                placeholder="Название проекта для заголовка страницы"
                onChange={(title) => editHeader({ title })}
                className={`max-w-[760px] font-display text-[30px] font-semibold leading-[1.08] tracking-[-0.02em] sm:text-[40px] ${
                  header.title.trim() ? "" : "bg-marker"
                }`}
              />
              <InlineText
                id="field-quote"
                label="Короткое описание под заголовком"
                value={header.quote}
                placeholder="Одно-два предложения: что делает проект и для кого"
                onChange={(quote) => editHeader({ quote })}
                className={`max-w-[680px] text-[17px] leading-relaxed ${header.quote.trim() ? "" : "bg-marker"}`}
              />
              <dl className="flex flex-wrap gap-x-8 gap-y-3 text-[15px]">
                <Fact label="Заказчик" value={header.client} onChange={(client) => editHeader({ client })} />
                <Fact label="Сроки" value={header.timeline} onChange={(timeline) => editHeader({ timeline })} />
                <Fact label="Руководитель" value={header.lead} onChange={(lead) => editHeader({ lead })} />
              </dl>
            </header>

            {visible.map(({ block, index }) => (
              <BlockEditor key={block.key} block={block} onChange={(patch) => editBlock(index, patch)} />
            ))}

            <TeamSection
              status={teamStatus}
              members={members}
              onRetry={() => void loadTeam()}
              onEdit={() => {
                setTeamError(null);
                setTeamOpen(true);
              }}
            />
          </article>

          <aside aria-label="Подсказки" className="flex max-w-full flex-[1_1_300px] flex-col gap-4 lg:sticky lg:top-6 lg:max-w-[340px]">
            <PublishPanel
              load={publication}
              state={pubState}
              busy={publishBusy}
              error={publishError}
              justPublished={justPublished}
              onPublish={() => void publish()}
              onWithdraw={() => void withdraw()}
              onRetry={() => void loadPublication()}
            />
            <ThemePicker value={theme} busy={themeBusy} error={themeError} onChange={(t) => void chooseTheme(t)} />
            <section className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-5">
              <h2 className="font-display text-[19px] font-semibold">Что дополнить</h2>
              {todos.length === 0 ? (
                <p className="text-[15px] leading-relaxed text-fur">Всё заполнено. Можно смотреть и публиковать.</p>
              ) : (
                <ul className="flex flex-col gap-2.5">
                  {todos.map((todo) => (
                    <li key={todo.targetId + todo.label}>
                      <button
                        type="button"
                        onClick={() => {
                          const el = document.getElementById(todo.targetId);
                          el?.scrollIntoView({ behavior: "smooth", block: "center" });
                          el?.focus({ preventScroll: true });
                        }}
                        className="flex gap-2.5 text-left text-[15px] leading-snug text-ink hover:text-scheme"
                      >
                        <span aria-hidden="true" className="mt-1.5 h-2.5 w-2.5 flex-none rounded-full bg-marker-dot" />
                        <span>{todo.label}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </section>
            <p aria-live="polite" className="px-1 text-[13px] text-fur">
              <SaveStatus state={saveState} savedAt={savedAt} error={saveError?.message ?? null} />
            </p>
          </aside>
        </div>
      </main>

      <DownloadDialog
        open={downloadOpen}
        fileName={fileName}
        busy={downloadBusy}
        error={downloadError}
        onDownload={() => void download()}
        onClose={() => setDownloadOpen(false)}
      />
      <TeamDialog
        open={teamOpen}
        initialText={team?.editable_text ?? ""}
        busy={teamBusy}
        error={teamError}
        onSave={(text) => void saveTeam(text)}
        onClose={() => setTeamOpen(false)}
      />
    </div>
  );
}

function TopBar({
  title,
  onLeave,
  children,
}: {
  title?: string;
  onLeave: (href: string) => void;
  children?: React.ReactNode;
}) {
  const guard = (href: string) => (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault();
    onLeave(href);
  };
  return (
    <header className="border-b border-grid bg-white">
      <div className="flex flex-wrap items-center gap-4 px-6 py-2.5">
        <CatLogoLink compact onClick={guard("/")} />
        <Link href="/studio" onClick={guard("/studio")} className="text-[15px] text-scheme no-underline hover:text-scheme-hover">
          Ваши лендинги
        </Link>
        <span className="min-w-0 flex-[1_1_200px] truncate text-[15px] font-semibold">{title}</span>
        {children && <div className="flex flex-wrap items-center gap-2.5">{children}</div>}
      </div>
    </header>
  );
}

const THEMES: { value: LandingTheme; label: string; swatch: string }[] = [
  {
    value: "night",
    label: "Ночной",
    swatch:
      "bg-[#0C1222] [background-image:linear-gradient(rgba(122,164,255,.12)_1px,transparent_1px),linear-gradient(90deg,rgba(122,164,255,.12)_1px,transparent_1px)] [background-size:8px_8px]",
  },
  { value: "light", label: "Светлый", swatch: "bg-white bg-grid-paper [background-size:8px_8px]" },
];

function ThemePicker({
  value,
  busy,
  error,
  onChange,
}: {
  value: LandingTheme;
  busy: boolean;
  error: string | null;
  onChange: (t: LandingTheme) => void;
}) {
  return (
    <section className="flex flex-col gap-3 rounded-2xl border border-line bg-white p-5">
      <h2 className="font-display text-[19px] font-semibold">Оформление</h2>
      <div className="grid grid-cols-2 gap-3">
        {THEMES.map((t) => (
          <button
            key={t.value}
            type="button"
            aria-pressed={value === t.value}
            disabled={busy}
            onClick={() => onChange(t.value)}
            className="flex flex-col gap-1.5 text-left text-[15px] disabled:cursor-wait"
          >
            <span
              className={`relative h-16 overflow-hidden rounded-[10px] border-2 ${t.swatch} ${
                value === t.value ? "border-scheme" : "border-line"
              }`}
            >
              <span className="absolute bottom-2 left-2 right-8 h-1.5 rounded bg-[#3FDCFF] shadow-[0_0_8px_#3FDCFF]" />
            </span>
            <span className={value === t.value ? "font-semibold" : ""}>{t.label}</span>
          </button>
        ))}
      </div>
      {error && (
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      )}
    </section>
  );
}

function TeamSection({
  status,
  members,
  onRetry,
  onEdit,
}: {
  status: TeamStatus;
  members: TeamReviewData["candidates"];
  onRetry: () => void;
  onEdit: () => void;
}) {
  return (
    <section id="team" aria-labelledby="team-title" className="flex flex-col gap-4 border-t border-grid-soft px-6 py-8 sm:px-12">
      <div className="flex flex-wrap items-baseline gap-3">
        <h2 id="team-title" className="font-display text-[26px] font-semibold">
          Команда
        </h2>
        {status === "ok" && (
          <span className="text-[15px] text-fur">{members.length > 0 ? `${members.length} чел.` : "не найдена в материалах"}</span>
        )}
      </div>
      {status === "loading" && <p className="text-[15px] text-fur">Загружаю команду…</p>}
      {status === "error" && (
        <div role="alert" className="flex flex-wrap items-center gap-3 text-[15px]">
          <span>Не удалось загрузить команду. Список не изменён.</span>
          <button id="team-retry" type="button" onClick={onRetry} className="h-10 rounded-lg border border-field bg-white px-4 hover:bg-paper">
            Повторить
          </button>
        </div>
      )}
      {status === "ok" && members.length > 0 && (
        <ul className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-x-8 gap-y-3">
          {members.map((m) => (
            <li key={m.id} className="flex flex-col">
              <span className="font-semibold">{m.display_name}</span>
              <span className={`text-sm leading-snug ${isSuspectRole(m.role) ? "self-start rounded bg-marker px-1" : "text-fur"}`}>
                {m.role?.trim() || "Роль не указана"}
              </span>
            </li>
          ))}
        </ul>
      )}
      {status === "ok" && (
        <div>
          <button id="team-edit" type="button" onClick={onEdit} className="h-10 rounded-lg border border-field bg-white px-4 text-[15px] hover:bg-paper">
            {members.length > 0 ? "Изменить список" : "Добавить команду"}
          </button>
        </div>
      )}
    </section>
  );
}

function Fact({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="flex min-w-[180px] flex-col">
      <dt className="text-fur">{label}</dt>
      <dd className="m-0 font-medium">
        <InlineText label={label} value={value} placeholder="Не указано" onChange={onChange} />
      </dd>
    </div>
  );
}

function BlockEditor({ block, onChange }: { block: LandingBlock; onChange: (patch: Partial<LandingBlock>) => void }) {
  const empty = isBlockEmpty(block);
  const name = block.title || "раздела";

  function focusBullet(i: number) {
    requestAnimationFrame(() => document.getElementById(`block-${block.key}-b${i}`)?.focus());
  }

  function onBulletKey(i: number, e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onChange({ bullets: insertAfter(block.bullets, i, "") });
      focusBullet(i + 1);
    } else if (e.key === "Backspace" && block.bullets[i] === "" && block.bullets.length > 0) {
      e.preventDefault();
      onChange({ bullets: removeAt(block.bullets, i) });
      if (i > 0) focusBullet(i - 1);
    }
  }

  return (
    <section
      aria-label={block.title || "Раздел без названия"}
      className={`flex flex-col gap-3 border-t border-grid-soft px-6 py-8 sm:px-12 ${empty ? "bg-[#FFF7F8]" : ""}`}
    >
      <InlineText
        label={`Заголовок раздела «${name}»`}
        value={block.title}
        placeholder="Заголовок раздела"
        onChange={(title) => onChange({ title })}
        className={`max-w-[700px] font-display text-[24px] font-semibold leading-tight sm:text-[26px] ${empty ? "self-start bg-marker" : ""}`}
      />
      {(block.content || empty || block.bullets.length === 0) && (
        <InlineText
          id={`block-${block.key}-content`}
          label={`Текст раздела «${name}»`}
          value={block.content}
          placeholder={blockHint(block.key)}
          onChange={(content) => onChange({ content })}
          className="max-w-[700px] text-base leading-relaxed"
        />
      )}
      {block.bullets.length > 0 && (
        <ul className="flex max-w-[700px] list-disc flex-col gap-1.5 pl-5 text-base leading-relaxed marker:text-scheme">
          {block.bullets.map((bullet, i) => (
            <li key={i}>
              <InlineText
                id={`block-${block.key}-b${i}`}
                label={`Пункт ${i + 1} раздела «${name}»`}
                value={bullet}
                placeholder="Новый пункт"
                onChange={(value) => onChange({ bullets: replaceAt(block.bullets, i, value) })}
                onKeyDown={(e) => onBulletKey(i, e)}
              />
            </li>
          ))}
        </ul>
      )}
      <div>
        <button
          type="button"
          onClick={() => {
            onChange({ bullets: [...block.bullets, ""] });
            focusBullet(block.bullets.length);
          }}
          className="rounded-md px-1.5 py-1 text-sm text-fur hover:bg-scheme-soft hover:text-scheme"
        >
          Добавить пункт
        </button>
      </div>
    </section>
  );
}

function SaveStatus({ state, savedAt, error }: { state: SaveState; savedAt: Date | null; error: string | null }) {
  if (state === "saving") return <>Сохраняю…</>;
  if (state === "error") return <span className="text-danger">{error ?? "Изменения не сохранились."}</span>;
  if (state === "saved" && savedAt) return <>Изменения сохраняются сами, последнее в {timeLabel(savedAt)}.</>;
  return <>Изменения сохраняются сами.</>;
}
