import type { StyleProfileId } from "./style_profiles";

export interface SpacingScale {
  sectionY: string;
  sectionGap: string;
  containerPx: string;
  gridGap: string;
  cardPad: string;
}

export function getSpacingScale(profile: StyleProfileId): SpacingScale {
  if (profile === "university_platform") {
    return {
      sectionY: "py-12 md:py-16",
      sectionGap: "gap-8 md:gap-10",
      containerPx: "px-4 md:px-8 lg:px-12",
      gridGap: "gap-6",
      cardPad: "p-5 md:p-6",
    };
  }
  const dense = profile === "medical" || profile === "ai_research" || profile === "enterprise";
  return {
    sectionY: dense ? "py-10 md:py-12" : "py-12 md:py-16",
    sectionGap: dense ? "gap-6 md:gap-8" : "gap-8 md:gap-10",
    containerPx: "px-4 md:px-8 lg:px-12",
    gridGap: dense ? "gap-4" : "gap-6",
    cardPad: dense ? "p-4 md:p-5" : "p-5 md:p-6",
  };
}
