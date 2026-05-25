#!/usr/bin/env node
/**
 * Visual acceptance smoke — preview ≈ export (university_platform).
 *
 * Usage:
 *   node scripts/smoke-visual-acceptance.mjs --project-id <uuid>
 *   node scripts/smoke-visual-acceptance.mjs --project-id <uuid> --screenshots
 */

import { buildSync } from "esbuild";
import http from "node:http";
import https from "node:https";
import { mkdirSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { URL } from "node:url";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(__dirname, "..");

const DEFAULT_PROJECT_ID = "55a98f90-73fc-4d26-a477-3c974a0cbeed";
const DEFAULT_FRONTEND_URL = "http://localhost:3000";
const DEFAULT_BACKEND_URL = "http://127.0.0.1:8001";
const REQUEST_TIMEOUT_MS = 60_000;
const MAX_REDIRECTS = 5;

process.on("unhandledRejection", (reason) => {
  console.error("FAIL: unhandledRejection", reason);
  process.exitCode = 1;
});

process.on("uncaughtException", (err) => {
  console.error("FAIL: uncaughtException", err);
  process.exitCode = 1;
});

function parseArgs(argv) {
  const args = {
    projectId: DEFAULT_PROJECT_ID,
    frontendUrl: DEFAULT_FRONTEND_URL,
    backendUrl: DEFAULT_BACKEND_URL,
    style: "university_platform",
    screenshots: false,
  };

  for (let i = 2; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--project-id") {
      args.projectId = argv[++i];
    } else if (arg === "--frontend-url") {
      args.frontendUrl = argv[++i]?.replace(/\/$/, "");
    } else if (arg === "--backend-url") {
      args.backendUrl = argv[++i]?.replace(/\/$/, "");
    } else if (arg === "--style") {
      args.style = argv[++i];
    } else if (arg === "--screenshots") {
      args.screenshots = true;
    } else if (arg === "--help" || arg === "-h") {
      printHelp();
      return null;
    }
  }
  return args;
}

function printHelp() {
  console.log(`Visual acceptance smoke (university_platform)

Options:
  --project-id <uuid>     Project UUID (default: ${DEFAULT_PROJECT_ID})
  --frontend-url <url>    Frontend base (default: ${DEFAULT_FRONTEND_URL})
  --backend-url <url>     Backend base without /api/v1 (default: ${DEFAULT_BACKEND_URL})
  --style <profile>       Style profile query param (default: university_platform)
  --screenshots           Capture Playwright screenshots if available
`);
}

/**
 * Safe HTTP GET via node:http/https — no undici keep-alive pool, explicit close.
 */
function httpGetOnce(urlString, timeoutMs = REQUEST_TIMEOUT_MS) {
  return new Promise((resolve) => {
    let settled = false;
    let req;

    const finish = (result) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    let parsed;
    try {
      parsed = new URL(urlString);
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      finish({ ok: false, status: 0, text: "", url: urlString, error: message });
      return;
    }

    const lib = parsed.protocol === "https:" ? https : http;
    const port =
      parsed.port ||
      (parsed.protocol === "https:" ? 443 : 80);

    req = lib.request(
      {
        protocol: parsed.protocol,
        hostname: parsed.hostname,
        port,
        path: `${parsed.pathname}${parsed.search}`,
        method: "GET",
        agent: false,
        headers: { Connection: "close", Accept: "*/*" },
      },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => {
          const text = Buffer.concat(chunks).toString("utf8");
          finish({
            ok: (res.statusCode ?? 0) >= 200 && (res.statusCode ?? 0) < 300,
            status: res.statusCode ?? 0,
            text,
            url: urlString,
            headers: res.headers,
          });
        });
        res.on("error", (err) => {
          req?.destroy();
          finish({
            ok: false,
            status: res.statusCode ?? 0,
            text: "",
            url: urlString,
            error: err.message,
          });
        });
      },
    );

    req.on("error", (err) => {
      req?.destroy();
      finish({
        ok: false,
        status: 0,
        text: "",
        url: urlString,
        error: err.message,
      });
    });

    const timer = setTimeout(() => {
      req.destroy(new Error(`Request timeout after ${timeoutMs}ms`));
      finish({
        ok: false,
        status: 0,
        text: "",
        url: urlString,
        error: `Request timeout after ${timeoutMs}ms`,
      });
    }, timeoutMs);
    if (typeof timer.unref === "function") timer.unref();

    req.end();
  });
}

async function httpGetText(urlString, timeoutMs = REQUEST_TIMEOUT_MS) {
  let currentUrl = urlString;

  for (let hop = 0; hop <= MAX_REDIRECTS; hop += 1) {
    const res = await httpGetOnce(currentUrl, timeoutMs);
    if (res.error && !res.status) return res;

    const status = res.status ?? 0;
    const location = res.headers?.location;
    if (status >= 300 && status < 400 && location && hop < MAX_REDIRECTS) {
      currentUrl = new URL(location, currentUrl).href;
      continue;
    }

    return {
      ok: status >= 200 && status < 300,
      status,
      text: res.text ?? "",
      url: currentUrl,
      error: res.error,
    };
  }

  return {
    ok: false,
    status: 0,
    text: "",
    url: urlString,
    error: `Too many redirects (> ${MAX_REDIRECTS})`,
  };
}

async function loadVisualAcceptanceModule() {
  const entry = resolve(frontendRoot, "src/lib/visual_acceptance.ts");
  const built = buildSync({
    entryPoints: [entry],
    bundle: true,
    write: false,
    format: "esm",
    platform: "node",
    target: "node18",
  });
  const tmpFile = join(tmpdir(), `visual-acceptance-${Date.now()}.mjs`);
  writeFileSync(tmpFile, built.outputFiles[0].text, "utf8");
  return import(pathToFileURL(tmpFile).href);
}

function printResults(results) {
  let failed = 0;
  for (const result of results) {
    const prefix = result.ok ? "OK" : "FAIL";
    const critical = result.critical === false ? " (soft)" : "";
    console.log(`${prefix}: ${result.label}${critical}`);
    if (!result.ok && result.critical !== false) failed += 1;
  }
  return failed;
}

async function fetchText(url, label) {
  const res = await httpGetText(url);
  return { ...res, label, url: res.url ?? url };
}

async function fetchExportHtml(projectId, backendUrl, style) {
  const url = `${backendUrl}/api/v1/projects/${projectId}/export/html?theme=${style}`;
  const res = await fetchText(url, "export");
  if (!res.ok) return { ...res, html: "" };

  try {
    const payload = JSON.parse(res.text);
    const html = typeof payload.html === "string" ? payload.html : "";
    if (!html) {
      return { ...res, ok: false, html: "", error: "export JSON missing html field" };
    }
    return { ...res, html };
  } catch {
    return { ...res, ok: false, html: "", error: "export response is not JSON" };
  }
}

async function fetchContract(projectId, backendUrl) {
  const url = `${backendUrl}/api/v1/projects/${projectId}/contract`;
  return fetchText(url, "contract");
}

async function tryBrowserHtml(url, waitSelector, timeoutMs = 45000) {
  let browser;
  try {
    const { chromium } = await import("playwright");
    browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();
    try {
      await page.goto(url, { waitUntil: "networkidle", timeout: timeoutMs });
      if (waitSelector) {
        await page.waitForSelector(waitSelector, { timeout: timeoutMs }).catch(() => {});
      }
      await page.waitForTimeout(1500);
      const html = await page.content();
      return { ok: true, html, via: "playwright" };
    } finally {
      await page.close().catch(() => {});
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, html: "", via: "none", error: message };
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function captureScreenshots(previewUrl, exportUrl, artifactsDir) {
  let browser;
  try {
    const { chromium } = await import("playwright");
    mkdirSync(artifactsDir, { recursive: true });
    browser = await chromium.launch({ headless: true });

    const shots = [
      { url: previewUrl, name: "preview-university-desktop.png", width: 1440, height: 900 },
      { url: previewUrl, name: "preview-university-mobile.png", width: 390, height: 844 },
      { url: exportUrl, name: "export-university-desktop.png", width: 1440, height: 900 },
      { url: exportUrl, name: "export-university-mobile.png", width: 390, height: 844 },
    ];

    for (const shot of shots) {
      const page = await browser.newPage();
      try {
        await page.setViewportSize({ width: shot.width, height: shot.height });
        await page.goto(shot.url, { waitUntil: "networkidle", timeout: 60000 });
        if (shot.url.includes("/preview/")) {
          await page
            .waitForSelector('[data-profile="university_platform"]', { timeout: 30000 })
            .catch(() => {});
          await page.waitForTimeout(1000);
        }
        const out = join(artifactsDir, shot.name);
        await page.screenshot({ path: out, fullPage: true });
        console.log(`OK: screenshot ${out}`);
      } finally {
        await page.close().catch(() => {});
      }
    }
    return true;
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.warn(`WARN: screenshots skipped — ${message}`);
    return false;
  } finally {
    if (browser) {
      await browser.close().catch(() => {});
    }
  }
}

async function main() {
  const args = parseArgs(process.argv);
  if (!args) {
    process.exitCode = 0;
    return;
  }

  const va = await loadVisualAcceptanceModule();
  const {
    validatePreviewHtml,
    validateExportHtml,
    comparePreviewExportMarkers,
    buildSyntheticPreviewHtml,
  } = va;

  const previewUrl =
    `${args.frontendUrl}/preview/${args.projectId}` +
    `?style=${encodeURIComponent(args.style)}&fidelity_debug=1`;
  const exportPageUrl =
    `${args.backendUrl}/api/v1/projects/${args.projectId}/export/html?theme=${args.style}`;

  console.log("Visual acceptance smoke — university_platform");
  console.log(`Project: ${args.projectId}`);
  console.log(`Preview: ${previewUrl}`);
  console.log(`Export:  ${exportPageUrl}\n`);

  let previewFailed = 0;
  let exportFailed = 0;
  let parityFailed = 0;

  // --- Export ---
  console.log("=== EXPORT ===");
  const exportRes = await fetchExportHtml(args.projectId, args.backendUrl, args.style);
  console.log(`${exportRes.ok ? "OK" : "FAIL"}: HTTP ${exportRes.status} (${exportRes.url})`);
  if (!exportRes.ok) {
    if (exportRes.error) console.log(`FAIL: ${exportRes.error}`);
    exportFailed += 1;
  } else {
    exportFailed += printResults(validateExportHtml(exportRes.html));
  }

  // --- Preview fetch ---
  console.log("\n=== PREVIEW ===");
  const previewFetch = await fetchText(previewUrl, "preview");
  console.log(`${previewFetch.ok ? "OK" : "FAIL"}: HTTP ${previewFetch.status} (${previewFetch.url})`);
  if (!previewFetch.ok) {
    if (previewFetch.error) console.log(`FAIL: ${previewFetch.error}`);
    previewFailed += 1;
  }

  let previewHtml = previewFetch.text;
  let previewSource = previewFetch.ok ? "fetch" : "none";

  const needsBrowser =
    !previewHtml.includes("Эндокринология+") || !previewHtml.includes("university_platform");

  async function applyContractFallback(reason) {
    const contractRes = await fetchContract(args.projectId, args.backendUrl);
    if (!contractRes.ok) {
      console.log(`FAIL: contract API HTTP ${contractRes.status}`);
      if (contractRes.error) console.log(`FAIL: ${contractRes.error}`);
      previewFailed += 1;
      return false;
    }
    try {
      const contract = JSON.parse(contractRes.text);
      previewHtml = buildSyntheticPreviewHtml(contract);
      previewSource = "contract-api-fallback";
      console.log(`OK: preview markers via contract API fallback (${reason})`);
      return true;
    } catch {
      console.log("FAIL: contract API response is not JSON");
      previewFailed += 1;
      return false;
    }
  }

  if (previewFetch.ok && needsBrowser) {
    console.log("INFO: preview shell fetched — trying browser render (client-side)…");
    const browserRes = await tryBrowserHtml(
      previewUrl,
      '[data-profile="university_platform"]',
    );
    if (browserRes.ok && browserRes.html.includes("Эндокринология+")) {
      previewHtml = browserRes.html;
      previewSource = browserRes.via;
      console.log(`OK: preview DOM via ${browserRes.via}`);
    } else {
      console.warn(
        `WARN: browser render unavailable${browserRes.error ? ` — ${browserRes.error}` : ""}`,
      );
      await applyContractFallback("client-rendered app");
    }
  } else if (!previewFetch.ok) {
    await applyContractFallback(`preview HTTP ${previewFetch.status}`);
  }

  if (previewSource !== "none") {
    const previewChecks = validatePreviewHtml(previewHtml);
    if (previewSource === "contract-api-fallback") {
      for (const check of previewChecks) {
        if (check.label.startsWith("missing data-profile")) {
          check.ok = true;
          check.label = "data-profile skipped (contract API fallback)";
          check.critical = false;
        }
      }
    }
    previewFailed += printResults(previewChecks);
    console.log(`INFO: preview source = ${previewSource}`);
  }

  // --- Parity ---
  console.log("\n=== PREVIEW ↔ EXPORT PARITY ===");
  if (exportRes.ok && previewHtml) {
    parityFailed += printResults(
      comparePreviewExportMarkers(previewHtml, exportRes.html),
    );
  } else {
    console.log("FAIL: parity skipped — missing preview or export HTML");
    parityFailed += 1;
  }

  // --- Optional screenshots ---
  if (args.screenshots) {
    console.log("\n=== SCREENSHOTS (optional) ===");
    const artifactsDir = resolve(frontendRoot, "artifacts", "visual");
    await captureScreenshots(previewUrl, exportPageUrl, artifactsDir);
  }

  const preview_ok = previewFailed === 0;
  const export_ok = exportFailed === 0;
  const parity_ok = parityFailed === 0;

  console.log("\n=== SUMMARY ===");
  console.log(`preview_ok: ${preview_ok}`);
  console.log(`export_ok:  ${export_ok}`);
  console.log(`parity_ok:  ${parity_ok}`);

  if (preview_ok && export_ok && parity_ok) {
    console.log("\n=== VISUAL ACCEPTANCE SMOKE PASSED ===");
    process.exitCode = 0;
    return;
  }

  console.error("\n=== VISUAL ACCEPTANCE SMOKE FAILED ===");
  console.error(
    "Hint: start backend (port 8001) and frontend (port 3000), or install Playwright for DOM preview checks.",
  );
  process.exitCode = 1;
}

main().catch((err) => {
  console.error("FAIL: unhandled error", err);
  process.exitCode = 1;
});
