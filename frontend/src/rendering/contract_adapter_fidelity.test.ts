import { describe, expect, it } from "vitest";
import { normalizeBulletText } from "@/lib/normalizeBulletText";
import type {
  FidelityMetadata,
  GeneratedLanding,
  LandingContract,
  LandingModule,
  TeamMember,
} from "@/lib/types";
import { buildRenderPlan } from "./contract_adapter";
import {
  buildFidelityData,
  resolveGroupedStack,
  resolveStructuredModules,
  resolveStructuredTeam,
} from "./fidelity_resolver";

const ENDO_MODULES: LandingModule[] = [
  { name: "GlaucoLogic", description: "OCT analysis", type: "AI system" },
  { name: "Copilot врача", description: "Documentation copilot", type: "AI platform" },
  { name: "VitaCalc", description: "Nutrition calc", type: "Calculator" },
];

const ENDO_TEAM: TeamMember[] = Array.from({ length: 16 }, (_, i) => ({
  name: `Member ${i + 1}`,
  role: "Developer",
  project_area: "Backend",
  contributions: ["● ● Task one", "Task two"],
}));

const ENDO_STACK: Record<string, string[]> = {
  "AI / LLM": ["OpenAI", "LangChain"],
  "Backend / API": ["FastAPI", "PostgreSQL"],
  "Frontend": ["Next.js"],
  "Data": ["Redis"],
  "Infra": ["Docker"],
};

const fidelity: FidelityMetadata = {
  parser_mode: "structured",
  modules: ENDO_MODULES,
  team_structured: ENDO_TEAM,
  tech_stack_grouped: ENDO_STACK,
};

const landing: GeneratedLanding = {
  project_id: "00000000-0000-0000-0000-000000000001",
  style: "corporate",
  generated_at: new Date().toISOString(),
  prompt_version: "stub",
  blocks: [
    { key: "tagline", title: "Tagline", body: "Tag", bullets: [] },
    { key: "tasks", title: "Tasks", body: "", bullets: ["Fallback module"] },
    { key: "team", title: "Team", body: "", bullets: ["Plain — role"] },
    { key: "tech_stack", title: "Stack", body: "", bullets: ["Python"] },
  ],
};

const contract: LandingContract = {
  project_id: landing.project_id,
  status: "draft",
  style: "corporate",
  title: "Эндокринология+",
  client: "Client",
  goals: [],
  presentation_style: null,
  visual_assets: [],
  blocks: [],
  fidelity,
  updated_at: landing.generated_at,
  version: 1,
};

describe("fidelity resolver", () => {
  it("prefers fidelity.modules over blocks", () => {
    const res = resolveStructuredModules(contract, null, landing);
    expect(res.source).toBe("fidelity");
    expect(res.data.map((m) => m.name)).toEqual([
      "GlaucoLogic",
      "Copilot врача",
      "VitaCalc",
    ]);
  });

  it("prefers fidelity.team_structured over blocks", () => {
    const res = resolveStructuredTeam(contract, landing);
    expect(res.source).toBe("fidelity");
    expect(res.data.length).toBe(16);
  });

  it("prefers grouped tech_stack over flat bullets", () => {
    const res = resolveGroupedStack(contract, landing);
    expect(res.source).toBe("fidelity");
    expect(Object.keys(res.data).length).toBe(5);
  });

  it("falls back to blocks when fidelity empty", () => {
    const emptyContract = { ...contract, fidelity: undefined };
    const mod = resolveStructuredModules(emptyContract, null, landing);
    expect(mod.source).toBe("blocks");
  });
});

describe("buildRenderPlan fidelity parity", () => {
  it("includes structured data on render plan", () => {
    const plan = buildRenderPlan(landing, contract, {
      profileId: "university_platform",
      layoutId: "architecture_first",
    });
    expect(plan.modules).toHaveLength(3);
    expect(plan.team.length).toBeGreaterThanOrEqual(15);
    expect(plan.fidelityDiagnostics.modulesSource).toBe("fidelity");
    expect(plan.fidelityDiagnostics.teamSource).toBe("fidelity");
    expect(plan.fidelityDiagnostics.stackSource).toBe("fidelity");
    expect(plan.fidelityDiagnostics.stackCategoriesCount).toBe(5);
  });

  it("normalizes bullets in sections", () => {
    const landingWithBullets: GeneratedLanding = {
      ...landing,
      blocks: [
        ...landing.blocks,
        {
          key: "purpose",
          title: "Purpose",
          body: "",
          bullets: ["● ● First", "● Second"],
        },
      ],
    };
    const plan = buildRenderPlan(landingWithBullets, contract, {
      profileId: "corporate",
      layoutId: "architecture_first",
    });
    const purpose = plan.sections.find((s) => s.sourceKeys.includes("purpose"));
    expect(purpose?.bullets).toEqual(["First", "Second"]);
  });
});

describe("buildFidelityData diagnostics", () => {
  it("reports counts for endocrinology-like contract", () => {
    const data = buildFidelityData(contract, null, landing);
    expect(data.diagnostics.modulesCount).toBe(3);
    expect(data.diagnostics.teamCount).toBe(16);
    expect(data.diagnostics.stackCategoriesCount).toBe(5);
  });
});

describe("normalizeBulletText", () => {
  it("removes duplicate markers", () => {
    expect(normalizeBulletText("● ● Task")).toBe("Task");
  });
});
