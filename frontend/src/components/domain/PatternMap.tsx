"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { ArchitecturePattern } from "./types";

interface Props {
  patterns: ArchitecturePattern[];
}

export function PatternMap({ patterns }: Props) {
  if (!patterns.length) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-base">Architecture Patterns</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">No patterns detected.</CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-dashed">
      <CardHeader>
        <CardTitle className="text-base">Architecture Patterns</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {patterns.map((p) => (
          <div key={String(p.pattern)} className="rounded border p-2">
            <p className="font-medium">{String(p.pattern)}</p>
            <p className="text-muted-foreground">
              {(p.confidence * 100).toFixed(0)}% · from {p.detected_from}
            </p>
            {p.related_modules.length > 0 && (
              <p className="text-xs">Modules: {p.related_modules.join(", ")}</p>
            )}
            {p.evidence.slice(0, 2).map((e) => (
              <p key={e} className="text-xs text-muted-foreground">
                {e}
              </p>
            ))}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
