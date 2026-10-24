"use client";

import { useRouter } from "next/navigation";
import { useId, useState } from "react";
import { createProject, uploadMaterials } from "@/lib/api";
import { rememberLastProject } from "@/lib/lastProject";
import {
  ACCEPTED_EXTENSIONS,
  fileSizeLabel,
  projectNameFromFile,
  staffErrorMessage,
  validateFiles,
} from "@/lib/staff";
import { mergeFileSelection, removeFileAt } from "@/lib/uploadFormUtils";
import { BuildingView, type BuildStep, type StepState } from "./BuildingView";

const STEP_LABELS = ["Создаю проект", "Загружаю и читаю файлы", "Открываю редактор"] as const;

function stepsAt(active: number): BuildStep[] {
  return STEP_LABELS.map((label, i): BuildStep => {
    const state: StepState = i < active ? "done" : i === active ? "active" : "pending";
    return { label, state };
  });
}

/** Upload hero: drop files, name the project, build the page. */
export function NewLanding() {
  const router = useRouter();
  const ids = useId();
  const [files, setFiles] = useState<File[]>([]);
  const [name, setName] = useState("");
  const [nameTouched, setNameTouched] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeStep, setActiveStep] = useState<number | null>(null);
  /** A project created by an attempt whose upload failed: the next attempt reuses it, not a duplicate. */
  const [pendingProjectId, setPendingProjectId] = useState<string | null>(null);

  function addFiles(list: FileList | null) {
    if (!list?.length) return;
    setError(null);
    const next = mergeFileSelection(files, list);
    setFiles(next);
    if (!nameTouched && !name.trim() && next[0]) setName(projectNameFromFile(next[0].name));
  }

  async function handleBuild(e: React.FormEvent) {
    e.preventDefault();
    const fileError = validateFiles(files);
    if (fileError) return setError(fileError);
    if (!name.trim()) return setError("Напишите название проекта: так его будет проще найти в списке.");

    setError(null);
    setActiveStep(0);
    let projectId = pendingProjectId;
    try {
      if (!projectId) {
        projectId = (await createProject(name.trim())).id;
        setPendingProjectId(projectId);
      }
      setActiveStep(1);
      await uploadMaterials(projectId, files);
    } catch (err) {
      console.error("Build failed", projectId, err);
      setActiveStep(null);
      setError(staffErrorMessage(err, "Не удалось собрать страницу"));
      return;
    }
    setActiveStep(2);
    try {
      rememberLastProject(projectId);
    } catch (err) {
      // Remembering the last project is a convenience; a blocked localStorage must not stop the editor.
      console.warn("Could not remember the last project", err);
    }
    router.push(`/editor/${projectId}`);
  }

  if (activeStep !== null) {
    return <BuildingView files={files} steps={stepsAt(activeStep)} />;
  }

  const fileInputId = `${ids}-files`;
  const nameId = `${ids}-name`;

  return (
    <section className="relative flex flex-wrap items-end gap-10 overflow-hidden rounded-3xl border border-line bg-white bg-grid-paper bg-cell p-6 sm:p-12">
      <form onSubmit={handleBuild} noValidate className="flex min-w-0 flex-[999_1_560px] flex-col gap-6">
        <div className="flex flex-col gap-3">
          <h1 className="max-w-[640px] font-display text-[40px] font-semibold leading-[1.05] tracking-[-0.02em] sm:text-[52px]">
            Соберём страницу проекта из ваших материалов
          </h1>
          <p className="max-w-[600px] text-lg leading-relaxed text-fur">
            Загрузите презентацию, текст или отчёт. Через несколько секунд получится лендинг, который можно
            поправить прямо на странице и скачать.
          </p>
        </div>

        <label
          htmlFor={fileInputId}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            addFiles(e.dataTransfer.files);
          }}
          className={`flex cursor-pointer flex-col items-start gap-2 rounded-2xl border-2 border-dashed p-7 transition-colors focus-within:outline focus-within:outline-2 focus-within:outline-scheme ${
            dragging ? "border-scheme bg-scheme-soft" : "border-scheme-line bg-scheme-soft/70 hover:bg-scheme-soft"
          }`}
        >
          <span className="flex items-center gap-3 font-display text-[22px] font-medium">
            <svg aria-hidden="true" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#1E5FD8" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4" />
              <path d="M7 9l5-5 5 5" />
              <path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
            </svg>
            {dragging ? "Отпустите файлы" : "Перетащите файлы сюда"}
          </span>
          <span className="text-base text-fur">
            или <span className="text-scheme underline">выберите на компьютере</span>. Подойдут PPTX, DOCX, PDF и
            TXT, до 50 МБ.
          </span>
          <input
            id={fileInputId}
            type="file"
            multiple
            accept={ACCEPTED_EXTENSIONS.join(",")}
            className="sr-only"
            onChange={(e) => {
              addFiles(e.target.files);
              e.target.value = "";
            }}
          />
        </label>

        {files.length > 0 && (
          <ul aria-label="Выбранные файлы" className="flex flex-col divide-y divide-grid rounded-xl border border-line bg-white">
            {files.map((file, index) => (
              <li key={`${file.name}-${file.size}-${file.lastModified}`} className="flex items-center justify-between gap-3 px-4 py-2.5">
                <span className="min-w-0 truncate text-[15px]">
                  {file.name} <span className="text-fur">{fileSizeLabel(file.size)}</span>
                </span>
                <button
                  type="button"
                  onClick={() => setFiles((prev) => removeFileAt(prev, index))}
                  className="shrink-0 rounded-lg px-2.5 py-1.5 text-sm text-fur hover:bg-paper hover:text-ink"
                >
                  Убрать<span className="sr-only"> файл {file.name}</span>
                </button>
              </li>
            ))}
          </ul>
        )}

        <div className="flex flex-wrap items-end gap-3">
          <div className="flex flex-[1_1_320px] flex-col gap-1.5">
            <label htmlFor={nameId} className="text-[15px] font-medium">
              Название проекта
            </label>
            <input
              id={nameId}
              type="text"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setNameTouched(true);
              }}
              placeholder="Контроль кассовых операций по видео"
              className="h-12 rounded-[10px] border border-field bg-white px-3.5 text-base text-ink placeholder:text-fur/70"
            />
          </div>
          <button
            type="submit"
            className="h-12 rounded-[10px] bg-scheme px-6 text-base font-semibold text-white hover:bg-scheme-hover"
          >
            Собрать страницу
          </button>
        </div>

        {error && (
          <p role="alert" className="text-[15px] text-danger">
            {error}
          </p>
        )}
      </form>

      {/* eslint-disable-next-line @next/next/no-img-element -- статичная иллюстрация */}
      <img
        src="/brand/cat-hero.webp"
        alt="Котик УИИ за ноутбуком"
        width={360}
        height={360}
        className="-mb-12 -mr-2 hidden h-auto w-full max-w-[360px] flex-[1_1_300px] md:block"
      />
    </section>
  );
}
