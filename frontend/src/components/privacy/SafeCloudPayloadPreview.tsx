import type { SafeCloudPayloadPreview } from "@/lib/types";

interface Props {
  preview: SafeCloudPayloadPreview | null;
  loading?: boolean;
}

export function SafeCloudPayloadPreviewPanel({ preview, loading }: Props) {
  if (loading) {
    return <p className="text-sm text-muted-foreground">Загрузка cloud payload…</p>;
  }
  if (!preview) return null;

  let statusLabel = "Safe";
  let statusClass = "text-emerald-800 bg-emerald-50 border-emerald-200";
  if (preview.unsafe) {
    statusLabel = "UNSAFE DEV";
    statusClass = "text-red-800 bg-red-50 border-red-200";
  } else if (preview.blocked_reason) {
    statusLabel = "Blocked";
    statusClass = "text-amber-800 bg-amber-50 border-amber-200";
  } else if (!preview.safe_for_cloud) {
    statusLabel = "Not safe";
    statusClass = "text-amber-800 bg-amber-50 border-amber-200";
  }

  return (
    <div className="space-y-2 text-sm">
      <div className="flex flex-wrap items-center gap-2">
        <span className={`rounded border px-2 py-0.5 text-xs font-medium ${statusClass}`}>
          {statusLabel}
        </span>
        <span className="text-muted-foreground">{preview.chars_count} символов</span>
        {preview.files.length > 0 && (
          <span className="text-muted-foreground">· {preview.files.join(", ")}</span>
        )}
      </div>
      {preview.blocked_reason && (
        <p className="text-amber-800 text-xs">Причина блокировки: {preview.blocked_reason}</p>
      )}
      {preview.warnings.length > 0 && (
        <p className="text-xs text-muted-foreground">Warnings: {preview.warnings.join(", ")}</p>
      )}
      <pre className="max-h-40 overflow-auto rounded-md border bg-muted/30 p-2 text-xs whitespace-pre-wrap">
        {preview.preview_text_redacted || "[empty preview]"}
      </pre>
    </div>
  );
}
