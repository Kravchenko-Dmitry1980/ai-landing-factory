interface Props {
  hasPii: boolean;
  count?: number;
}

export function PiiBadge({ hasPii, count }: Props) {
  if (!hasPii) return null;
  return (
    <span
      className="inline-flex items-center rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-900"
      title="Обнаружены персональные данные — перед cloud LLM применяется маскирование"
    >
      PII detected{count != null && count > 0 ? ` · ${count}` : ""}
    </span>
  );
}
