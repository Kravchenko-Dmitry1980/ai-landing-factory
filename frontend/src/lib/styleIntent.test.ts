import { describe, expect, it } from "vitest";
import { parseStyleIntent, UNIVERSITY_DEFAULT_TOKENS } from "./styleIntent";

describe("parseStyleIntent", () => {
  it("parses dark tech blue 3D prompt", () => {
    const tokens = parseStyleIntent(
      "тёмный технологичный стиль с синим акцентом и 3D карточками",
    );
    expect(tokens.color_scheme).toBe("dark");
    expect(tokens.accent).toBe("blue");
    expect(tokens.hero_mode).toBe("future_3d");
    expect(tokens.motion).toBe("expressive");
  });

  it("parses strict corporate light", () => {
    const tokens = parseStyleIntent("строгий корпоративный светлый");
    expect(tokens.color_scheme).toBe("light");
    expect(tokens.density).toBe("normal");
    expect(tokens.motion).toBe("subtle");
  });

  it("returns university defaults for empty prompt", () => {
    expect(parseStyleIntent("")).toEqual(UNIVERSITY_DEFAULT_TOKENS);
    expect(parseStyleIntent("   ")).toEqual(UNIVERSITY_DEFAULT_TOKENS);
  });

  it("ignores raw CSS and script injection attempts", () => {
    const tokens = parseStyleIntent(
      'body { display:none } <script>alert(1)</script>',
    );
    expect(tokens).toEqual(UNIVERSITY_DEFAULT_TOKENS);
    expect(JSON.stringify(tokens)).not.toContain("script");
    expect(JSON.stringify(tokens)).not.toContain("display");
  });
});
