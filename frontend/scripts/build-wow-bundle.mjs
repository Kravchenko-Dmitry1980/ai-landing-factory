#!/usr/bin/env node
/**
 * Build the Interactive WOW Bundle (Stage P.7.2).
 *
 * Bundles the standalone React/R3F app (`src/wow-bundle/main.tsx`) into a single
 * IIFE JS file + CSS, so it runs offline from `file://` with no module loading
 * restrictions, no dev server, no backend and no CDN.
 *
 * Output:
 *   frontend/dist-wow/assets/wow-app.js
 *   frontend/dist-wow/assets/wow-app.css
 *
 * Usage:
 *   node scripts/build-wow-bundle.mjs
 *   npm run build:wow-bundle
 */

import { build } from "esbuild";
import { mkdirSync, rmSync, existsSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const entry = join(frontendRoot, "src", "wow-bundle", "main.tsx");
const outdir = join(frontendRoot, "dist-wow", "assets");

async function main() {
  if (!existsSync(entry)) {
    console.error(`FAIL: entry not found: ${entry}`);
    process.exit(1);
  }

  // Clean previous output so stale chunks never ship inside a ZIP.
  rmSync(join(frontendRoot, "dist-wow"), { recursive: true, force: true });
  mkdirSync(outdir, { recursive: true });

  const started = Date.now();
  await build({
    entryPoints: { "wow-app": entry },
    bundle: true,
    format: "iife",
    platform: "browser",
    target: ["es2019"],
    outdir,
    minify: true,
    sourcemap: false,
    jsx: "automatic",
    legalComments: "none",
    loader: { ".css": "css" },
    define: { "process.env.NODE_ENV": '"production"' },
    logLevel: "info",
  });

  const js = join(outdir, "wow-app.js");
  const css = join(outdir, "wow-app.css");
  const jsKb = existsSync(js) ? Math.round(statSync(js).size / 1024) : 0;
  const cssKb = existsSync(css) ? Math.round(statSync(css).size / 1024) : 0;

  if (!existsSync(js)) {
    console.error("FAIL: wow-app.js was not produced");
    process.exit(1);
  }

  console.log(
    `OK: wow-bundle built in ${Date.now() - started}ms — wow-app.js ${jsKb}KB, wow-app.css ${cssKb}KB`,
  );
  console.log(`Output: ${outdir}`);
}

main().catch((err) => {
  console.error("FAIL: wow-bundle build error", err);
  process.exit(1);
});
