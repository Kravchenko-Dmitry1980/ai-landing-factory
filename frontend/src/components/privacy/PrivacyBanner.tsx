import type { PrivacyStatusResponse } from "@/lib/types";

interface Props {
  status: PrivacyStatusResponse | null;
}

export function PrivacyBanner({ status }: Props) {
  if (!status?.cloud_unsafe_warning) return null;
  return (
    <div
      role="alert"
      className="rounded-md border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-900"
    >
      <strong>CLOUD_UNSAFE_DEV:</strong> облачная LLM может получать немаскированный текст.
      Не используйте в production.
    </div>
  );
}
