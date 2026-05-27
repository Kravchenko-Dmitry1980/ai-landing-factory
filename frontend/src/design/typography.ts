import type { StyleProfileId } from "./styleProfiles";

export interface TypographyScale {
  hero: string;
  h1: string;
  h2: string;
  h3: string;
  body: string;
  caption: string;
  label: string;
  mono: string;
}

const MINIMAL: TypographyScale = {
  hero: "text-3xl md:text-4xl font-light tracking-tight leading-tight",
  h1: "text-2xl md:text-3xl font-light tracking-tight",
  h2: "text-lg md:text-xl font-medium",
  h3: "text-base font-normal",
  body: "text-base leading-loose",
  caption: "text-sm text-[var(--alf-text-muted)]",
  label: "text-[0.6875rem] uppercase tracking-widest font-medium text-[var(--alf-text-muted)]",
  mono: "font-mono text-sm",
};

const CORPORATE: TypographyScale = {
  hero: "text-3xl md:text-4xl font-semibold tracking-tight leading-tight",
  h1: "text-2xl md:text-3xl font-semibold tracking-tight",
  h2: "text-lg md:text-xl font-semibold",
  h3: "text-base font-medium",
  body: "text-sm md:text-[0.9375rem] leading-relaxed",
  caption: "text-xs text-[var(--alf-text-muted)]",
  label: "text-[0.6875rem] uppercase tracking-widest font-medium text-[var(--alf-text-muted)]",
  mono: "font-mono text-xs",
};

const TECH: TypographyScale = {
  hero: "text-4xl md:text-5xl font-bold tracking-tight leading-[1.1]",
  h1: "text-2xl md:text-3xl font-bold tracking-tight",
  h2: "text-xl font-semibold",
  h3: "text-base font-semibold",
  body: "text-base leading-relaxed",
  caption: "text-sm text-[var(--alf-text-muted)]",
  label: "text-xs uppercase tracking-widest font-medium text-[var(--alf-text-muted)]",
  mono: "font-mono text-sm",
};

const BOLD: TypographyScale = {
  hero: "text-5xl md:text-6xl font-extrabold tracking-tight leading-[1.05]",
  h1: "text-3xl md:text-4xl font-extrabold tracking-tight",
  h2: "text-2xl md:text-3xl font-bold",
  h3: "text-lg font-bold",
  body: "text-base md:text-lg leading-relaxed",
  caption: "text-sm text-[var(--alf-text-muted)]",
  label: "text-xs uppercase tracking-widest font-bold text-[var(--alf-text-muted)]",
  mono: "font-mono text-sm",
};

const UNIVERSITY: TypographyScale = {
  hero: "text-[2.5rem] md:text-[3rem] font-bold tracking-tight leading-[1.15]",
  h1: "text-2xl md:text-[2rem] font-bold tracking-tight",
  h2: "text-2xl md:text-[2rem] font-bold border-b border-[#111111] pb-3",
  h3: "text-lg md:text-[1.375rem] font-semibold",
  body: "text-base leading-[1.65]",
  caption: "text-sm text-[var(--alf-text-muted)]",
  label: "text-xs uppercase tracking-widest font-medium text-[var(--alf-text-muted)]",
  mono: "font-mono text-sm",
};

export function getTypographyScale(profile: StyleProfileId): TypographyScale {
  switch (profile) {
    case "minimal":
      return MINIMAL;
    case "corporate":
      return CORPORATE;
    case "tech":
      return TECH;
    case "bold":
      return BOLD;
    case "custom":
      return CORPORATE;
    case "university_platform":
    default:
      return UNIVERSITY;
  }
}
