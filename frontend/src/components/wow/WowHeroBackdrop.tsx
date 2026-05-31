"use client";

/**
 * Light 2D hero backdrop (Stage P.7.6).
 *
 * Soft lavender gradients and subtle dot particles — no 3D rings, portal,
 * constellation or sci-fi grid. The cat mascot PNG is the only "3D" visual.
 */
export function WowHeroBackdrop() {
  return (
    <div className="wow-hero-backdrop" aria-hidden="true">
      <div className="wow-hero-aurora" />
      <div className="wow-hero-dots" />
    </div>
  );
}
