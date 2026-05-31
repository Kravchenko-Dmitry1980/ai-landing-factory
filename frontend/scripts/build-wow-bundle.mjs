#!/usr/bin/env node
/**
 * Build the Interactive WOW Bundle (Stage P.7.5).
 *
 * Bundles the standalone React/R3F app (`src/wow-bundle/main.tsx`) into a single
 * IIFE JS file + CSS, copies the cat mascot PNG, and validates that the output
 * contains the cat-mascot build marker (rejects stale robot bundles).
 *
 * Output:
 *   frontend/dist-wow/assets/wow-app.js
 *   frontend/dist-wow/assets/wow-app.css
 *   frontend/dist-wow/assets/wow/cat-assistant.png
 *
 * Usage:
 *   node scripts/build-wow-bundle.mjs
 *   npm run build:wow-bundle
 */

import { build } from "esbuild";
import { mkdirSync, rmSync, existsSync, statSync, copyFileSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");
const entry = join(frontendRoot, "src", "wow-bundle", "main.tsx");
const outdir = join(frontendRoot, "dist-wow", "assets");

const BUILD_MARKER = "wow-bundle-cat-mascot-v1";
const MASCOT_MARKERS = ["cat-assistant", "wow-hero-mascot", BUILD_MARKER];
const STALE_ROBOT_MARKERS = ["PhoneStage", "function Assistant"];

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function validateBundleJs(jsPath) {
  const text = readFileSync(jsPath, "utf-8");
  for (const marker of MASCOT_MARKERS) {
    if (!text.includes(marker)) {
      fail(`wow-app.js missing mascot marker ${JSON.stringify(marker)}. Source bundle may be stale.`);
    }
  }
  for (const stale of STALE_ROBOT_MARKERS) {
    if (text.includes(stale)) {
      fail(`wow-app.js still contains stale robot marker ${JSON.stringify(stale)}. Rebuild from current source.`);
    }
  }
}

async function main() {
  if (!existsSync(entry)) {
    fail(`entry not found: ${entry}`);
  }

  const catSrc = join(frontendRoot, "public", "assets", "wow", "cat-assistant.png");
  if (!existsSync(catSrc)) {
    fail(`cat mascot asset missing: ${catSrc}`);
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
    alias: {
      "@": join(frontendRoot, "src"),
    },
    logLevel: "info",
  });

  const js = join(outdir, "wow-app.js");
  const css = join(outdir, "wow-app.css");
  const jsKb = existsSync(js) ? Math.round(statSync(js).size / 1024) : 0;
  const cssKb = existsSync(css) ? Math.round(statSync(css).size / 1024) : 0;

  if (!existsSync(js)) {
    fail("wow-app.js was not produced");
  }

  validateBundleJs(js);

  const catOutDir = join(outdir, "wow");
  mkdirSync(catOutDir, { recursive: true });
  const catOut = join(catOutDir, "cat-assistant.png");
  copyFileSync(catSrc, catOut);
  if (!existsSync(catOut)) {
    fail(`failed to copy cat mascot to ${catOut}`);
  }

  console.log(
    `OK: wow-bundle built in ${Date.now() - started}ms — wow-app.js ${jsKb}KB, wow-app.css ${cssKb}KB`,
  );
  console.log(`OK: cat mascot copied to ${catOut}`);
  console.log(`OK: build marker ${BUILD_MARKER} verified in wow-app.js`);
  console.log(`Output: ${outdir}`);
}

main().catch((err) => {
  console.error("FAIL: wow-bundle build error", err);
  process.exit(1);
});
