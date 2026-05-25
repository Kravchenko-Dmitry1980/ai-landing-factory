"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { IntelligenceDomainProfile } from "./types";

interface Props {
  profile: IntelligenceDomainProfile | null | undefined;
}

export function DomainProfilePanel({ profile }: Props) {
  if (!profile) {
    return (
      <Card className="border-dashed">
        <CardHeader>
          <CardTitle className="text-base">Domain Profile</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Domain analysis not available. Run generate or domain-analyze.
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-dashed">
      <CardHeader>
        <CardTitle className="text-base">Domain Profile</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2 text-sm">
        <p>
          Primary: <strong>{profile.primary_domain}</strong> · confidence{" "}
          {(profile.confidence * 100).toFixed(0)}%
        </p>
        {profile.secondary_domains.length > 0 && (
          <p>Secondary: {profile.secondary_domains.join(", ")}</p>
        )}
        {profile.evidence.length > 0 && (
          <ul className="list-disc pl-5 text-muted-foreground">
            {profile.evidence.slice(0, 5).map((e) => (
              <li key={e}>{e}</li>
            ))}
          </ul>
        )}
        {profile.warnings.map((w) => (
          <p key={w} className="text-amber-700">
            {w}
          </p>
        ))}
      </CardContent>
    </Card>
  );
}
