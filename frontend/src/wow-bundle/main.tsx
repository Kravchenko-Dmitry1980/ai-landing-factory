/**
 * Bundle entry point for the Interactive WOW Bundle (Stage P.7.2).
 *
 * Reads the embedded project payload, mounts the standalone React/R3F app, and
 * runs fully offline (no Next router, no backend, no CDN). Built by
 * `frontend/scripts/build-wow-bundle.mjs` into `frontend/dist-wow/assets/wow-app.js`.
 */

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { WowBundleApp } from "./WowBundleApp";
import { readEmbeddedBundleData } from "./WowBundleData";
import "./wow-bundle.css";

function mount(): void {
  const container = document.getElementById("wow-bundle-root");
  if (!container) {
    console.error("[wow-bundle] #wow-bundle-root not found");
    return;
  }
  const data = readEmbeddedBundleData();
  document.title = data.project.title;
  createRoot(container).render(
    <StrictMode>
      <WowBundleApp data={data} />
    </StrictMode>,
  );
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", mount, { once: true });
} else {
  mount();
}
