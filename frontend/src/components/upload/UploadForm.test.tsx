import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";
import {
  appendFilesToFormData,
  mergeFileSelection,
  removeFileAt,
  validateUploadSubmit,
} from "@/lib/uploadFormUtils";

function mockFile(name: string, size = 100): File {
  return new File(["x".repeat(size)], name, { type: "application/octet-stream" });
}

function mockFileList(files: File[]): FileList {
  const list = {
    length: files.length,
    item: (i: number) => files[i] ?? null,
    [Symbol.iterator]: function* () {
      yield* files;
    },
  } as FileList;
  files.forEach((file, index) => {
    Object.defineProperty(list, index, { value: file, enumerable: true });
  });
  return list;
}

describe("UploadForm", () => {
  it("source has file input with multiple attribute", () => {
    const dir = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(dir, "UploadForm.tsx"), "utf-8");
    expect(source).toMatch(/type="file"/);
    expect(source).toMatch(/\bmultiple\b/);
  });
});

describe("uploadFormUtils", () => {
  it("mergeFileSelection adds two distinct files", () => {
    const a = mockFile("01_presentation.pptx");
    const b = mockFile("02_landing.docx");
    const merged = mergeFileSelection([], mockFileList([a, b]));
    expect(merged).toHaveLength(2);
    expect(merged.map((f) => f.name)).toEqual([
      "01_presentation.pptx",
      "02_landing.docx",
    ]);
  });

  it("removeFileAt updates list", () => {
    const a = mockFile("a.pptx");
    const b = mockFile("b.docx");
    const next = removeFileAt([a, b], 0);
    expect(next).toHaveLength(1);
    expect(next[0].name).toBe("b.docx");
  });

  it("appendFilesToFormData sends both files", () => {
    const form = appendFilesToFormData([
      mockFile("a.pptx"),
      mockFile("b.docx"),
    ]);
    const entries = Array.from(form.entries());
    const fileEntries = entries.filter(([key]) => key === "files");
    expect(fileEntries).toHaveLength(2);
  });

  it("validateUploadSubmit blocks empty submit", () => {
    expect(validateUploadSubmit("", [])).toBe("Укажите название проекта");
    expect(validateUploadSubmit("Demo", [])).toBe("Выберите хотя бы один файл");
    expect(validateUploadSubmit("Demo", [mockFile("x.docx")])).toBeNull();
  });
});

describe("uploadMaterials API contract", () => {
  it("submit sends both files to api", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        project_id: "00000000-0000-0000-0000-000000000001",
        files: [],
        message: "ok",
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    const { uploadMaterials } = await import("@/lib/api");
    await uploadMaterials("00000000-0000-0000-0000-000000000001", [
      mockFile("a.pptx"),
      mockFile("b.docx"),
    ]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("POST");
    const body = init.body as FormData;
    const files = Array.from(body.entries()).filter(([k]) => k === "files");
    expect(files).toHaveLength(2);

    vi.unstubAllGlobals();
  });
});
