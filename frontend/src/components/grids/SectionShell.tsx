import { motion } from "framer-motion";
import { revealVariants } from "@/design/motion";
import type { RenderPlan } from "@/rendering/types";
import type { SectionType } from "@/rendering/types";

interface Props {
  plan: RenderPlan;
  sectionId: string;
  sectionType: SectionType;
  index: number;
  children: React.ReactNode;
}

export function SectionShell({ plan, sectionId, sectionType, index, children }: Props) {
  const width = plan.layout.sectionWidths[sectionType] ?? "full";
  const widthClass =
    width === "narrow"
      ? "max-w-3xl"
      : width === "wide"
        ? "max-w-6xl"
        : width === "split"
          ? "max-w-5xl"
          : "max-w-7xl";

  const { sectionY, containerPx } = plan.profile.spacing;
  const motionCfg = plan.profile.motion.sectionReveal;

  return (
    <motion.section
      id={sectionId}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-40px" }}
      variants={revealVariants}
      transition={{ duration: motionCfg.duration, delay: index * plan.profile.motion.staggerChildren }}
      className={`scroll-mt-16 ${sectionY} ${containerPx} mx-auto ${widthClass} w-full`}
    >
      {children}
    </motion.section>
  );
}
