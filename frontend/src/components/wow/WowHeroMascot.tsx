"use client";

import { WOW_CAT_MASCOT_SRC } from "./wowMascotAsset";

interface Props {
  /** Override image src (bundle export uses a relative path). */
  src?: string;
  className?: string;
}

/**
 * Exhibition-grade hero mascot layer (Stage P.7.6).
 *
 * "2D landing + one 3D mascot": the cat PNG sits on the right with a soft
 * platform glow and lightweight glass UI cards. No portal rings or heavy 3D
 * decor — works in preview, bundle and static export.
 */
export function WowHeroMascot({ src = WOW_CAT_MASCOT_SRC, className }: Props) {
  return (
    <div
      className={["wow-hero-mascot", className].filter(Boolean).join(" ")}
      aria-hidden="true"
    >
      {/* Floating 2D UI decor around the mascot */}
      <div className="wow-hero-ui-card wow-hero-ui-card--chart">
        <span className="wow-hero-ui-bar wow-hero-ui-bar--1" />
        <span className="wow-hero-ui-bar wow-hero-ui-bar--2" />
        <span className="wow-hero-ui-bar wow-hero-ui-bar--3" />
        <span className="wow-hero-ui-bar wow-hero-ui-bar--4" />
      </div>

      <div className="wow-hero-ui-card wow-hero-ui-card--news">
        <span className="wow-hero-ui-line wow-hero-ui-line--title" />
        <span className="wow-hero-ui-line" />
        <span className="wow-hero-ui-line wow-hero-ui-line--short" />
      </div>

      <div className="wow-hero-ui-icon wow-hero-ui-icon--telegram" title="">
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path
            fill="currentColor"
            d="M9.78 15.28l-.28 3.92c.4 0 .57-.17.78-.38l1.87-1.78 3.88 2.85c.71.39 1.22.18 1.4-.64l2.54-12c.23-1.04-.38-1.45-1.07-1.2L2.36 9.82c-1.03.4-1.02.97-.18 1.22l4.47 1.39L18.9 6.5c.66-.43 1.26-.2.77.26"
          />
        </svg>
      </div>

      <div className="wow-hero-ui-card wow-hero-ui-card--pie">
        <span className="wow-hero-ui-pie" />
      </div>

      <div className="wow-hero-mascot-glow" />
      <div className="wow-hero-mascot-platform" />

      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img
        className="wow-hero-mascot-image"
        src={src}
        alt=""
        width={480}
        height={480}
        loading="eager"
        decoding="async"
        draggable={false}
      />
    </div>
  );
}
