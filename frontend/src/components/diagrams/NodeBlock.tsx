interface Props {
  label: string;
  value: string;
}

export function NodeBlock({ label, value }: Props) {
  return (
    <div className="inline-flex flex-col rounded border border-[var(--alf-border)] bg-[var(--alf-code-bg)] px-3 py-2">
      <span className="text-[0.65rem] uppercase tracking-wider text-[var(--alf-text-muted)]">
        {label}
      </span>
      <span className="font-mono text-xs text-[var(--alf-text)]">{value}</span>
    </div>
  );
}
