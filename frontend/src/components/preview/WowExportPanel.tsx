"use client";

import { Button } from "@/components/ui/button";

export interface WowExportPanelProps {
  onStandard: () => void;
  onWow: () => void;
  onWow3d: () => void;
  onWowBundle: () => void;
  busy?: boolean;
}

/**
 * Demo export controls (Stage P.7).
 *
 * Standard export stays the default stable version. WOW export is a separate,
 * presentation-grade build (AI cockpit hero, metrics, pipeline map, CTA).
 */
export function WowExportPanel({
  onStandard,
  onWow,
  onWow3d,
  onWowBundle,
  busy = false,
}: WowExportPanelProps) {
  return (
    <section
      className="rounded-lg border border-border bg-muted/40 p-4"
      aria-label="Экспорт для демонстрации"
    >
      <h2 className="text-sm font-semibold">Экспорт для демонстрации</h2>
      <p className="mt-1 text-xs text-muted-foreground">
        WOW HTML — презентационная версия проекта: AI-hero, метрики,
        pipeline-карта и CTA для витрины.
      </p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button variant="outline" type="button" onClick={onStandard} disabled={busy}>
          Standard HTML
        </Button>
        <Button type="button" onClick={onWow} disabled={busy}>
          WOW HTML
        </Button>
        <Button variant="ghost" type="button" onClick={onWow3d} disabled={busy}>
          WOW HTML + 3D runtime
        </Button>
        <Button variant="default" type="button" onClick={onWowBundle} disabled={busy}>
          Экспорт интерактивного WOW ZIP
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Интерактивный WOW ZIP содержит React/R3F-версию лендинга. Распакуйте
        архив и откройте index.html. Если браузер блокирует локальный запуск
        (file://), откройте папку через локальный static server (например{" "}
        <code className="text-xs">python -m http.server</code>).
      </p>
      <p className="mt-2 text-xs text-muted-foreground">
        Standard export остаётся обычной стабильной версией. WOW export
        создаётся отдельно.
      </p>
    </section>
  );
}
