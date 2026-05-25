/**
 * Core design tokens — CSS-variable friendly, profile-agnostic.
 */

export const baseTokens = {
  color: {
    white: "#ffffff",
    gray50: "#f8fafc",
    gray100: "#f1f5f9",
    gray200: "#e2e8f0",
    gray300: "#cbd5e1",
    gray500: "#64748b",
    gray700: "#334155",
    gray900: "#0f172a",
    blue600: "#2563eb",
    blue700: "#1d4ed8",
  },
  radius: {
    sm: "0.25rem",
    md: "0.375rem",
    lg: "0.5rem",
  },
  shadow: {
    none: "none",
    sm: "0 1px 2px rgba(15, 23, 42, 0.04)",
    md: "0 4px 12px rgba(15, 23, 42, 0.06)",
  },
  font: {
    sans: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif',
    mono: 'ui-monospace, "Cascadia Code", "Segoe UI Mono", monospace',
  },
  zIndex: {
    content: 0,
    overlay: 40,
    devPanel: 50,
  },
} as const;

export type ThemeTokens = {
  "--alf-bg": string;
  "--alf-surface": string;
  "--alf-border": string;
  "--alf-text": string;
  "--alf-text-muted": string;
  "--alf-accent": string;
  "--alf-accent-muted": string;
  "--alf-code-bg": string;
};
