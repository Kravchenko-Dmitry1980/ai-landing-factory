import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

function source(file: string): string {
  const dir = dirname(fileURLToPath(import.meta.url));
  return readFileSync(join(dir, file), "utf-8");
}

describe("LandingEditor runtime guards", () => {
  it("renders friendly missing-project actions", () => {
    const src = source("LandingEditor.tsx");
    expect(src).toContain("Не удалось открыть проект");
    expect(src).toContain("Проект не найден");
    expect(src).toContain("Вернуться к списку");
    expect(src).toContain("Повторить");
  });

  it("does not import R3F or WOW bundle modules", () => {
    const src = source("LandingEditor.tsx");
    expect(src).not.toContain("@react-three/fiber");
    expect(src).not.toContain("src/wow-bundle");
    expect(src).not.toContain("components/wow");
  });
});
