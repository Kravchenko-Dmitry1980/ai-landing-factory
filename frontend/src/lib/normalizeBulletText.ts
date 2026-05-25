const BULLET_PREFIX = /^[●•·▸▪◦\-*–—]\s*/;

const BAD_ENDING_WORDS = new Set([
  "с", "в", "на", "для", "по", "из", "к", "и", "через", "между",
  "над", "под", "при", "от", "до", "а", "но", "или", "у", "о", "об",
]);

/** Strip duplicate leading bullet markers (parity with HTML export). */
export function normalizeBulletText(text: string): string {
  let cleaned = text.trim();
  while (BULLET_PREFIX.test(cleaned)) {
    cleaned = cleaned.replace(BULLET_PREFIX, "").trim();
  }
  return cleaned;
}

export function normalizeBulletList(items: string[]): string[] {
  return items.map(normalizeBulletText).filter(Boolean);
}

export const MAX_TEAM_CONTRIBUTIONS_VISIBLE = 4;
export const MAX_TEAM_BULLET_CHARS = 240;

function lastWord(text: string): string {
  const stripped = text.replace(/…$/u, "").replace(/[.,;!]+$/u, "").trim();
  const parts = stripped.split(/\s+/u);
  return parts.length ? parts[parts.length - 1].toLowerCase() : "";
}

function endsOnBadWord(text: string): boolean {
  return BAD_ENDING_WORDS.has(lastWord(text));
}

export function truncateAtWord(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  const idx = text.lastIndexOf(" ", maxLen);
  return idx > 0 ? text.slice(0, idx) : text.slice(0, maxLen);
}

/** Parity with backend truncate_sentence_safe for team contribution bullets. */
export function truncateSentenceSafe(
  text: string,
  maxChars: number = MAX_TEAM_BULLET_CHARS,
): string {
  const cleaned = normalizeBulletText(text);
  if (!cleaned || cleaned.length <= maxChars) return cleaned;

  const segment = cleaned.slice(0, maxChars);
  const candidates: string[] = [];

  for (const sep of [".", ";", ","]) {
    const idx = segment.lastIndexOf(sep);
    if (idx >= Math.floor(maxChars * 0.35)) {
      const candidate = segment.slice(0, idx).trim();
      if (candidate) candidates.push(candidate);
    }
  }

  const spaceCut = segment.includes(" ")
    ? segment.slice(0, segment.lastIndexOf(" ")).trim()
    : segment.trim();
  if (spaceCut) candidates.push(spaceCut);

  let chosen = "";
  for (const candidate of candidates) {
    if (!endsOnBadWord(candidate)) {
      chosen = candidate;
      break;
    }
  }

  if (!chosen) {
    chosen = truncateAtWord(cleaned, maxChars).trim();
    while (chosen && endsOnBadWord(chosen) && chosen.includes(" ")) {
      chosen = chosen.slice(0, chosen.lastIndexOf(" ")).trim();
    }
  }

  if (!chosen) {
    chosen = cleaned.slice(0, maxChars).trim();
  }

  if (chosen.length < cleaned.length && !chosen.endsWith("…")) {
    chosen = `${chosen.replace(/[.,;]+$/u, "")}…`;
  }
  return chosen;
}

export function formatMoreCount(count: number): string {
  const n = Math.abs(count);
  const mod100 = n % 100;
  const mod10 = n % 10;
  let word = "пунктов";
  if (mod100 >= 11 && mod100 <= 14) {
    word = "пунктов";
  } else if (mod10 === 1) {
    word = "пункт";
  } else if (mod10 >= 2 && mod10 <= 4) {
    word = "пункта";
  }
  return `+ ещё ${n} ${word}`;
}
