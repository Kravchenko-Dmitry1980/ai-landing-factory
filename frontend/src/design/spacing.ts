import type { StyleProfileId } from "./styleProfiles";

export interface SpacingScale {
  sectionY: string;
  sectionGap: string;
  containerPx: string;
  gridGap: string;
  cardPad: string;
}

export function getSpacingScale(profile: StyleProfileId): SpacingScale {
  const spacious: SpacingScale = {
    sectionY: "py-16 md:py-24",
    sectionGap: "gap-10 md:gap-14",
    containerPx: "px-4 md:px-8 lg:px-12",
    gridGap: "gap-8",
    cardPad: "p-6 md:p-8",
  };
  const normal: SpacingScale = {
    sectionY: "py-12 md:py-16",
    sectionGap: "gap-8 md:gap-10",
    containerPx: "px-4 md:px-8 lg:px-12",
    gridGap: "gap-6",
    cardPad: "p-5 md:p-6",
  };
  const compact: SpacingScale = {
    sectionY: "py-10 md:py-12",
    sectionGap: "gap-6 md:gap-8",
    containerPx: "px-4 md:px-8 lg:px-12",
    gridGap: "gap-4",
    cardPad: "p-4 md:p-5",
  };

  switch (profile) {
    case "minimal":
      return spacious;
    case "bold":
      return compact;
    case "tech":
    case "corporate":
    case "custom":
      return normal;
    case "university_platform":
    default:
      return normal;
  }
}
