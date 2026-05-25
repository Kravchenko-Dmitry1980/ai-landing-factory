"use client";

import { useState } from "react";
import type { TeamMember } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  members: TeamMember[];
}

export function TeamCardsPanel({ members }: Props) {
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});

  if (!members.length) return null;

  function toggle(name: string) {
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">
          Команда ({members.length})
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2 sm:grid-cols-2">
        {members.map((m) => {
          const isOpen = expanded[m.name] ?? false;
          const preview = m.contributions.slice(0, isOpen ? undefined : 2);
          return (
            <div
              key={m.name}
              className="rounded-md border border-border bg-muted/30 p-3 text-sm"
            >
              <button
                type="button"
                className="w-full text-left"
                onClick={() => toggle(m.name)}
              >
                <p className="font-medium">{m.name}</p>
                {m.role && (
                  <p className="text-xs text-primary">{m.role}</p>
                )}
                {m.project_area && (
                  <p className="text-xs text-muted-foreground">{m.project_area}</p>
                )}
              </button>
              {preview.length > 0 && (
                <ul className="mt-2 list-disc pl-4 text-xs text-muted-foreground">
                  {preview.map((c) => (
                    <li key={c.slice(0, 40)}>{c}</li>
                  ))}
                </ul>
              )}
              {m.contributions.length > 2 && (
                <button
                  type="button"
                  className="mt-1 text-xs text-primary hover:underline"
                  onClick={() => toggle(m.name)}
                >
                  {isOpen ? "Свернуть" : `Ещё ${m.contributions.length - 2}…`}
                </button>
              )}
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}
