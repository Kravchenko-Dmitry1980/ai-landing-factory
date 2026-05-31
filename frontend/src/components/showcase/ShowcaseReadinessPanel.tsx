"use client";

import {
  computeShowcaseReadiness,
  type ReadinessStatus,
} from "@/lib/showcaseReadiness";
import type { ShowcaseConfig } from "@/lib/showcase";

const STATUS_CLASS: Record<ReadinessStatus, string> = {
  ok: "border-green-200 bg-green-50 text-green-900",
  warning: "border-amber-200 bg-amber-50 text-amber-900",
  info: "border-sky-200 bg-sky-50 text-sky-900",
};

export function ShowcaseReadinessPanel({ config }: { config: ShowcaseConfig }) {
  const report = computeShowcaseReadiness(config);

  return (
    <section className="space-y-3 rounded-lg border p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-lg font-semibold">Готовность к демонстрации</h2>
        <span
          className={`rounded-full px-3 py-1 text-xs font-medium ${
            report.ready
              ? "bg-green-100 text-green-800"
              : "bg-amber-100 text-amber-800"
          }`}
        >
          {report.ready ? "Готово к демо" : "Требует доработки"}
        </span>
      </div>
      <ul className="space-y-2">
        {report.checks.map((check) => (
          <li
            key={check.id}
            className={`rounded-md border px-3 py-2 text-sm ${STATUS_CLASS[check.status]}`}
          >
            {check.label}
          </li>
        ))}
      </ul>
    </section>
  );
}
