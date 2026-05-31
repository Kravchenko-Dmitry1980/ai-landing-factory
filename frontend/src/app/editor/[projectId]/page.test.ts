import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

function source(): string {
  const dir = dirname(fileURLToPath(import.meta.url));
  return readFileSync(join(dir, "page.tsx"), "utf-8");
}

describe("editor route preflight", () => {
  it("uses backend preflight and notFound for missing project", () => {
    const src = source();
    expect(src).toContain("notFound()");
    expect(src).toContain("/projects/${projectId}");
    expect(src).toContain("Editor preflight failed");
  });
});
