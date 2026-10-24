import { describe, expect, it } from "vitest";
import type { LandingModel } from "./model";
import { changePhrase, esc, plural, renderLandingHtml } from "./render";
import { runTiming } from "./styles";

const assets = {
  fontFaces: "@font-face{font-family:x}",
  catMark: "data:image/webp;base64,MARK",
  catHero: "data:image/webp;base64,HERO",
};

function model(overrides: Partial<LandingModel> = {}): LandingModel {
  return {
    title: "Контроль операций",
    description: "Камера сверяет действия с регламентом.",
    facts: [{ label: "Заказчик", value: "ООО «Пример»" }],
    titles: {
      results: "Результаты",
      about: "О проекте",
      purpose: "Зачем это нужно",
      inputs: "Что получает",
      outputs: "Что выдаёт",
      work: "Что сделали",
      stack: "Технологии",
      outlook: "Что дальше",
    },
    essence: "",
    essenceItems: [],
    purposeIntro: "",
    purpose: [],
    inputs: [],
    outputs: [],
    workIntro: "",
    steps: [
      { title: "Разметка", text: "Гибридная разметка" },
      { title: "Детекция", text: "YOLO" },
      { title: "Правила", text: "FSM" },
    ],
    metrics: [{ value: "95,12%", label: "Классификация сцены", detail: "accuracy", ring: 95.12 }],
    beforeAfter: null,
    resultsIntro: "",
    resultNotes: [],
    stack: [],
    team: [],
    outlookIntro: "",
    outlook: [],
    ...overrides,
  };
}

describe("renderLandingHtml", () => {
  it("escapes text from documents and never emits scripts", () => {
    const html = renderLandingHtml(model({ title: `<script>alert(1)</script>`, description: `" onmouseover="x` }), {
      theme: "night",
      assets,
    });
    expect(html).not.toMatch(/<script/i);
    expect(html).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(html).toContain('content="&quot; onmouseover=&quot;x"');
  });

  it("sets the theme, embeds fonts, and embeds the large cat once", () => {
    const html = renderLandingHtml(model(), { theme: "light", assets });
    expect(html).toContain('<html lang="ru" data-theme="light">');
    expect(html).toContain("@font-face{font-family:x}");
    expect(html).toContain('src="data:image/webp;base64,MARK"');
    expect(html.split("base64,HERO")).toHaveLength(2);
  });

  it("animates the screen for at most eight steps but lists every step", () => {
    const steps = Array.from({ length: 10 }, (_, i) => ({ title: `Шаг ${i + 1}`, text: "" }));
    const html = renderLandingHtml(model({ steps }), { theme: "night", assets });
    expect(html.match(/class="run__step run__step--\d"/g)).toHaveLength(8);
    expect(html).toContain("<h3>Шаг 10</h3>");
    expect(html).toContain('aria-label="Схема проекта: 8 этапов"');
  });

  it("names the screen with the right word form and shows the best metric", () => {
    const html = renderLandingHtml(model(), { theme: "night", assets });
    expect(html).toContain('aria-label="Схема проекта: 3 этапа"');
    expect(html).toContain('<div class="toast"><b>95,12%</b>');
  });

  it("uses the section titles from the model", () => {
    const html = renderLandingHtml(model({ titles: { ...model().titles, results: "Чего добились" } }), { theme: "night", assets });
    expect(html).toContain("<h2>Чего добились</h2>");
    expect(html).toContain('<a href="#results">Чего добились</a>');
  });

  it("drops sections that have no content", () => {
    const html = renderLandingHtml(model({ metrics: [], steps: [] }), { theme: "night", assets });
    expect(html).not.toContain('id="results"');
    expect(html).not.toContain('class="screen"');
    expect(html).not.toContain('id="team"');
    expect(html).not.toContain('href="#results"');
  });
});

describe("helpers", () => {
  const base = { label: "", beforeText: "", afterText: "", detail: "" };

  it("phrases a before/after change without rounding the effect up", () => {
    expect(changePhrase({ ...base, before: 97, after: 5 })).toBe("более чем в 19 раз меньше");
    expect(changePhrase({ ...base, before: 10, after: 40 })).toBe("в 4 раза больше");
    expect(changePhrase({ ...base, before: 30, after: 10 })).toBe("в 3 раза меньше");
    expect(changePhrase({ ...base, before: 10, after: 4.5 })).toBe("более чем в 2 раза меньше");
    expect(changePhrase({ ...base, before: 32, after: 10 })).toBe("более чем в 3 раза меньше");
    expect(changePhrase({ ...base, before: 10, after: 9 })).toBe("");
  });

  it("declines Russian nouns by number", () => {
    expect([1, 3, 11, 22, 25].map((n) => plural(n, "человек", "человека", "человек"))).toEqual([
      "человек",
      "человека",
      "человек",
      "человека",
      "человек",
    ]);
  });

  it("escapes all HTML-significant characters", () => {
    expect(esc(`<a href="x">'&'</a>`)).toBe("&lt;a href=&quot;x&quot;&gt;&#39;&amp;&#39;&lt;/a&gt;");
  });

  it("times every step inside one cycle", () => {
    const t = runTiming(8);
    expect(t.stepAt).toHaveLength(8);
    expect(Math.max(...t.stepAt)).toBeLessThan(80);
  });
});
