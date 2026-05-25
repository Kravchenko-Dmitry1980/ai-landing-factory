#!/usr/bin/env node
/**
 * Smoke-check frontend → backend API connectivity.
 * Usage: node scripts/smoke-api.mjs
 */

import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const root = resolve(__dirname, "..");

function loadApiBase() {
  const envPath = resolve(root, ".env.local");
  if (existsSync(envPath)) {
    for (const line of readFileSync(envPath, "utf8").split(/\r?\n/)) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eq = trimmed.indexOf("=");
      if (eq === -1) continue;
      const key = trimmed.slice(0, eq).trim();
      const value = trimmed.slice(eq + 1).trim();
      if (key === "NEXT_PUBLIC_API_URL" && value) {
        return value.replace(/\/$/, "");
      }
    }
  }
  return (process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001/api/v1").replace(
    /\/$/,
    "",
  );
}

const apiBase = loadApiBase();
const target = `${apiBase}/projects/privacy`;

console.log("NEXT_PUBLIC_API_URL (resolved):", apiBase);
console.log("GET", target);

try {
  const res = await fetch(target, { method: "GET" });
  console.log("Status:", res.status, res.statusText);

  if (res.status === 200) {
    const body = await res.json();
    console.log("OK — privacy_mode:", body.privacy_mode ?? "(unknown)");
    process.exit(0);
  }

  if (res.status === 404) {
    console.error(
      "FAIL: 404 Not Found. Проверьте:\n" +
        "  1) NEXT_PUBLIC_API_URL включает /api/v1\n" +
        "  2) backend запущен на правильном порту\n" +
        "  3) privacy router зарегистрирован первым в api/router.py",
    );
    process.exit(1);
  }

  const text = await res.text();
  console.error("FAIL: unexpected status. Body:", text.slice(0, 200));
  process.exit(1);
} catch (err) {
  console.error(
    "FAIL: backend недоступен.",
    err instanceof Error ? err.message : err,
  );
  console.error("Запустите: cd backend && ..\\.venv\\Scripts\\uvicorn.exe app.main:app --port 8001");
  process.exit(1);
}
