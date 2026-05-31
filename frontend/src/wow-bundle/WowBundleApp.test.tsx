import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { WowBundleApp } from "./WowBundleApp";
import { normalizeWowBundleData } from "./WowBundleData";

const DATA = normalizeWowBundleData({
  version: "1",
  project: { title: "Indlab News Intelligence", subtitle: "Realtime news analytics", client: "Indlab" },
  metrics: [
    { value: "37 000+", label: "постов", hint: "в корпусе" },
    { value: "17", label: "AI-моделей" },
    { value: "800+", label: "тем" },
    { value: "92%", label: "Accuracy" },
  ],
  pipeline: [
    { title: "Источники", tags: ["Telegram"] },
    { title: "AI-анализ", tags: ["E5", "LLM"] },
  ],
  modules: [{ title: "Semantic Engine", type: "ai", description: "E5 embeddings" }],
  stack: [{ group: "Storage", items: ["Qdrant", "Neo4j"] }],
  team: [{ name: "Lead ML", role: "ML Lead" }],
  links: { demo_url: "https://example.com/demo", showcase_url: "/showcase/1" },
  theme: { profile: "tech", accent: "#7c8bff", mode: "dark" },
});

function render() {
  // enable3d=false forces the static (no-WebGL) hero path, which is fully SSR-able.
  return renderToStaticMarkup(<WowBundleApp data={DATA} enable3d={false} reducedMotion />);
}

describe("WowBundleApp", () => {
  it("renders the project title", () => {
    expect(render()).toContain("Indlab News Intelligence");
  });

  it("renders metric values and labels", () => {
    const html = render();
    expect(html).toContain("37 000+");
    expect(html).toContain("Accuracy");
  });

  it("renders the pipeline stages", () => {
    const html = render();
    expect(html).toContain("Источники");
    expect(html).toContain("AI-анализ");
  });

  it("renders modules, stack and team", () => {
    const html = render();
    expect(html).toContain("Semantic Engine");
    expect(html).toContain("Qdrant");
    expect(html).toContain("Lead ML");
  });

  it("renders CTA links from project data", () => {
    const html = render();
    expect(html).toContain("https://example.com/demo");
    expect(html).toContain("/showcase/1");
  });

  it("renders a static hero fallback without WebGL (no canvas)", () => {
    const html = render();
    expect(html).toContain("wow-hero__static");
    expect(html).not.toContain("<canvas");
  });

  it("renders the cat mascot layer with bundle asset path", () => {
    const html = render();
    expect(html).toContain("wow-hero-mascot");
    expect(html).toContain("wow-hero-mascot-image");
    expect(html).toContain('src="assets/wow/cat-assistant.png"');
    expect(html).toContain("wow-bundle-cat-mascot-v1");
  });

  it("bundle renderer source has no portal arch or procedural robot", () => {
    const dir = dirname(fileURLToPath(import.meta.url));
    const src = readFileSync(join(dir, "WowBundleRenderer.tsx"), "utf-8");
    expect(src).not.toContain("function Assistant");
    expect(src).not.toContain("PhoneStage");
    expect(src).not.toContain("PortalArch");
    expect(src).not.toContain("torusGeometry");
  });

  it("does not break when links are missing", () => {
    const noLinks = normalizeWowBundleData({ project: { title: "X" }, metrics: [], pipeline: [] });
    const html = renderToStaticMarkup(
      <WowBundleApp data={noLinks} enable3d={false} reducedMotion />,
    );
    expect(html).toContain("X");
    expect(html).toContain("Демо-ссылка появится");
  });
});
