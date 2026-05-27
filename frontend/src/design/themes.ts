import type { CSSProperties } from "react";
import type { ThemeTokens } from "./tokens";
import type { StyleProfileId } from "./styleProfiles";

export function buildThemeTokens(profile: StyleProfileId): ThemeTokens {
  const themes: Record<StyleProfileId, ThemeTokens> = {
    university_platform: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#F1F4F7",
      "--alf-border": "#E5E7EB",
      "--alf-text": "#111111",
      "--alf-text-muted": "#7A8799",
      "--alf-accent": "#7C3AED",
      "--alf-accent-muted": "#EDE9FE",
      "--alf-code-bg": "#EEF2F5",
    },
    minimal: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#fafafa",
      "--alf-border": "#f0f0f0",
      "--alf-text": "#171717",
      "--alf-text-muted": "#737373",
      "--alf-accent": "#525252",
      "--alf-accent-muted": "#f5f5f5",
      "--alf-code-bg": "#fafafa",
    },
    corporate: {
      "--alf-bg": "#f8fafc",
      "--alf-surface": "#ffffff",
      "--alf-border": "#cbd5e1",
      "--alf-text": "#0f172a",
      "--alf-text-muted": "#64748b",
      "--alf-accent": "#2563eb",
      "--alf-accent-muted": "#dbeafe",
      "--alf-code-bg": "#f1f5f9",
    },
    tech: {
      "--alf-bg": "#0f172a",
      "--alf-surface": "#1e293b",
      "--alf-border": "rgba(148,163,184,0.25)",
      "--alf-text": "#e8edf4",
      "--alf-text-muted": "#94a3b8",
      "--alf-accent": "#6366f1",
      "--alf-accent-muted": "#312e8133",
      "--alf-code-bg": "#243044",
    },
    bold: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#fff7ed",
      "--alf-border": "#fed7aa",
      "--alf-text": "#1c1917",
      "--alf-text-muted": "#78716c",
      "--alf-accent": "#ea580c",
      "--alf-accent-muted": "#ffedd5",
      "--alf-code-bg": "#fff7ed",
    },
    custom: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#F1F4F7",
      "--alf-border": "#E5E7EB",
      "--alf-text": "#111111",
      "--alf-text-muted": "#7A8799",
      "--alf-accent": "#7C3AED",
      "--alf-accent-muted": "#EDE9FE",
      "--alf-code-bg": "#EEF2F5",
    },
  };
  return themes[profile];
}

export function themeStyleObject(tokens: ThemeTokens): CSSProperties {
  return tokens as unknown as CSSProperties;
}
