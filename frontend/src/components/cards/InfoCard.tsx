import type { RenderPlan } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
  title: string;
  children: React.ReactNode;
}

export function InfoCard({ plan, title, children }: Props) {
  const { cardPad } = plan.profile.spacing;
  const { h3, body } = plan.profile.typography;
  return (
    <div
      className={`${cardPad} rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)]`}
    >
      <h3 className={`${h3} mb-2 text-[var(--alf-text)]`}>{title}</h3>
      <div className={`${body} text-[var(--alf-text-muted)]`}>{children}</div>
    </div>
  );
}
