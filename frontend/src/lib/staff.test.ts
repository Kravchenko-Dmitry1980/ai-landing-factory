import { describe, expect, it } from "vitest";
import { ApiRequestError } from "./api-errors";
import {
  isRetryableError,
  staffErrorMessage,
  editableBlocks,
  fileSizeLabel,
  formatEditedAt,
  insertAfter,
  isBlockEmpty,
  isSuspectRole,
  projectNameFromFile,
  removeAt,
  slugifyRu,
  validateFiles,
} from "./staff";

const NOW = new Date(2026, 9, 24, 16, 0);

describe("formatEditedAt", () => {
  it("names today and yesterday with time", () => {
    expect(formatEditedAt(new Date(2026, 9, 24, 15, 24).toISOString(), NOW)).toBe("Изменён сегодня в 15:24");
    expect(formatEditedAt(new Date(2026, 9, 23, 9, 5).toISOString(), NOW)).toBe("Изменён вчера в 09:05");
  });

  it("shows the year only for previous years", () => {
    expect(formatEditedAt(new Date(2026, 6, 26, 12, 0).toISOString(), NOW)).toBe("Изменён 26 июля");
    expect(formatEditedAt(new Date(2025, 4, 3, 12, 0).toISOString(), NOW)).toBe("Изменён 3 мая 2025");
  });

  it("does not crash on a broken date", () => {
    expect(formatEditedAt("not a date", NOW)).toBe("Дата изменения неизвестна");
  });
});

describe("file helpers", () => {
  it("turns a file name into a project name", () => {
    expect(projectNameFromFile("Лендинг_АлгоФьюжн_CV.docx")).toBe("Лендинг АлгоФьюжн CV");
    expect(projectNameFromFile("report-final.v2.pdf")).toBe("report final.v2");
  });

  it("makes a Latin file slug", () => {
    expect(slugifyRu("Контроль валютно-обменных операций")).toBe("kontrol-valyutno-obmennyh-operatsiy");
    expect(slugifyRu("!!!")).toBe("landing");
  });

  it("validates format and total size", () => {
    expect(validateFiles([])).toMatch(/хотя бы один файл/);
    expect(validateFiles([{ name: "photo.png", size: 10 }])).toMatch(/photo\.png/);
    expect(validateFiles([{ name: "a.PPTX", size: 10 }, { name: "b.docx", size: 10 }])).toBeNull();
    expect(validateFiles([{ name: "big.pdf", size: 51 * 1024 * 1024 }])).toMatch(/50 МБ/);
  });

  it("formats sizes in Russian", () => {
    expect(fileSizeLabel(15_153)).toBe("15 КБ");
    expect(fileSizeLabel(1_258_291)).toBe("1,2 МБ");
  });
});

describe("staff errors", () => {
  it("speaks plain Russian without server internals", () => {
    expect(staffErrorMessage(new ApiRequestError("Failed to fetch", null), "Не удалось сохранить")).toMatch(
      /^Не удалось сохранить: нет связи с сервером/,
    );
    expect(staffErrorMessage(new ApiRequestError("Internal Server Error", 500), "Не удалось сохранить")).toMatch(
      /сервер не справился/,
    );
    expect(staffErrorMessage(new SyntaxError("Unexpected token <"), "Не удалось сохранить")).toBe(
      "Не удалось сохранить. Попробуйте ещё раз.",
    );
    expect(staffErrorMessage(new ApiRequestError("{}", 422), "X")).not.toMatch(/uvicorn|API|422 Unprocessable/);
  });

  it("tells how to recover from an ended session without losing the text on screen", () => {
    const ended = new ApiRequestError(JSON.stringify({ detail: "Войдите в учётную запись." }), 401);
    expect(staffErrorMessage(ended, "Изменения не сохранились")).toMatch(/Войдите в новой вкладке и нажмите «Повторить»/);
    expect(isRetryableError(ended)).toBe(true);
    expect(staffErrorMessage(new ApiRequestError("{}", 403), "X")).toMatch(/нет прав/);
  });

  it("offers a retry only when it can help", () => {
    expect(isRetryableError(new ApiRequestError("x", null))).toBe(true);
    expect(isRetryableError(new ApiRequestError("x", 503))).toBe(true);
    expect(isRetryableError(new ApiRequestError("x", 404))).toBe(false);
    expect(isRetryableError(new ApiRequestError("x", 422))).toBe(false);
  });
});

describe("blocks and team", () => {
  it("treats whitespace-only content and bullets as empty", () => {
    expect(isBlockEmpty({ content: "  ", bullets: ["", " "] })).toBe(true);
    expect(isBlockEmpty({ content: "", bullets: ["пункт"] })).toBe(false);
  });

  it("hides team and tagline blocks but keeps their indexes", () => {
    const blocks = ["essence", "team", "tagline", "results"].map((key) => ({ key, title: key, content: "", bullets: [] }));
    expect(editableBlocks(blocks).map((b) => [b.block.key, b.index])).toEqual([["essence", 0], ["results", 3]]);
  });

  it("flags roles that look like achievements", () => {
    expect(isSuspectRole("Лид Compliance Engine")).toBe(false);
    expect(isSuspectRole("Выполнил сортировку кропов (класс empty), разметку в CVAT.")).toBe(true);
    expect(isSuspectRole("")).toBe(true);
  });

  it("edits bullet lists immutably", () => {
    const items = ["a", "b"];
    expect(insertAfter(items, 0, "x")).toEqual(["a", "x", "b"]);
    expect(removeAt(items, 0)).toEqual(["b"]);
    expect(items).toEqual(["a", "b"]);
  });
});
