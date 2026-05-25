#!/usr/bin/env node
/**
 * Free a TCP port before `next dev` — avoids stale/zombie Next.js on Windows.
 * Usage: node scripts/ensure-port-free.mjs [--port 3000]
 */

import { execSync } from "node:child_process";
import net from "node:net";

const DEFAULT_PORT = 3000;

function parsePort(argv) {
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === "--port" && argv[i + 1]) {
      return Number(argv[i + 1]);
    }
  }
  return DEFAULT_PORT;
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.unref();
    server.on("error", () => resolve(false));
    server.listen({ port, host: "127.0.0.1" }, () => {
      server.close(() => resolve(true));
    });
  });
}

function findListeningPids(port) {
  if (process.platform !== "win32") {
    try {
      const out = execSync(`lsof -ti :${port}`, { encoding: "utf8" }).trim();
      return out ? out.split(/\s+/).map(Number).filter(Boolean) : [];
    } catch {
      return [];
    }
  }

  try {
    const out = execSync(`netstat -ano | findstr ":${port}"`, { encoding: "utf8" });
    const pids = new Set();
    for (const line of out.split(/\r?\n/)) {
      if (!line.includes("LISTENING")) continue;
      const parts = line.trim().split(/\s+/);
      const pid = Number(parts[parts.length - 1]);
      if (pid > 0) pids.add(pid);
    }
    return [...pids];
  } catch {
    return [];
  }
}

function processName(pid) {
  if (process.platform !== "win32") return "unknown";
  try {
    const out = execSync(`tasklist /FI "PID eq ${pid}" /FO CSV /NH`, { encoding: "utf8" });
    const match = out.match(/"([^"]+)"/);
    return match ? match[1].toLowerCase() : "unknown";
  } catch {
    return "unknown";
  }
}

function killPid(pid) {
  if (process.platform === "win32") {
    execSync(`taskkill /PID ${pid} /F`, { stdio: "ignore" });
  } else {
    execSync(`kill -9 ${pid}`, { stdio: "ignore" });
  }
}

async function main() {
  const port = parsePort(process.argv);
  if (!Number.isFinite(port) || port <= 0) {
    console.error("FAIL: invalid port");
    process.exitCode = 1;
    return;
  }

  if (await isPortFree(port)) {
    console.log(`Port ${port} is free`);
    return;
  }

  const pids = findListeningPids(port);
  if (pids.length === 0) {
    console.warn(`WARN: port ${port} busy but no LISTENING PID found — continuing`);
    return;
  }

  let killed = 0;
  for (const pid of pids) {
    const name = processName(pid);
    const isNode = name.includes("node");
    if (!isNode) {
      console.error(
        `FAIL: port ${port} is used by ${name} (PID ${pid}). Stop it manually before npm run dev.`,
      );
      process.exitCode = 1;
      return;
    }
    console.warn(`WARN: killing stale ${name} on port ${port} (PID ${pid})`);
    try {
      killPid(pid);
      killed += 1;
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      console.error(`FAIL: could not kill PID ${pid}: ${message}`);
      process.exitCode = 1;
      return;
    }
  }

  await new Promise((r) => setTimeout(r, 800));

  if (await isPortFree(port)) {
    console.log(`Port ${port} freed (${killed} process(es) stopped)`);
    return;
  }

  console.error(`FAIL: port ${port} still busy after cleanup`);
  process.exitCode = 1;
}

main().catch((err) => {
  console.error("FAIL:", err);
  process.exitCode = 1;
});
