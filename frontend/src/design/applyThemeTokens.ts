import type { LandingStyleConfig } from "@/lib/types";
import {
  normalizeThemeTokens,
  themeTokensToCssVars,
  type AlfCssVars,
} from "./themeTokens";

export type { AlfCssVars as ExtendedThemeVars };

export function applyThemeTokenOverrides(styleConfig: LandingStyleConfig): AlfCssVars {
  const tokens = normalizeThemeTokens(styleConfig);
  return themeTokensToCssVars(tokens);
}

export function heroModeClass(heroMode?: string): string {
  switch (heroMode) {
    case "gradient":
      return "alf-hero--gradient";
    case "cards":
    case "bold":
      return "alf-hero--cards";
    case "future_3d":
      return "alf-hero--future-3d";
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
