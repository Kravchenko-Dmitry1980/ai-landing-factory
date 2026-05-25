"use client";

import { useState } from "react";
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
  const [expanded, setExpanded] = useState(false);
  const contribs = member.contributions.map((c) =>
    truncateSentenceSafe(normalizeBulletText(c), 240),
  );
  const visible = expanded
    ? contribs
    : contribs.slice(0, MAX_TEAM_CONTRIBUTIONS_VISIBLE);
  const hiddenCount = contribs.length - MAX_TEAM_CONTRIBUTIONS_VISIBLE;

  return (
    <article
      className={`${cardPad} rounded-lg border border-[var(--alf-border)] bg-[var(--alf-surface)] text-left ${
        isUniversity ? "shadow-none" : ""
      }`}
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
      {visible.length > 0 && (
        <ul className="mt-3 space-y-1 text-sm text-[var(--alf-text)]">
          {visible.map((c) => (
            <li key={c} className="pl-3 relative before:content-['·'] before:absolute before:left-0 before:text-[var(--alf-accent)]">
              {c}
            </li>
          ))}
          {!expanded && hiddenCount > 0 && (
            <li className="text-[var(--alf-text-muted)] italic">{formatMoreCount(hiddenCount)}</li>
          )}
        </ul>
      )}
      {hiddenCount > 0 && (
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className={`mt-3 text-sm font-medium ${
            isUniversity ? "text-[var(--alf-accent)]" : "text-[var(--alf-text-muted)]"
          } hover:underline`}
        >
          {expanded ? "Свернуть" : "Показать больше"}
        </button>
      )}
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
