import { accentToHex, type ThemeTokens } from "@/lib/styleIntent";
import type { ThemeTokens as AlfThemeTokens } from "./tokens";
import type { StyleProfileId } from "./styleProfiles";
import { buildThemeTokens } from "./themes";

const RADIUS_MAP = {
  sharp: "4px",
  soft: "8px",
  rounded: "16px",
} as const;

const DENSITY_GAP = {
  compact: "1rem",
  normal: "1.5rem",
  spacious: "2rem",
} as const;

export interface ExtendedThemeVars extends AlfThemeTokens {
  "--alf-radius": string;
  "--alf-gap": string;
  "--alf-motion-duration": string;
  "--alf-hero-mode": string;
}

export function applyThemeTokenOverrides(
  profileId: StyleProfileId,
  tokens?: ThemeTokens | null,
): ExtendedThemeVars {
  const base = buildThemeTokens(profileId);
  const t = tokens ?? {};
  const accentHex = accentToHex(t.accent);
  const isDark = t.color_scheme === "dark";

  const out: ExtendedThemeVars = {
    ...base,
    "--alf-radius": RADIUS_MAP[t.radius ?? "soft"] ?? RADIUS_MAP.soft,
    "--alf-gap": DENSITY_GAP[t.density ?? "normal"] ?? DENSITY_GAP.normal,
    "--alf-motion-duration":
      t.motion === "expressive" ? "0.45s" : t.motion === "none" ? "0s" : "0.25s",
    "--alf-hero-mode": t.hero_mode ?? "classic",
    "--alf-accent": accentHex,
  };

  if (t.background) out["--alf-bg"] = t.background;
  if (t.surface) out["--alf-surface"] = t.surface;

  if (isDark) {
    out["--alf-bg"] = t.background ?? "#0f1419";
    out["--alf-surface"] = t.surface ?? "#1a2332";
    out["--alf-text"] = "#e8edf4";
    out["--alf-text-muted"] = "#94a3b8";
    out["--alf-border"] = "rgba(148,163,184,0.25)";
    out["--alf-accent-muted"] = `${accentHex}26`;
    out["--alf-code-bg"] = "#243044";
  } else if (t.color_scheme === "light") {
    out["--alf-text"] = out["--alf-text"] ?? "#111111";
    out["--alf-text-muted"] = out["--alf-text-muted"] ?? "#7A8799";
  }

  // Bold preset keeps warm accent from base theme when tokens use violet
  if (profileId === "bold" && !isDark) {
    out["--alf-accent"] = "#ea580c";
    out["--alf-accent-muted"] = "#ffedd5";
  }

  return out;
}

export function heroModeClass(heroMode?: string): string {
  switch (heroMode) {
    case "gradient":
      return "alf-hero--gradient";
    case "cards":
      return "alf-hero--cards";
    case "future_3d":
      return "alf-hero--future-3d";
    case "bold":
      return "alf-hero--bold";
    default:
      return "alf-hero--classic";
  }
}

export function motionClass(motion?: string): string {
  if (motion === "none") return "alf-motion--none";
  if (motion === "expressive") return "alf-motion--expressive";
  return "alf-motion--subtle";
}

export function cardStyleClass(cardStyle?: string): string {
  switch (cardStyle) {
    case "flat":
      return "alf-cards--flat";
    case "glass":
      return "alf-cards--glass";
    case "outlined":
      return "alf-cards--outlined";
    default:
      return "alf-cards--soft";
  }
}
