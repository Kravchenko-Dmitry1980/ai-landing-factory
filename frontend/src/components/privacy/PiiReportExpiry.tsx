interface Props {
  expiresAt: string | null;
}

export function PiiReportExpiry({ expiresAt }: Props) {
  if (!expiresAt) return null;
  const exp = new Date(expiresAt);
  const label = exp.toLocaleString("ru-RU");
  return (
    <p className="text-xs text-muted-foreground">
      Отчёт PII истекает: {label} (TTL cleanup)
    </p>
  );
}
