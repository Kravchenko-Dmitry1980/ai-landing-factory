import { describe, expect, it } from "vitest";
import type { LandingContract, TeamMember } from "@/lib/types";
import {
  blockParts,
  buildLandingModel,
  descriptionOf,
  sameText,
  parseResult,
  prettyTimeline,
  splitHead,
  splitList,
  themeFromContract,
  themeFromProfile,
} from "./model";

function contract(overrides: Partial<LandingContract> = {}): LandingContract {
  return {
    project_id: "p1",
    status: "draft",
    style: "minimal",
    title: "Контроль операций по видео",
    client: "ООО «Пример»",
    timeline: "с 04 марта по 28 мая 2026 года",
    lead: "Иван Петров",
    quote: "",
    goals: [],
    presentation_style: null,
    style_config: { profile: "university_platform" },
    visual_assets: [],
    updated_at: "2026-10-24T10:00:00Z",
    version: 1,
    blocks: [
      { key: "tagline", title: "Фраза", content: "Камера сверяет действия с регламентом.", bullets: [] },
      { key: "essence", title: "Суть проекта", content: "Длинное описание проекта.", bullets: ["Отдельный пункт сути"] },
      { key: "tasks", title: "Задачи проекта", content: "", bullets: ["Data & Annotation: Гибридная разметка", "CV Core — детекция: Обучение модели"] },
      {
        key: "results",
        title: "Чего добились",
        content: "",
        bullets: [
          "Детекция объектов (YOLO v11 nano): mAP50 = 0.956, precision = 0.905.",
          "Классификация сцены (Random Forest): accuracy = 95.12%. Шесть классов.",
          "Автоматизация разметки (SAM 2): из 177 ручных кадров получено 4142 (ускорение ×4 без потерь).",
          "Движок правил: ложные срабатывания снижены с 97% до менее 5%. Семь состояний.",
          "Интерфейс v3.0: живой таймлайн и архив 7–30 дней.",
        ],
      },
      { key: "tech_stack", title: "Используемый технологический стек", content: "", bullets: ["Infrastructure: Docker (multi-stage, slim), Redis, Git"] },
      { key: "inputs", title: "Вводные данные", content: "", bullets: [""] },
      { key: "purpose", title: "Для чего", content: "", bullets: ["Создать систему, которая:", "Распознаёт этапы операции.", "Сценарий: важный пункт"] },
      { key: "outlook", title: "Перспектива развития", content: "Вступление к планам", bullets: ["1. Расширение — на все отделения"] },
    ],
    fidelity: { parser_mode: "structured", modules: [], tech_stack_grouped: {}, team_structured: [] },
    ...overrides,
  } as LandingContract;
}

const team: TeamMember[] = [
  { name: "Сидоров Олег", role: "Протестировал модели XGBoost, LightGBM и CatBoost на трёх выборках.", project_area: "", contributions: ["Провёл эксперименты"] },
  { name: "Петров Иван", role: "Тимлид", project_area: "", contributions: ["Руководство"] },
  { name: "Иванова Анна", role: "Научный руководитель, д.т.н., проф.", project_area: "", contributions: [] },
];

const value = (bullet: string) => {
  const r = parseResult(bullet);
  return r?.kind === "metric" ? r.metric.value : r?.kind === "change" ? `${r.change.beforeText} → ${r.change.afterText}` : null;
};

describe("parseResult", () => {
  it("reads known 0–1 metrics as a ring", () => {
    const r = parseResult("Детекция объектов (YOLO v11 nano): mAP50 = 0.956, precision = 0.905.");
    expect(r).toEqual({ kind: "metric", metric: expect.objectContaining({ value: "0,956", label: "Детекция объектов (YOLO v11 nano)", ring: 95.6 }) });
  });

  it("does not ring arbitrary decimals", () => {
    expect(parseResult("Обучение: loss = 0.45 на валидации")).toBeNull();
  });

  it("recognises changes written in different ways", () => {
    expect(value("Ложные срабатывания: снижены со 100% до 7%")).toBe("100% → 7%");
    expect(value("Точность: c 70% до 95%")).toBe("70% → 95%");
    expect(value("Точность: с 60% до более чем 90%")).toBe("60% → более 90%");
    expect(value("Ошибки: с 97% до примерно 5%")).toBe("97% → примерно 5%");
    expect(value("Ошибки: 97 % → 5 %")).toBe("97% → 5%");
    expect(value("Движок правил: снижены с 97% до менее 5%.")).toBe("97% → менее 5%");
  });

  it("never shows a starting value it could not pair with the result", () => {
    expect(parseResult("Ошибки: с 97% до 5–7 раз меньше")).toBeNull();
  });

  it("keeps signs and ranges and draws no ring for them", () => {
    expect(parseResult("Время ответа: −40%")).toEqual({ kind: "metric", metric: expect.objectContaining({ value: "-40%", ring: null }) });
    expect(parseResult("Скорость: выросла на 150%")).toEqual({ kind: "metric", metric: expect.objectContaining({ value: "150%", ring: null }) });
    expect(parseResult("Доля: 7–30% случаев")).toEqual({ kind: "metric", metric: expect.objectContaining({ value: "7–30%", ring: null }) });
    expect(parseResult("Качество: IoU = 0.5–0.7")).toEqual({ kind: "metric", metric: expect.objectContaining({ value: "0,5–0,7", ring: null }) });
  });

  it("reads ×N but not a frame size", () => {
    expect(value("Автоматизация разметки (SAM 2): из 177 кадров получено 4142 (ускорение ×4 без потерь).")).toBe("×4");
    expect(parseResult("Разрешение: камеры 1920 x 1080")).toBeNull();
  });

  it("drops a detail that only repeats the figure", () => {
    const r = parseResult("Точность: 95%");
    expect(r?.kind === "metric" && r.metric.detail).toBe("");
  });

  it("skips bullets without a real figure", () => {
    expect(parseResult("Интерфейс v3.0: живой таймлайн и архив 7–30 дней.")).toBeNull();
    expect(parseResult("Просто текст без цифр")).toBeNull();
  });
});

describe("helpers", () => {
  it("splits on a colon first, then on a spaced dash", () => {
    expect(splitHead("CV Core — детекция: Обучение")).toEqual(["CV Core — детекция", "Обучение"]);
    expect(splitHead("Расширение на отделения — масштабирование")).toEqual(["Расширение на отделения", "масштабирование"]);
    expect(splitHead("Без разделителя")).toEqual(["", "Без разделителя"]);
  });

  it("splits lists on top-level commas and keeps parentheses", () => {
    expect(splitList("Python (FastAPI, SQLAlchemy), PostgreSQL (pgvector), Git")).toEqual([
      "Python (FastAPI, SQLAlchemy)",
      "PostgreSQL (pgvector)",
      "Git",
    ]);
  });

  it("keeps block text that the items do not repeat", () => {
    expect(blockParts({ key: "x", title: "", content: "Абзац\nПункт", bullets: ["Пункт"] })).toEqual({ text: "Абзац", items: ["Пункт"] });
    expect(blockParts({ key: "x", title: "", content: "Только текст", bullets: [] })).toEqual({ text: "", items: ["Только текст"] });
    expect(blockParts({ key: "x", title: "", content: "", bullets: ["-30% времени"] }).items).toEqual(["-30% времени"]);
  });

  it("makes timelines readable", () => {
    expect(prettyTimeline("с 04 марта по 28 мая 2026 года")).toBe("4 марта — 28 мая 2026");
    expect(prettyTimeline("весна 2026")).toBe("весна 2026");
  });

  it("maps style profiles to themes, night by default, legacy style as a fallback", () => {
    expect(themeFromProfile(undefined)).toBe("night");
    expect(themeFromProfile("minimal")).toBe("light");
    expect(themeFromContract({ style_config: null, presentation_style: null, style: "minimal" })).toBe("light");
    expect(themeFromContract({ style_config: { profile: "tech" }, presentation_style: null, style: "minimal" })).toBe("night");
  });
});

describe("buildLandingModel", () => {
  const model = buildLandingModel(contract(), team);

  it("never repeats the title as the description under it", () => {
    const copy = contract({
      quote: "Контроль операций по видео",
      blocks: contract().blocks.map((b) => (b.key === "tagline" ? { ...b, content: "«Контроль операций по видео»" } : b)),
    });
    const hero = buildLandingModel(copy, team);
    expect(hero.description).not.toBe(hero.title);
    expect(sameText(hero.description, hero.title)).toBe(false);
    expect(descriptionOf("Эндокринология+", "", "Эндокринология+")).toBe("");
    expect(descriptionOf("Эндокринология+", "Эндокринология+", "Помогает врачу")).toBe("Помогает врачу");
    expect(sameText("Контроль операций!", "контроль  операций")).toBe(true);
    expect(sameText("", "")).toBe(false);
    // Nor through the first sentence of the essence, the last fallback.
    const echo = contract({
      quote: "",
      blocks: [{ key: "essence", title: "Суть", content: "Контроль операций по видео. Камера смотрит за кассой.", bullets: [] }],
    });
    expect(buildLandingModel(echo, team).description).toBe("");
  });

  it("builds the hero from title, tagline and facts", () => {
    expect(model.description).toBe("Камера сверяет действия с регламентом.");
    expect(model.facts.map((f) => f.value)).toEqual(["ООО «Пример»", "4 марта — 28 мая 2026", "Иван Петров"]);
  });

  it("separates metrics, the before/after change and plain notes", () => {
    expect(model.metrics.map((m) => m.value)).toEqual(["0,956", "95,12%", "×4"]);
    expect(model.beforeAfter?.beforeText).toBe("97%");
    expect(model.resultNotes.map((n) => n.title)).toEqual(["Интерфейс v3.0"]);
  });

  it("uses section titles the editor changed and short page titles otherwise", () => {
    expect(model.titles.results).toBe("Чего добились");
    expect(model.titles.stack).toBe("Технологии");
    expect(model.titles.about).toBe("Разработанное решение");
  });

  it("keeps steps, essence bullets, intros and numbered lines readable", () => {
    expect(model.steps.map((s) => s.title)).toEqual(["Data & Annotation", "CV Core — детекция"]);
    expect(model.essenceItems).toEqual(["Отдельный пункт сути"]);
    expect(model.purposeIntro).toBe("Создать систему, которая:");
    expect(model.outlookIntro).toBe("Вступление к планам");
    expect(model.outlook).toEqual([{ title: "Расширение", text: "на все отделения" }]);
  });

  it("does not cap the steps list", () => {
    const tasks = Array.from({ length: 10 }, (_, i) => `Шаг ${i + 1}: описание`);
    const many = buildLandingModel(
      contract({ blocks: [{ key: "tasks", title: "Задачи проекта", content: "", bullets: tasks }] }),
      [],
    );
    expect(many.steps).toHaveLength(10);
  });

  it("shows only the publishable team, lead first, roles kept unless they are sentences", () => {
    expect(model.team.map((p) => p.name)).toEqual(["Петров Иван", "Сидоров Олег", "Иванова Анна"]);
    expect(model.team[0]).toEqual(expect.objectContaining({ isLead: true, initials: "ПИ" }));
    expect(model.team[1]!.role).toBe("");
    expect(model.team[1]!.contributions[0]).toMatch(/^Протестировал модели/);
    expect(model.team[2]!.role).toBe("Научный руководитель, д.т.н., проф.");
  });

  it("shows no team when the publishable list is unavailable", () => {
    const withStructured = contract();
    withStructured.fidelity!.team_structured = team;
    expect(buildLandingModel(withStructured, null).team).toEqual([]);
  });

  it("recognises the lead despite a note in parentheses", () => {
    expect(buildLandingModel(contract({ lead: "Иван Петров (тимлид)" }), team).team[0]?.isLead).toBe(true);
  });

  it("drops empty sections", () => {
    expect(model.inputs).toEqual([]);
    expect(model.outputs).toEqual([]);
  });
});
