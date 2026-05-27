import type { CSSProperties } from "react";
import type { StyleProfileId } from "./styleProfiles";
import { PROFILE_PRESETS, themeTokensToCssVars } from "./themeTokens";
import type { ThemeTokens as LegacyCssTokens } from "./tokens";

/** Build legacy CSS-var map from shared token presets. */
export function buildThemeTokens(profile: StyleProfileId): LegacyCssTokens {
  const preset = PROFILE_PRESETS[profile];
  const vars = themeTokensToCssVars(preset);
  return {
    "--alf-bg": vars["--alf-bg"],
    "--alf-surface": vars["--alf-surface"],
    "--alf-border": vars["--alf-border"],
    "--alf-text": vars["--alf-text"],
    "--alf-text-muted": vars["--alf-muted"],
    "--alf-accent": vars["--alf-accent"],
    "--alf-accent-muted": vars["--alf-accent-light"],
    "--alf-code-bg": vars["--alf-code-bg"],
  };
}

export function themeStyleObject(vars: Record<string, string>): CSSProperties {
  return vars as unknown as CSSProperties;
}
