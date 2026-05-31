import { describe, expect, it } from "vitest";
import { buildWowHeroData, NODE_KIND_COLOR } from "./wowHeroMapping";
import type {
  GeneratedLanding,
  GeneratedSemanticLanding,
  LandingContract,
} from "./types";

function landing(blocks: Array<{ key: string; title?: string; body?: string; bullets?: string[] }>): GeneratedLanding {
  return {
    project_id: "p1",
    style: "tech",
    blocks: blocks.map((b) => ({
      key: b.key,
      title: b.title ?? "",
      body: b.body ?? "",
      bullets: b.bullets ?? [],
    })),
    generated_at: "now",
    prompt_version: "v1",
  };
}

function contract(overrides: Partial<LandingContract> = {}): LandingContract {
  return {
    project_id: "p1",
    status: "ready",
    style: "tech",
    title: "Intelligence Platform",
    client: "УИИ",
    timeline: "2024 Q1–Q3",
    lead: "Иванов И.",
    quote: null,
    goals: [],
    presentation_style: null,
    visual_assets: [],
    blocks: [],
    updated_at: "now",
    version: 1,
    ...overrides,
  };
}

const richFidelity = {
  parser_mode: "structured",
  modules: [
    { name: "Telegram Scraper", description: "сбор источников", type: "data" },
    { name: "Embedding Service", description: "E5 эмбеддинги", type: "ml" },
    { name: "Qdrant Storage", description: "vector база", type: "storage" },
    { name: "Digest Dashboard", description: "дашборд отчётов", type: "ui" },
  ],
  team_structured: [
    { name: "A", role: "lead", project_area: "ml", contributions: [] },
    { name: "B", role: "dev", project_area: "be", contributions: [] },
  ],
  tech_stack_grouped: {
    backend: ["FastAPI", "Postgres"],
    ml: ["E5", "BERT"],
  },
};

describe("buildWowHeroData", () => {
  it("derives title, chips and subtitle from contract", () => {
    const data = buildWowHeroData(
      landing([{ key: "essence", body: "Система анализа корпуса сообщений." }]),
      contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] }),
      null,
    );
    expect(data.title).toBe("Intelligence Platform");
    expect(data.subtitle).toContain("Система анализа");
    const chipLabels = data.chips.map((c) => c.label);
    expect(chipLabels).toEqual(expect.arrayContaining(["Клиент", "Период", "Лид"]));
  });

  it("maps modules to nodes with kinds and limits to 8", () => {
    const data = buildWowHeroData(
      landing([]),
      contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] }),
      null,
    );
    expect(data.nodes.length).toBe(4);
    const labels = data.nodes.map((n) => n.label);
    expect(labels).toContain("Telegram Scraper");
    const kinds = data.nodes.map((n) => n.kind);
    expect(kinds).toContain("data");
    expect(kinds).toContain("ml");
    expect(kinds).toContain("storage");
    expect(kinds).toContain("ui");
    for (const n of data.nodes) {
      expect(NODE_KIND_COLOR[n.kind]).toMatch(/^#/);
    }
  });

  it("derives metric counts from fidelity and tasks", () => {
    const data = buildWowHeroData(
      landing([{ key: "tasks", bullets: ["t1", "t2", "t3"] }]),
      contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] }),
      null,
    );
    const byLabel = Object.fromEntries(data.metrics.map((m) => [m.label, m.value]));
    expect(byLabel["Подсистем"]).toBe("4");
    expect(byLabel["Команда"]).toBe("2");
    expect(byLabel["Технологий"]).toBe("4");
    expect(byLabel["Задач"]).toBe("3");
    expect(data.metrics.length).toBeGreaterThanOrEqual(4);
    expect(data.metrics.length).toBeLessThanOrEqual(6);
  });

  it("extracts impact numbers from text", () => {
    const data = buildWowHeroData(
      landing([{ key: "essence", body: "Обработано 37 000+ постов из 800+ каналов." }]),
      contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] }),
      null,
    );
    const values = data.metrics.map((m) => m.value);
    expect(values).toContain("37 000+");
  });

  it("builds a 5-stage pipeline when signal is strong", () => {
    const data = buildWowHeroData(
      landing([]),
      contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] }),
      null,
    );
    expect(data.pipeline.length).toBe(5);
    const titles = data.pipeline.map((p) => p.title);
    expect(titles).toContain("AI-анализ");
  });

  it("gracefully falls back with empty data", () => {
    const data = buildWowHeroData(landing([]), null, null);
    expect(data.title).toBe("AI-проект");
    expect(data.nodes.length).toBeGreaterThan(0);
    expect(data.metrics.length).toBeGreaterThanOrEqual(4);
    expect(data.pipeline.length).toBe(5);
    expect(data.chips).toEqual([]);
  });

  it("prefers semantic narrative for subtitle when present", () => {
    const semantic = {
      narrative: { system: "Семантический поиск по корпусу." },
      sections: [],
    } as unknown as GeneratedSemanticLanding;
    const data = buildWowHeroData(landing([]), contract(), semantic);
    expect(data.subtitle).toContain("Семантический поиск");
  });

  it("is deterministic for identical input", () => {
    const c = contract({ fidelity: richFidelity as unknown as LandingContract["fidelity"] });
    const a = buildWowHeroData(landing([]), c, null);
    const b = buildWowHeroData(landing([]), c, null);
    expect(JSON.stringify(a)).toEqual(JSON.stringify(b));
  });
});
