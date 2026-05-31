/**
 * Demo readiness checks for a saved showcase (Stage P.6.3, UI-only).
 */

import type { ShowcaseConfig } from "./showcase";

export type ReadinessStatus = "ok" | "warning" | "info";

export interface ShowcaseReadinessCheck {
  id: string;
  label: string;
  status: ReadinessStatus;
}

export interface ShowcaseReadinessReport {
  ready: boolean;
  checks: ShowcaseReadinessCheck[];
}

export interface ShowcaseReadinessOptions {
  /** Whether portable ZIP export is available in this build. */
  zipExportAvailable?: boolean;
  /** Whether vendored A-Frame runtime is bundled into ZIP exports. */
  aframeVendored?: boolean;
}

function countDemoLinks(config: ShowcaseConfig): number {
  return config.projects.filter((p) => p.demo_url?.trim()).length;
}

function countLandingLinks(config: ShowcaseConfig): number {
  return config.projects.filter((p) => p.landing_url?.trim()).length;
}

function countPreviewLandingLinks(config: ShowcaseConfig): number {
  return config.projects.filter((p) =>
    p.landing_url?.trim().startsWith("/preview/"),
  ).length;
}

/** Compute demo-readiness messages from the current showcase config. */
export function computeShowcaseReadiness(
  config: ShowcaseConfig,
  options: ShowcaseReadinessOptions = {},
): ShowcaseReadinessReport {
  const zipExportAvailable = options.zipExportAvailable ?? true;
  const aframeVendored = options.aframeVendored ?? true;
  const checks: ShowcaseReadinessCheck[] = [];
  const projectCount = config.projects.length;
  const demoCount = countDemoLinks(config);
  const landingCount = countLandingLinks(config);
  const previewLandingCount = countPreviewLandingLinks(config);

  if (projectCount === 0) {
    checks.push({
      id: "projects",
      label: "Добавьте хотя бы один проект в витрину",
      status: "warning",
    });
  } else {
    checks.push({
      id: "projects",
      label: `${projectCount} проект(ов) добавлено`,
      status: "ok",
    });
  }

  if (projectCount > 0 && demoCount === 0) {
    checks.push({
      id: "demo_links",
      label: "Demo-ссылки не добавлены — укажите AI Google Studio или другое демо",
      status: "warning",
    });
  } else if (demoCount > 0) {
    checks.push({
      id: "demo_links",
      label: `${demoCount} demo-ссыл(ок/ки) добавлено`,
      status: "ok",
    });
  }

  if (landingCount > 0) {
    checks.push({
      id: "landing_links",
      label:
        previewLandingCount === landingCount
          ? `${landingCount} ссыл(ок/ки) на ленд — относительные preview-ссылки (тот же frontend)`
          : `${landingCount} ссыл(ок/ки) на ленд в карточках проектов`,
      status: "info",
    });
  }

  if (zipExportAvailable) {
    checks.push({
      id: "zip_export",
      label: "ZIP-экспорт доступен",
      status: "ok",
    });
  } else {
    checks.push({
      id: "zip_export",
      label: "ZIP-экспорт недоступен в этой сборке",
      status: "warning",
    });
  }

  if (aframeVendored) {
    checks.push({
      id: "aframe_runtime",
      label: "3D runtime (A-Frame) включён в ZIP — офлайн-просмотр 3D-стенда",
      status: "ok",
    });
  }

  checks.push({
    id: "demo_internet",
    label: "Demo-ссылки требуют интернет при открытии",
    status: "info",
  });

  const ready =
    projectCount > 0 &&
    demoCount > 0 &&
    zipExportAvailable &&
    aframeVendored;

  return { ready, checks };
}
