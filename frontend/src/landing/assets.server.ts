import { readFile } from "node:fs/promises";
import path from "node:path";
import type { LandingAssets } from "./render";

/** Unicode ranges from @fontsource, so browsers fetch only the subset a page needs. */
const LATIN =
  "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD";
const CYRILLIC = "U+0301,U+0400-045F,U+0490-0491,U+04B0-04B1,U+2116";

const FONTS = [
  { family: "Geologica Variable", weight: "100 900", range: CYRILLIC, file: "@fontsource-variable/geologica/files/geologica-cyrillic-wght-normal.woff2" },
  { family: "Geologica Variable", weight: "100 900", range: LATIN, file: "@fontsource-variable/geologica/files/geologica-latin-wght-normal.woff2" },
  { family: "Golos Text", weight: "400", range: CYRILLIC, file: "@fontsource/golos-text/files/golos-text-cyrillic-400-normal.woff2" },
  { family: "Golos Text", weight: "400", range: LATIN, file: "@fontsource/golos-text/files/golos-text-latin-400-normal.woff2" },
  { family: "Golos Text", weight: "600", range: CYRILLIC, file: "@fontsource/golos-text/files/golos-text-cyrillic-600-normal.woff2" },
  { family: "Golos Text", weight: "600", range: LATIN, file: "@fontsource/golos-text/files/golos-text-latin-600-normal.woff2" },
];

let cached: Promise<LandingAssets> | null = null;

async function load(): Promise<LandingAssets> {
  const root = process.cwd();
  const faces = await Promise.all(
    FONTS.map(async (f) => {
      const data = await readFile(path.join(root, "node_modules", f.file));
      return `@font-face{font-family:"${f.family}";font-style:normal;font-display:swap;font-weight:${f.weight};src:url(data:font/woff2;base64,${data.toString(
        "base64",
      )}) format("woff2");unicode-range:${f.range}}`;
    }),
  );
  const [mark, hero] = await Promise.all([
    readFile(path.join(root, "public", "brand", "cat-mark.webp")),
    readFile(path.join(root, "public", "brand", "cat-hero.webp")),
  ]);
  return {
    fontFaces: faces.join(""),
    catMark: `data:image/webp;base64,${mark.toString("base64")}`,
    catHero: `data:image/webp;base64,${hero.toString("base64")}`,
  };
}

/** Fonts and the cat as data URIs: the downloaded page works offline with no other files. */
export function loadLandingAssets(): Promise<LandingAssets> {
  cached ??= load().catch((err) => {
    cached = null;
    throw err;
  });
  return cached;
}
