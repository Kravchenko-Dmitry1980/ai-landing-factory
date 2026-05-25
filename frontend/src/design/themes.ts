import type { CSSProperties } from "react";
import type { ThemeTokens } from "./tokens";
import type { StyleProfileId } from "./style_profiles";

export function buildThemeTokens(profile: StyleProfileId): ThemeTokens {
  const themes: Record<StyleProfileId, ThemeTokens> = {
    enterprise: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#f8fafc",
      "--alf-border": "#e2e8f0",
      "--alf-text": "#0f172a",
      "--alf-text-muted": "#64748b",
      "--alf-accent": "#2563eb",
      "--alf-accent-muted": "#dbeafe",
      "--alf-code-bg": "#f1f5f9",
    },
    medical: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#f8fafc",
      "--alf-border": "#cbd5e1",
      "--alf-text": "#1e293b",
      "--alf-text-muted": "#64748b",
      "--alf-accent": "#0e7490",
      "--alf-accent-muted": "#cffafe",
      "--alf-code-bg": "#f1f5f9",
    },
    ai_research: {
      "--alf-bg": "#fafafa",
      "--alf-surface": "#f4f4f5",
      "--alf-border": "#d4d4d8",
      "--alf-text": "#18181b",
      "--alf-text-muted": "#71717a",
      "--alf-accent": "#4338ca",
      "--alf-accent-muted": "#e0e7ff",
      "--alf-code-bg": "#f4f4f5",
    },
    education: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#f9fafb",
      "--alf-border": "#e5e7eb",
      "--alf-text": "#111827",
      "--alf-text-muted": "#6b7280",
      "--alf-accent": "#1d4ed8",
      "--alf-accent-muted": "#eff6ff",
      "--alf-code-bg": "#f3f4f6",
    },
    analytics: {
      "--alf-bg": "#ffffff",
      "--alf-surface": "#f8fafc",
      "--alf-border": "#e2e8f0",
      "--alf-text": "#0f172a",
      "--alf-text-muted": "#475569",
      "--alf-accent": "#0369a1",
      "--alf-accent-muted": "#e0f2fe",
      "--alf-code-bg": "#f1f5f9",
    },
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
  };
  return themes[profile];
}

export function themeStyleObject(tokens: ThemeTokens): CSSProperties {
  return tokens as unknown as CSSProperties;
}
