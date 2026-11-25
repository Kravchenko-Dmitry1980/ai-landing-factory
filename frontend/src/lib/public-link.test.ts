import { afterEach, describe, expect, it, vi } from "vitest";
import { copyPublicLink, publicLandingUrl } from "./public-link";

const path = `/s/${"a".repeat(43)}`;

afterEach(() => vi.unstubAllGlobals());

describe("publicLandingUrl", () => {
  it("uses the domain of the editor instead of an internal backend or build-time host", () => {
    expect(publicLandingUrl(path, "https://lend.example.org")).toBe(`https://lend.example.org${path}`);
    expect(publicLandingUrl("/s/prognoz-defolta", "https://lend.example.org")).toBe(
      "https://lend.example.org/s/prognoz-defolta",
    );
    expect(publicLandingUrl(path, "http://127.0.0.1:18088")).toBe(`http://127.0.0.1:18088${path}`);
  });

  it("never turns a backend value into a foreign or internal share address", () => {
    for (const bad of [null, undefined, "", "/p/private-page", "//other.example/s/abc", `https://other.example${path}`, `${path}?secret=x`, `${path}/html`]) {
      expect(publicLandingUrl(bad, "https://lend.example.org")).toBeNull();
    }
    expect(publicLandingUrl(path, "file:///course")).toBeNull();
    expect(publicLandingUrl(path, "not an origin")).toBeNull();
  });
});

describe("copyPublicLink", () => {
  it("reports success only after the clipboard accepted the full URL", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    vi.stubGlobal("navigator", { clipboard: { writeText } });
    const url = `https://lend.example.org${path}`;
    expect(await copyPublicLink(url)).toBe(true);
    expect(writeText).toHaveBeenCalledExactlyOnceWith(url);
  });

  it("requests manual copying when HTTP provides no Clipboard API", async () => {
    vi.stubGlobal("navigator", {});
    expect(await copyPublicLink(`http://lend.example.org${path}`)).toBe(false);
  });

  it("requests manual copying when permission is denied, without claiming success", async () => {
    vi.stubGlobal("navigator", { clipboard: { writeText: vi.fn().mockRejectedValue(new Error("NotAllowedError")) } });
    expect(await copyPublicLink(`https://lend.example.org${path}`)).toBe(false);
  });
});
