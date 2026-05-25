"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import type { SectionRenderProps } from "@/rendering/types";

function bulletsToChartData(bullets: string[]) {
  return bullets.slice(0, 8).map((b, i) => ({
    name: `R${i + 1}`,
    label: b.length > 32 ? `${b.slice(0, 32)}…` : b,
    value: Math.max(1, Math.min(100, b.length * 2)),
  }));
}

export function MetricsSection({ section, plan, index }: SectionRenderProps) {
  const data = bulletsToChartData(
    section.bullets.length ? section.bullets : [section.body || "Outcome"],
  );
  const accent = "var(--alf-accent)";

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="metrics" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Outcomes" />
      <div className="h-64 w-full rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)] p-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--alf-border)" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="var(--alf-text-muted)" />
            <YAxis tick={{ fontSize: 11 }} stroke="var(--alf-text-muted)" />
            <Tooltip
              contentStyle={{
                background: "var(--alf-bg)",
                border: "1px solid var(--alf-border)",
                fontSize: 12,
              }}
              formatter={(_, __, item) => [(item.payload as { label: string }).label, ""]}
            />
            <Bar dataKey="value" fill={accent} radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
      <ul className="mt-4 grid gap-2 md:grid-cols-2">
        {section.bullets.map((b) => (
          <li
            key={b}
            className="border-l-2 border-[var(--alf-accent)] pl-3 text-sm text-[var(--alf-text)]"
          >
            {b}
          </li>
        ))}
      </ul>
    </SectionShell>
  );
}
