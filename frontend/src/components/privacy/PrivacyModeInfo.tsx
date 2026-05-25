import type { PrivacyStatusResponse } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface Props {
  status: PrivacyStatusResponse | null;
}

const MODE_LABELS: Record<string, string> = {
  local_only: "LOCAL_ONLY — без облачной LLM",
  hybrid_safe: "HYBRID_SAFE — cloud только после redaction",
  cloud_unsafe_dev: "CLOUD_UNSAFE_DEV — dev, raw в cloud",
};

export function PrivacyModeInfo({ status }: Props) {
  if (!status) return null;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Privacy mode</CardTitle>
      </CardHeader>
      <CardContent className="space-y-1 text-sm text-muted-foreground">
        <p>{MODE_LABELS[status.privacy_mode] ?? status.privacy_mode}</p>
        <p>PII detection: {status.enable_pii_detection ? "on" : "off"}</p>
        <p>Rehydration: {status.enable_rehydration ? "on" : "off"}</p>
        <p>Cloud LLM allowed: {status.cloud_allowed ? "yes" : "no"}</p>
        <p className="text-xs">
          Режим задаётся в <code className="text-xs">backend/.env</code> (PRIVACY_MODE).
        </p>
      </CardContent>
    </Card>
  );
}
