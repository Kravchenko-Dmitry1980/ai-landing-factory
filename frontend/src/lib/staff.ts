/** Pure helpers for the staff interface (home, building screen, editor). Unit-tested. */

import { ApiRequestError } from "./api-errors";
import type { LandingBlock } from "./types";

/** Plain-Russian error for staff screens: what failed and what to do, never server internals. */
export function staffErrorMessage(err: unknown, action: string): string {
  if (!(err instanceof ApiRequestError)) return `${action}. Попробуйте ещё раз.`;
  const { status } = err;
  if (status === null) return `${action}: нет связи с сервером. Проверьте подключение и попробуйте ещё раз.`;
  if (status === 404) return `${action}: на сервере нет такого лендинга.`;
  if (status === 413) return `${action}: файлы слишком большие для сервера. Уберите часть файлов.`;
  if (status >= 500) return `${action}: сервер не справился. Попробуйте ещё раз через минуту.`;
  return `${action}: сервер не принял данные (код ${status}). Обновите страницу и попробуйте снова.`;
}

/** Whether repeating the same request can help (network trouble or a temporary server failure). */
export function isRetryableError(err: unknown): boolean {
  if (!(err instanceof ApiRequestError)) return true;
  return err.status === null || err.status >= 500;
}

export const ACCEPTED_EXTENSIONS = [".pptx", ".docx", ".pdf", ".txt", ".md"] as const;
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;

/** Blocks the editor does not show as text: the team has its own panel, the tagline is the hero quote. */
export const EDITOR_HIDDEN_BLOCKS = new Set(["team", "tagline"]);

const MONTHS_GENITIVE = [
  "января", "февраля", "марта", "апреля", "мая", "июня",
  "июля", "августа", "сентября", "октября", "ноября", "декабря",
];

function sameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

function hhmm(d: Date): string {
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

/** "Изменён сегодня в 15:24", "Изменён вчера в 09:05", "Изменён 26 июля", "Изменён 3 мая 2025". */
export function formatEditedAt(iso: string, now: Date = new Date()): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "Дата изменения неизвестна";
  if (sameDay(d, now)) return `Изменён сегодня в ${hhmm(d)}`;
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (sameDay(d, yesterday)) return `Изменён вчера в ${hhmm(d)}`;
  const date = `${d.getDate()} ${MONTHS_GENITIVE[d.getMonth()]}`;
  return d.getFullYear() === now.getFullYear() ? `Изменён ${date}` : `Изменён ${date} ${d.getFullYear()}`;
}

/** "Лендинг_АлгоФьюжн_CV.docx" → "Лендинг АлгоФьюжн CV". */
export function projectNameFromFile(fileName: string): string {
  return fileName
    .replace(/\.[^.]+$/, "")
    .replace(/[_\-]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

const TRANSLIT: Record<string, string> = {
  а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "e", ж: "zh", з: "z", и: "i", й: "y",
  к: "k", л: "l", м: "m", н: "n", о: "o", п: "p", р: "r", с: "s", т: "t", у: "u", ф: "f",
  х: "h", ц: "ts", ч: "ch", ш: "sh", щ: "sch", ъ: "", ы: "y", ь: "", э: "e", ю: "yu", я: "ya",
};

/** File-name-safe Latin slug: "Контроль кассы" → "kontrol-kassy". */
export function slugifyRu(text: string, maxLength = 60): string {
  const latin = Array.from(text.toLowerCase())
    .map((ch) => TRANSLIT[ch] ?? ch)
    .join("");
  const slug = latin
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, maxLength)
    .replace(/-+$/g, "");
  return slug || "landing";
}

export function isAcceptedFile(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

/** Error text for the chosen files, or null when they can be uploaded. */
export function validateFiles(files: Pick<File, "name" | "size">[]): string | null {
  if (files.length === 0) return "Добавьте хотя бы один файл: презентацию, документ или отчёт.";
  const rejected = files.filter((f) => !isAcceptedFile(f.name));
  if (rejected.length > 0) {
    return `Этот формат не подходит: ${rejected.map((f) => f.name).join(", ")}. Нужны PPTX, DOCX, PDF или TXT.`;
  }
  const total = files.reduce((sum, f) => sum + f.size, 0);
  if (total > MAX_UPLOAD_BYTES) return "Файлы вместе больше 50 МБ. Уберите часть файлов или сожмите презентацию.";
  return null;
}

export function fileSizeLabel(bytes: number): string {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  return `${(bytes / (1024 * 1024)).toFixed(1).replace(".", ",")} МБ`;
}

export function isBlockEmpty(block: Pick<LandingBlock, "content" | "bullets">): boolean {
  return !block.content.trim() && block.bullets.every((b) => !b.trim());
}

/** Blocks shown as editable text in the editor, in contract order. */
export function editableBlocks(blocks: LandingBlock[]): { block: LandingBlock; index: number }[] {
  return blocks
    .map((block, index) => ({ block, index }))
    .filter(({ block }) => !EDITOR_HIDDEN_BLOCKS.has(block.key));
}

const BLOCK_HINTS: Record<string, string> = {
  essence: "Расскажите в двух-трёх предложениях, что это за проект и какую задачу он решает.",
  purpose: "Перечислите, зачем проект нужен заказчику и что он даёт.",
  tasks: "Перечислите основные задачи или направления работы.",
  inputs: "Опишите, какие данные или материалы получает решение на входе.",
  outputs: "Опишите, что решение выдаёт в результате работы.",
  results: "Добавьте 2–3 результата, лучше с цифрами.",
  outlook: "Напишите, как проект может развиваться дальше.",
  tech_stack: "Перечислите технологии и инструменты, которые использовали.",
};

export function blockHint(key: string): string {
  return BLOCK_HINTS[key] ?? "Напишите пару предложений для этого раздела.";
}

/** A role that looks like a sentence of achievements rather than a job title. */
export function isSuspectRole(role: string | null | undefined): boolean {
  const text = (role ?? "").trim();
  return !text || text.endsWith(".") || text.length > 80;
}

export function replaceAt<T>(items: T[], index: number, value: T): T[] {
  return items.map((item, i) => (i === index ? value : item));
}

export function insertAfter<T>(items: T[], index: number, value: T): T[] {
  return [...items.slice(0, index + 1), value, ...items.slice(index + 1)];
}

export function removeAt<T>(items: T[], index: number): T[] {
  return items.filter((_, i) => i !== index);
}
