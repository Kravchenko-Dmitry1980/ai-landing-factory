"use client";

import { WOW_CAT_MASCOT_SRC } from "./wowMascotAsset";

interface Props {
  /** Override image src (bundle export uses a relative path). */
  src?: string;
  className?: string;
}

/**
 * Exhibition-grade hero mascot layer (Stage P.7.X).
 *
 * Sits on the right of the WOW hero as a composed scene: portal ring, pedestal,
 * soft glow and mini AI labels. Pure HTML/CSS — works in preview, WebGL
 * fallback and static export without a 3D pipeline.
 */
export function WowHeroMascot({ src = WOW_CAT_MASCOT_SRC, className }: Props) {
  return (
    <div
      className={["wow-hero-mascot", className].filter(Boolean).join(" ")}
      aria-hidden="true"
    >
      <div className="wow-hero-mascot-glow" />
      <div className="wow-hero-mascot-portal">
        <span className="wow-hero-mascot-ring" />
        <span className="wow-hero-mascot-ring wow-hero-mascot-ring--inner" />
      </div>
      <div className="wow-hero-mascot-pedestal">
        <span className="wow-hero-mascot-pedestal-tier wow-hero-mascot-pedestal-tier--1" />
        <span className="wow-hero-mascot-pedestal-tier wow-hero-mascot-pedestal-tier--2" />
      </div>
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
      <span className="wow-hero-mascot-float wow-hero-mascot-float--1">AI Assistant</span>
      <span className="wow-hero-mascot-float wow-hero-mascot-float--2">Neural scan</span>
      <span className="wow-hero-mascot-float wow-hero-mascot-float--3">Live</span>
    </div>
  );
}
