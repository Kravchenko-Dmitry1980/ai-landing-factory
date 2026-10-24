import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it, vi } from "vitest";
import { mergeFileSelection, removeFileAt } from "@/lib/uploadFormUtils";

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

describe("NewLanding upload form", () => {
  it("source has a multi-file input", () => {
    const dir = dirname(fileURLToPath(import.meta.url));
    const source = readFileSync(join(dir, "../components/home/NewLanding.tsx"), "utf-8");
    expect(source).toMatch(/type="file"/);
    expect(source).toMatch(/\bmultiple\b/);
  });
});

describe("uploadFormUtils", () => {
  it("mergeFileSelection adds two distinct files", () => {
    const a = mockFile("01_presentation.pptx");
    const b = mockFile("02_landing.docx");
    const merged = mergeFileSelection([], mockFileList([a, b]));
    expect(merged.map((f) => f.name)).toEqual(["01_presentation.pptx", "02_landing.docx"]);
  });

  it("mergeFileSelection skips a file chosen twice", () => {
    const a = mockFile("a.pptx");
    expect(mergeFileSelection([a], mockFileList([a]))).toHaveLength(1);
  });

  it("removeFileAt updates list", () => {
    const next = removeFileAt([mockFile("a.pptx"), mockFile("b.docx")], 0);
    expect(next.map((f) => f.name)).toEqual(["b.docx"]);
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
    await uploadMaterials("00000000-0000-0000-0000-000000000001", [mockFile("a.pptx"), mockFile("b.docx")]);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.method).toBe("POST");
    const files = Array.from((init.body as FormData).entries()).filter(([k]) => k === "files");
    expect(files).toHaveLength(2);

    vi.unstubAllGlobals();
  });
});
