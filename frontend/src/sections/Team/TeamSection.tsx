"use client";

import { SectionHeading } from "@/components/typography/SectionHeading";
import { SectionShell } from "@/components/grids/SectionShell";
import {
  MAX_TEAM_CONTRIBUTIONS_VISIBLE,
  formatMoreCount,
  normalizeBulletText,
  truncateSentenceSafe,
} from "@/lib/normalizeBulletText";
import type { TeamMember } from "@/lib/types";
import type { SectionRenderProps } from "@/rendering/types";

function parseMember(line: string): TeamMember {
  const parts = line.split(/[—–-]/);
  if (parts.length >= 2) {
    return {
      name: parts[0].trim(),
      role: parts.slice(1).join("-").trim(),
      project_area: "",
      contributions: [],
    };
  }
  return { name: line, role: "Contributor", project_area: "", contributions: [] };
}

function TeamMemberCard({
  member,
  isUniversity,
  cardPad,
  h3,
  body,
}: {
  member: TeamMember;
  isUniversity: boolean;
  cardPad: string;
  h3: string;
  body: string;
}) {
  const contribs = member.contributions.map((c) =>
    truncateSentenceSafe(normalizeBulletText(c), 240),
  );
  const preview = contribs.slice(0, MAX_TEAM_CONTRIBUTIONS_VISIBLE);
  const hiddenCount = contribs.length - MAX_TEAM_CONTRIBUTIONS_VISIBLE;

  return (
    <article
      className={`alf-card-lift alf-card--interactive ${cardPad} rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)] text-left ${
        isUniversity ? "shadow-none" : ""
      }`}
      style={{ borderRadius: "var(--alf-radius, 0.5rem)" }}
    >
      <h3 className={`${h3} text-[var(--alf-text)]`}>{member.name}</h3>
      {member.role && (
        <p
          className={`${body} mt-1 ${
            isUniversity ? "text-[var(--alf-accent)] font-medium" : "text-[var(--alf-text-muted)]"
          }`}
        >
          {member.role}
        </p>
      )}
      {member.project_area && (
        <p className="mt-1 text-sm text-[var(--alf-text-muted)]">{member.project_area}</p>
      )}
      {contribs.length > 0 &&
        (hiddenCount > 0 ? (
          <details className="alf-collapsible team-contrib mt-3">
            <summary className="text-sm">Вклад участника</summary>
            <ul className="mt-2 space-y-1 text-sm text-[var(--alf-text)]">
              {contribs.map((c) => (
                <li
                  key={c}
                  className="relative pl-3 before:absolute before:left-0 before:text-[var(--alf-accent)] before:content-['·']"
                >
                  {c}
                </li>
              ))}
            </ul>
          </details>
        ) : (
          <ul className="mt-3 space-y-1 text-sm text-[var(--alf-text)]">
            {preview.map((c) => (
              <li
                key={c}
                className="relative pl-3 before:absolute before:left-0 before:text-[var(--alf-accent)] before:content-['·']"
              >
                {c}
              </li>
            ))}
            {hiddenCount > 0 && (
              <li className="italic text-[var(--alf-text-muted)]">{formatMoreCount(hiddenCount)}</li>
            )}
          </ul>
        ))}
    </article>
  );
}

export function TeamSection({ section, plan, index }: SectionRenderProps) {
  const structured = plan.team;
  const useStructured = structured.length > 0;
  const fallbackLines = (section.bullets.length ? section.bullets : [section.body]).filter(
    Boolean,
  );
  const members = useStructured ? structured : fallbackLines.map(parseMember);

  const { gridGap, cardPad } = plan.profile.spacing;
  const { h3, body } = plan.profile.typography;
  const isUniversity = plan.profileId === "university_platform";

  if (members.length === 0) return null;

  return (
    <SectionShell plan={plan} sectionId={section.id} sectionType="team" index={index}>
      <SectionHeading plan={plan} title={section.title} kicker="Project team" />
      <div className={`grid ${gridGap} sm:grid-cols-2`}>
        {members.map((member) => (
          <TeamMemberCard
            key={`${member.name}-${member.role}`}
            member={member}
            isUniversity={isUniversity}
            cardPad={cardPad}
            h3={h3}
            body={body}
          />
        ))}
      </div>
    </SectionShell>
  );
}
