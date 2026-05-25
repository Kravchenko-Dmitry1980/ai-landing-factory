import type { RenderPlan } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
  title: string;
  kicker?: string;
}

export function SectionHeading({ plan, title, kicker }: Props) {
  const { label, h2 } = plan.profile.typography;
  const headerBorder =
    plan.profileId === "university_platform"
      ? "mb-6 border-b border-[#111111] pb-4"
      : "mb-6 border-b border-[var(--alf-border)] pb-4";
  return (
    <header className={headerBorder}>
      {kicker && <p className={label}>{kicker}</p>}
      <h2 className={`${h2} text-[var(--alf-text)]`}>{title}</h2>
    </header>
  );
}
