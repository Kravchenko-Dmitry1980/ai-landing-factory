import type { PrivacyStatusResponse } from "@/lib/types";

interface Props {
  status: PrivacyStatusResponse | null;
}

const MODE_LABELS: Record<string, string> = {
  local_only: "LOCAL_ONLY — облачная LLM заблокирована",
  hybrid_safe: "HYBRID_SAFE — cloud только после redaction",
  cloud_unsafe_dev: "CLOUD_UNSAFE_DEV — dev, raw в cloud",
};

export function PrivacyModeStatus({ status }: Props) {
  if (!status) return null;
  return (
    <div className="space-y-1 text-sm text-muted-foreground">
      <p className="font-medium text-foreground">
        {MODE_LABELS[status.privacy_mode] ?? status.privacy_mode}
      </p>
      <p>PII detection: {status.enable_pii_detection ? "on" : "off"}</p>
      <p>Rehydration: {status.enable_rehydration ? "on" : "off"}</p>
      <p>Cloud LLM: {status.cloud_allowed ? "разрешена" : "заблокирована"}</p>
      {status.cloud_unsafe_warning && (
        <p className="text-red-700 font-medium text-xs">
          ⚠ Dev-режим: персональные данные могут уходить в облако без маскирования
        </p>
      )}
    </div>
  );
}
