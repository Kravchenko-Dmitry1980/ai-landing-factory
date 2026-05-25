"use client";

import type { SystemArchetype } from "./types";

interface Props {
  archetypes: SystemArchetype[];
  domain?: string | null;
}

export function ArchetypeBadges({ archetypes, domain }: Props) {
  const items = [
    ...(domain ? [{ label: domain, kind: "domain" as const }] : []),
    ...archetypes.map((a) => ({
      label: String(a.archetype),
      kind: "archetype" as const,
      confidence: a.confidence,
    })),
  ];

  if (items.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item.label}
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
            item.kind === "domain"
              ? "bg-blue-100 text-blue-900"
              : "bg-violet-100 text-violet-900"
          }`}
          title={"confidence" in item ? `${(item.confidence * 100).toFixed(0)}%` : undefined}
        >
          {item.label}
        </span>
      ))}
    </div>
  );
}
