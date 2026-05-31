/**
 * WOW hero preview mode resolution (Stage P.7.1).
 *
 * The preview hero has three modes, fully backward compatible:
 *  - "standard": no WOW hero, the classic interactive renderer only (default).
 *  - "wow":      premium R3F hero with lightweight motion ("lite" intensity).
 *  - "wow3d":    full immersive R3F hero (particles, orbiting nodes, parallax).
 *
 * Mode is opt-in via the `?mode=` query param so the standard preview path is
 * never altered when the param is absent.
 */

export type WowHeroMode = "standard" | "wow" | "wow3d";

export type WowSceneIntensity = "lite" | "full";

const VALID_MODES: ReadonlySet<string> = new Set(["standard", "wow", "wow3d"]);

/** Parse a raw query value into a safe {@link WowHeroMode}. */
export function parseWowHeroMode(raw: string | null | undefined): WowHeroMode {
  if (!raw) return "standard";
  const value = raw.trim().toLowerCase();
  if (VALID_MODES.has(value)) return value as WowHeroMode;
  return "standard";
}

/** Whether the given mode renders the R3F WOW hero at all. */
export function isWowMode(mode: WowHeroMode): boolean {
  return mode === "wow" || mode === "wow3d";
}

/** Scene richness for a mode: wow = lite motion, wow3d = full immersive. */
export function sceneIntensity(mode: WowHeroMode): WowSceneIntensity {
  return mode === "wow3d" ? "full" : "lite";
}

/** Detect the user's reduced-motion preference (SSR-safe). */
export function prefersReducedMotion(): boolean {
  if (typeof window === "undefined" || !window.matchMedia) return false;
  try {
    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch {
    return false;
  }
}

/**
 * Best-effort WebGL availability probe (SSR-safe). Used to decide whether the
 * 3D canvas can mount or the static fallback must be shown instead.
 */
export function isWebGLAvailable(): boolean {
  if (typeof window === "undefined" || typeof document === "undefined") {
    return false;
  }
  try {
    const canvas = document.createElement("canvas");
    const gl =
      canvas.getContext("webgl2") ||
      canvas.getContext("webgl") ||
      canvas.getContext("experimental-webgl");
    return Boolean(gl);
  } catch {
    return false;
  }
}
