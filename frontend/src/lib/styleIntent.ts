/**
 * Deterministic custom style intent → safe theme tokens (no LLM, no raw CSS).
 */

export type ColorScheme = "light" | "dark" | "auto";
export type AccentToken = "blue" | "violet" | "green";
export type RadiusToken = "sharp" | "soft" | "rounded";
export type DensityToken = "compact" | "normal" | "spacious";
export type MotionToken = "none" | "subtle" | "expressive";
export type HeroModeToken = "classic" | "gradient" | "cards" | "future_3d";

export interface ThemeTokens {
  color_scheme?: ColorScheme;
  accent?: AccentToken;
  background?: string;
  surface?: string;
  radius?: RadiusToken;
  density?: DensityToken;
  motion?: MotionToken;
  hero_mode?: HeroModeToken;
}

const ACCENT_HEX: Record<AccentToken, string> = {
  blue: "#2563eb",
  violet: "#7C3AED",
  green: "#059669",
};

const DARK_SURFACES = {
  background: "#0f1419",
  surface: "#1a2332",
};

const LIGHT_SURFACES = {
  background: "#ffffff",
  surface: "#F1F4F7",
};

/** University platform baseline when prompt is empty. */
export const UNIVERSITY_DEFAULT_TOKENS: ThemeTokens = {
  color_scheme: "light",
  accent: "violet",
  background: "#ffffff",
  surface: "#F1F4F7",
  radius: "soft",
  density: "normal",
  motion: "subtle",
  hero_mode: "classic",
};

const DANGEROUS_PATTERN =
  /(<\s*script|javascript:|@import|url\s*\(|expression\s*\(|body\s*\{|display\s*:\s*none|\.css|{\s*[^}]*:)/i;

function normalizePrompt(prompt: string): string {
  return prompt
    .toLowerCase()
    .replace(/ё/g, "е")
    .replace(/[^\p{L}\p{N}\s#-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function containsDangerousInput(prompt: string): boolean {
  return DANGEROUS_PATTERN.test(prompt);
}

function pickHeroMode(text: string): HeroModeToken | undefined {
  if (/3d|объемн|объёмн|интерактив/.test(text)) return "future_3d";
  if (/технолог|cyber|\bai\b/.test(text)) return "gradient";
  if (/карточк|cards/.test(text)) return "cards";
  return undefined;
}

function pickMotion(text: string): MotionToken | undefined {
  if (/анимац|плавн|expressive|динамич|технолог/.test(text)) return "expressive";
  if (/без анима|static|none/.test(text)) return "none";
  if (/строг|корпоратив|делов/.test(text)) return "subtle";
  return undefined;
}

/**
 * Parse free-text style description into controlled theme tokens only.
 */
export function parseStyleIntent(prompt: string): ThemeTokens {
  const raw = prompt.trim();
  if (!raw || containsDangerousInput(raw)) {
    return { ...UNIVERSITY_DEFAULT_TOKENS };
  }

  const text = normalizePrompt(raw);
  const tokens: ThemeTokens = { ...UNIVERSITY_DEFAULT_TOKENS };

  if (/темн|dark|ночн/.test(text)) {
    tokens.color_scheme = "dark";
    tokens.background = DARK_SURFACES.background;
    tokens.surface = DARK_SURFACES.surface;
  } else if (/светл|light|бел/.test(text)) {
    tokens.color_scheme = "light";
    tokens.background = LIGHT_SURFACES.background;
    tokens.surface = LIGHT_SURFACES.surface;
  }

  if (/син/.test(text)) tokens.accent = "blue";
  else if (/фиолет/.test(text)) tokens.accent = "violet";
  else if (/зелен|зелён/.test(text)) tokens.accent = "green";

  if (/остр|sharp|строг/.test(text)) tokens.radius = "sharp";
  else if (/скруг|rounded|мягк/.test(text)) tokens.radius = "rounded";

  if (/компакт|compact|плотн/.test(text)) tokens.density = "compact";
  else if (/простор|spacious|воздуш/.test(text)) tokens.density = "spacious";

  const motion = pickMotion(text);
  if (motion) tokens.motion = motion;

  if (/строг|корпоратив/.test(text)) {
    tokens.density = tokens.density ?? "normal";
    tokens.motion = tokens.motion ?? "subtle";
  }

  const hero = pickHeroMode(text);
  if (hero) tokens.hero_mode = hero;
  else if (/технолог|cyber|\bai\b/.test(text)) {
    tokens.hero_mode = tokens.hero_mode ?? "gradient";
    tokens.accent = tokens.accent ?? "blue";
  }

  if (tokens.hero_mode === "future_3d") {
    tokens.motion = tokens.motion ?? "expressive";
  }

  if (tokens.accent) {
    const hex = ACCENT_HEX[tokens.accent];
    void hex;
  }

  return tokens;
}

export function accentToHex(accent?: AccentToken): string {
  if (!accent) return ACCENT_HEX.violet;
  return ACCENT_HEX[accent] ?? ACCENT_HEX.violet;
}
