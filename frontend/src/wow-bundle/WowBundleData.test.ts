import { describe, expect, it } from "vitest";
import {
  buildSceneNodes,
  classifyKind,
  normalizeWowBundleData,
  safeLink,
  type WowBundleData,
} from "./WowBundleData";

const SAMPLE = {
  version: "1",
  project: { title: "Indlab News Intelligence", subtitle: "Realtime analytics", client: "Indlab" },
  metrics: [
    { value: "37 000+", label: "постов" },
    { value: "17", label: "AI-моделей" },
    { value: "800+", label: "тем" },
    { value: "92%", label: "Accuracy" },
  ],
  pipeline: [
    { title: "Источники", tags: ["Telegram"] },
    { title: "AI-анализ", tags: ["E5"] },
  ],
  modules: [{ title: "Semantic Engine", type: "ai" }],
  stack: [{ group: "Storage", items: ["Qdrant", "Neo4j"] }],
  team: [{ name: "Lead ML", role: "ML Lead" }],
  links: { demo_url: "https://example.com/demo" },
  theme: { profile: "tech", accent: "#7c8bff", mode: "dark" },
};

describe("normalizeWowBundleData", () => {
  it("preserves valid payload fields", () => {
    const data = normalizeWowBundleData(SAMPLE);
    expect(data.project.title).toBe("Indlab News Intelligence");
    expect(data.metrics).toHaveLength(4);
    expect(data.pipeline).toHaveLength(2);
    expect(data.stack[0].items).toContain("Qdrant");
  });

  it("never throws and returns defaults for garbage input", () => {
    const data = normalizeWowBundleData(null);
    expect(data.project.title).toBe("AI-проект");
    expect(data.metrics).toEqual([]);
    expect(data.theme.accent).toBe("#7c8bff");
  });

  it("drops empty stack groups and unnamed team members", () => {
    const data = normalizeWowBundleData({
      stack: [{ group: "Empty", items: [] }],
      team: [{ role: "ghost" }],
    });
    expect(data.stack).toEqual([]);
    expect(data.team).toEqual([]);
  });

  it("falls back to default accent for invalid hex", () => {
    const data = normalizeWowBundleData({ theme: { accent: "not-a-color" } });
    expect(data.theme.accent).toBe("#7c8bff");
  });
});

describe("safeLink", () => {
  it("accepts http(s) and relative links", () => {
    expect(safeLink("https://x.dev")).toBe("https://x.dev");
    expect(safeLink("/showcase/1")).toBe("/showcase/1");
  });

  it("rejects javascript: / data: / file:", () => {
    expect(safeLink("javascript:alert(1)")).toBeUndefined();
    expect(safeLink("data:text/html,x")).toBeUndefined();
    expect(safeLink("file:///etc/passwd")).toBeUndefined();
  });
});

describe("buildSceneNodes", () => {
  it("derives nodes from modules", () => {
    const data = normalizeWowBundleData(SAMPLE) as WowBundleData;
    const nodes = buildSceneNodes(data);
    expect(nodes.length).toBeGreaterThan(0);
    expect(nodes.some((n) => n.label.includes("Semantic"))).toBe(true);
  });

  it("provides generic nodes when no data", () => {
    const data = normalizeWowBundleData(null);
    const nodes = buildSceneNodes(data);
    expect(nodes.length).toBeGreaterThanOrEqual(4);
  });
});

describe("classifyKind", () => {
  it("maps keywords to kinds", () => {
    expect(classifyKind("Qdrant vector store")).toBe("storage");
    expect(classifyKind("LLM embeddings")).toBe("ml");
    expect(classifyKind("Telegram parser")).toBe("data");
  });
});
