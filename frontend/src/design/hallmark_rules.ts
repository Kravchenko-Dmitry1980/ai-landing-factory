import type { RenderPlan } from "@/rendering/types";

export type HallmarkSeverity = "info" | "warning" | "error";

export interface HallmarkViolation {
  ruleId: string;
  message: string;
  severity: HallmarkSeverity;
  sectionId?: string;
}

const GRADIENT_PATTERN =
  /gradient|from-[a-z]+-\d+|to-[a-z]+-\d+|bg-gradient|neon|glow|shadow-\[0_0/i;

export function runHallmarkQualityGate(plan: RenderPlan): HallmarkViolation[] {
  const violations: HallmarkViolation[] = [];
  const sections = plan.sections;

  if (sections.length < 3) {
    violations.push({
      ruleId: "density-low",
      message: "Low information density: fewer than 3 sections rendered.",
      severity: "warning",
    });
  }

  const hero = sections.find((s) => s.type === "hero");
  if (hero) {
    const heroLen = (hero.body?.length ?? 0) + hero.bullets.join(" ").length;
    if (heroLen > 420) {
      violations.push({
        ruleId: "hero-oversized",
        message: "Hero copy exceeds recommended length (420 chars).",
        severity: "warning",
        sectionId: hero.id,
      });
    }
    if (heroLen < 24 && !plan.meta.title) {
      violations.push({
        ruleId: "hero-empty",
        message: "Hero lacks title and substantive copy.",
        severity: "warning",
        sectionId: hero.id,
      });
    }
  }

  const cardSections = sections.filter((s) =>
    ["modules", "team", "metrics"].includes(s.type),
  );
  if (cardSections.length >= 3) {
    const similarTitles = cardSections.map((s) => s.title).join("|");
    if (
      cardSections.every((s) => s.bullets.length >= 4) &&
      new Set(cardSections.map((s) => s.bullets.length)).size === 1
    ) {
      violations.push({
        ruleId: "card-repetition",
        message: "Repeated card grids with identical bullet counts — SaaS pattern risk.",
        severity: "warning",
      });
    }
    void similarTitles;
  }

  const allText = sections
    .map((s) => `${s.title} ${s.body ?? ""} ${s.bullets.join(" ")}`)
    .join(" ");
  if (GRADIENT_PATTERN.test(allText)) {
    violations.push({
      ruleId: "gradient-copy",
      message: "Content references gradient/glow styling — avoid in renderer classes.",
      severity: "info",
    });
  }

  const h2Count = sections.filter((s) => s.title.length > 0).length;
  if (h2Count > 0 && sections.some((s) => !s.title)) {
    violations.push({
      ruleId: "typography-hierarchy",
      message: "Some sections missing titles — weak hierarchy.",
      severity: "info",
    });
  }

  if (plan.profile.motion.intensity === "moderate" && sections.length > 8) {
    violations.push({
      ruleId: "motion-heavy",
      message: "Many sections with moderate motion — prefer subtle for enterprise.",
      severity: "info",
    });
  }

  return violations;
}

export function runArchitectureHallmarkGate(plan: RenderPlan): HallmarkViolation[] {
  const violations: HallmarkViolation[] = [];
  const topo = plan.architecture;
  if (!topo) return violations;

  if (topo.edge_count > topo.node_count * 2.5) {
    violations.push({
      ruleId: "diagram-excessive-arrows",
      message: "Excessive arrows — topology may appear chaotic.",
      severity: "warning",
    });
  }

  if (topo.graph_density > 0.35) {
    violations.push({
      ruleId: "diagram-density-high",
      message: "High graph density — simplify topology for enterprise clarity.",
      severity: "warning",
    });
  }

  const inferredRatio = topo.nodes.filter((n) => n.inferred).length / Math.max(topo.node_count, 1);
  if (inferredRatio > 0.6) {
    violations.push({
      ruleId: "diagram-weak-grounding",
      message: "Majority inferred nodes — weak hierarchy / grounding.",
      severity: "info",
    });
  }

  if (topo.node_count > 150) {
    violations.push({
      ruleId: "diagram-node-limit",
      message: "Node count exceeds 150 — performance degradation risk.",
      severity: "error",
    });
  }

  return violations;
}

export function logHallmarkViolations(violations: HallmarkViolation[]): void {
  if (violations.length === 0) return;
  const label = "[Hallmark Quality Gate]";
  for (const v of violations) {
    const fn =
      v.severity === "error"
        ? console.error
        : v.severity === "warning"
          ? console.warn
          : console.info;
    fn(`${label} ${v.ruleId}: ${v.message}`);
  }
}
