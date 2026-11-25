/**
 * The single rendering engine of the landing: model → complete standalone HTML document.
 * The preview iframe and the downloaded file are the same bytes from this function.
 * No scripts: the page is static, and every piece of text is escaped.
 */

import type { BeforeAfter, LandingModel, LandingTheme, Metric, Person, Point } from "./model";
import { landingCss, runTiming } from "./styles";
import { plural } from "@/lib/plural";

export { plural };

export interface LandingAssets {
  /** @font-face rules for Geologica and Golos Text (data URIs in the downloaded file). */
  fontFaces: string;
  /** Small UII cat for the header (data URI). */
  catMark: string;
  /** Large UII cat for the hero card and the footer (data URI). */
  catHero: string;
}

/** Steps drawn on the hero card. The "Что сделали" section lists every step. */
export const SCREEN_STEPS = 5;
/** The share page replaces this with the demo player. It stays a comment when there is no video. */
export const DEMO_MARKER = "<!--demo-->";
/** A point this short reads as a card heading; a longer one stays a paragraph. */
const SHORT_POINT = 70;

export function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

/** "в 20 раз меньше" / "более чем в 19 раз меньше": never rounds the effect up; "" when it is small. */
export function changePhrase(c: BeforeAfter): string {
  const [hi, lo] = c.before >= c.after ? [c.before, c.after] : [c.after, c.before];
  if (lo <= 0 || hi / lo < 1.5) return "";
  const factor = hi / lo;
  const word = c.after < c.before ? "меньше" : "больше";
  const times = (n: number) => `${n} ${plural(n, "раз", "раза", "раз")}`;
  const rounded = Math.round(factor);
  return Math.abs(factor - rounded) <= 0.15
    ? `в ${times(rounded)} ${word}`
    : `более чем в ${times(Math.floor(factor))} ${word}`;
}

function paragraphs(text: string, lead = false): string {
  return text
    .split(/\r?\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p, i) => `<p${lead && i === 0 ? ' class="section-intro"' : ""}>${esc(p)}</p>`)
    .join("");
}

function point(p: Point): string {
  return p.title ? `<li><strong>${esc(p.title)}.</strong> ${esc(p.text)}</li>` : `<li>${esc(p.text)}</li>`;
}

function num(i: number): string {
  return String(i + 1).padStart(2, "0");
}

function hero(model: LandingModel, hasResults: boolean, hasTeam: boolean, catHero: string): string {
  const facts = model.facts
    .map((f) => `<div><small>${esc(f.label)}</small><strong>${esc(f.value)}</strong></div>`)
    .join("");
  const shown = model.steps.slice(0, SCREEN_STEPS);
  const client = model.facts.find((f) => f.label === "Заказчик")?.value || "Проект";
  const steps = shown
    .map(
      (s, i) =>
        `<div class="step"><span><i></i>${esc(s.title)}</span><small>${num(i)}</small></div>`,
    )
    .join("");
  const visual = shown.length
    ? `<div class="visual"><div class="workflow"><div class="workflow-head"><span>${esc(client)}</span><span class="status"><i class="dot"></i> Основной контур</span></div>${steps}<img class="mascot" src="${esc(catHero)}" alt="Котик УИИ с ноутбуком"></div></div>`
    : "";
  const actions = [
    `<a class="btn primary" href="#demo" hidden>Смотреть демо</a>`,
    hasResults ? `<a class="btn" href="#results">Результаты</a>` : "",
    hasTeam ? `<a class="btn" href="#team">Команда проекта</a>` : "",
  ].join("");
  return `<section class="hero" id="top"><div class="wrap hero-grid"><div><div class="kicker">Практический AI-проект · портфолио команды</div><h1>${esc(model.title)}</h1>${
    model.description ? `<p class="subtitle">${esc(model.description)}</p>` : ""
  }${
    facts ? `<div class="meta">${facts}</div>` : ""
  }${actions ? `<div class="actions">${actions}</div>` : ""}</div>${visual}</div></section>`;
}

function problem(model: LandingModel): string {
  if (model.purpose.length === 0 && !model.purposeIntro) return "";
  // A point without its own heading is the heading: a card never repeats the section title.
  const card = (p: Point, i: number) => {
    const body = p.title
      ? `<h3>${esc(p.title)}</h3>${p.text ? `<p>${esc(p.text)}</p>` : ""}`
      : p.text.length <= SHORT_POINT
        ? `<h3>${esc(p.text.replace(/\.$/, ""))}</h3>`
        : `<p>${esc(p.text)}</p>`;
    return `<div class="box"><span class="num">${num(i)}</span>${body}</div>`;
  };
  const cards = model.purpose.map(card).join("");
  return `<section class="section" id="problem"><div class="wrap"><div class="kicker">Контекст</div><h2>${esc(model.titles.purpose)}</h2>${
    model.purposeIntro ? `<p class="section-intro">${esc(model.purposeIntro)}</p>` : ""
  }${cards ? `<div class="problem">${cards}</div>` : ""}</div></section>`;
}

/**
 * The heading and the explanation stay on the left. The card on the right starts on the same
 * line as the heading, not under it.
 */
function solution(model: LandingModel): string {
  const hasText = Boolean(model.essence) || model.essenceItems.length > 0;
  const pipes = model.steps.slice(0, 6);
  const sideItems = model.outputs.length > 0 ? model.outputs : model.inputs;
  const sideTitle = model.outputs.length > 0 ? model.titles.outputs : model.titles.inputs;
  if (!hasText && sideItems.length === 0 && pipes.length === 0) return "";
  const list = (items: string[]) =>
    items.length ? `<ul>${items.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>` : "";
  const extraInputs =
    model.outputs.length > 0 && model.inputs.length > 0
      ? `<h3 class="sub">${esc(model.titles.inputs)}</h3>${list(model.inputs)}`
      : "";
  const body = `${paragraphs(model.essence, true)}${list(model.essenceItems)}${extraInputs}`;
  const text = body ? `<div class="text">${body}</div>` : "";
  const card = sideItems.length
    ? `<div class="box"><h3>${esc(sideTitle)}</h3>${list(sideItems)}</div>`
    : "";
  const heading = `<h2>${esc(model.titles.about)}</h2>`;
  const columns = card ? `<div class="solution">${heading}${text}${card}</div>` : `${heading}${text}`;
  const pipeline = pipes.length
    ? `<div class="pipeline">${pipes
      .map((s, i) => `<div class="pipe"><b>${num(i)}</b>${esc(s.title)}</div>`)
      .join("")}</div>`
    : "";
  return `<section class="section alt" id="solution"><div class="wrap"><div class="kicker">Подход</div>${columns}${pipeline}</div></section>`;
}

function features(model: LandingModel): string {
  if (model.steps.length === 0 && !model.workIntro) return "";
  const cards = model.steps
    .map(
      (s, i) =>
        `<article class="feature"><small>${num(i)}</small><h3>${esc(s.title)}</h3>${s.text ? `<p>${esc(s.text)}</p>` : ""}</article>`,
    )
    .join("");
  return `<section class="section alt" id="work"><div class="wrap"><div class="kicker">Реализация</div><h2>${esc(model.titles.work)}</h2>${
    model.workIntro ? `<p class="section-intro">${esc(model.workIntro)}</p>` : ""
  }${cards ? `<div class="features">${cards}</div>` : ""}</div></section>`;
}

function metricCard(m: Metric): string {
  return `<div class="metric"><span class="kind">${esc(m.label)}</span><strong>${esc(m.value)}</strong>${
    m.detail ? `<p>${esc(m.detail)}</p>` : ""
  }</div>`;
}

function changeCard(c: BeforeAfter): string {
  const phrase = changePhrase(c);
  const detail = [phrase, c.detail].filter(Boolean).join(". ");
  return `<div class="metric"><span class="kind">${esc(c.label)}</span><strong>${esc(c.beforeText)} → ${esc(c.afterText)}</strong>${
    detail ? `<p>${esc(detail)}</p>` : ""
  }</div>`;
}

function results(model: LandingModel): string {
  const cards = [model.beforeAfter ? changeCard(model.beforeAfter) : "", ...model.metrics.map(metricCard)].join("");
  if (!cards && model.resultNotes.length === 0 && !model.resultsIntro) return "";
  const notes = model.resultNotes.length
    ? `<p class="smallprint">${model.resultNotes.map((p) => esc(p.title ? `${p.title}. ${p.text}` : p.text)).join(" ")}</p>`
    : "";
  return `<section class="section" id="results"><div class="wrap"><div class="kicker">Проверки</div><h2>${esc(model.titles.results)}</h2>${
    model.resultsIntro ? `<p class="section-intro">${esc(model.resultsIntro)}</p>` : ""
  }${cards ? `<div class="results">${cards}</div>` : ""}${notes}</div></section>`;
}

function stack(model: LandingModel): string {
  if (model.stack.length === 0) return "";
  const tags = model.stack
    .flatMap((g) => g.items)
    .map((item) => `<span class="tag">${esc(item)}</span>`)
    .join("");
  const boxes = model.stack
    .filter((g) => g.name && g.name !== "Технологии")
    .map((g) => `<div class="box"><h3>${esc(g.name)}</h3><ul>${g.items.map((item) => `<li>${esc(item)}</li>`).join("")}</ul></div>`)
    .join("");
  return `<section class="section alt" id="tech"><div class="wrap"><div class="kicker">Инженерная часть</div><h2>${esc(model.titles.stack)}</h2><div class="tags">${tags}</div>${
    boxes ? `<div class="grid2">${boxes}</div>` : ""
  }</div></section>`;
}

function personCard(p: Person, index: number): string {
  const contributions = p.contributions.length
    ? `<details><summary>Личный вклад в проект</summary><ul>${p.contributions.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></details>`
    : "";
  return `<article class="person${p.isLead ? " lead" : ""}" id="participant-${index + 1}"><div class="person-top"><span class="avatar">${esc(
    p.initials,
  )}</span><div><strong>${esc(p.name)}</strong>${
    p.role || p.isLead ? `<span class="muted">${esc(p.role || "Руководитель проекта")}</span>` : ""
  }</div></div>${contributions}</article>`;
}

function team(model: LandingModel): string {
  if (model.team.length === 0) return "";
  const word = plural(model.team.length, "человек", "человека", "человек");
  return `<section class="section" id="team"><div class="wrap"><div class="kicker">Люди за проектом</div><h2>Команда <span class="count">${model.team.length} ${word}</span></h2><div class="person-grid">${model.team
    .map(personCard)
    .join("")}</div></div></section>`;
}

function outlook(model: LandingModel): string {
  if (model.outlook.length === 0 && !model.outlookIntro) return "";
  const items = model.outlook.map(point).join("");
  return `<section class="section alt" id="status"><div class="wrap"><div class="kicker">Следующий этап</div><h2>${esc(model.titles.outlook)}</h2>${
    model.outlookIntro ? `<p class="section-intro">${esc(model.outlookIntro)}</p>` : ""
  }${items ? `<div class="box"><ul>${items}</ul></div>` : ""}</div></section>`;
}

export function renderLandingHtml(model: LandingModel, options: { theme: LandingTheme; assets: LandingAssets }): string {
  const { theme, assets } = options;
  const resultsHtml = results(model);
  const teamHtml = team(model);
  const workHtml = features(model);
  const problemHtml = problem(model);
  const solutionHtml = solution(model);
  const techHtml = stack(model);
  const nav = [
    problemHtml || solutionHtml ? `<a href="#${problemHtml ? "problem" : "solution"}">О проекте</a>` : "",
    // Shown by the share page once the demo player is put in place of the marker.
    `<a href="#demo" hidden>Демо</a>`,
    resultsHtml ? `<a href="#results">${esc(model.titles.results)}</a>` : "",
    techHtml ? `<a href="#tech">${esc(model.titles.stack)}</a>` : "",
    teamHtml ? `<a href="#team">Команда</a>` : "",
  ].join("");
  return `<!doctype html>
<html lang="ru" data-theme="${theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(model.title)}</title>
${model.description ? `<meta name="description" content="${esc(model.description)}">` : ""}
<meta name="generator" content="Ленд, платформа УИИ">
<style>${assets.fontFaces}${landingCss(runTiming(Math.min(model.steps.length, SCREEN_STEPS)))}</style>
</head>
<body>
<header class="header"><div class="wrap nav"><a class="brand" href="#top"><img src="${esc(assets.catMark)}" alt="Маскот проекта"><span>Проект на платформе УИИ</span></a>${
    nav ? `<nav class="links" aria-label="Разделы страницы">${nav}</nav>` : ""
  }</div></header>
<main>
${hero(model, Boolean(resultsHtml), Boolean(teamHtml), assets.catHero)}
${problemHtml}
${solutionHtml}
${DEMO_MARKER}
${workHtml}
${resultsHtml}
${techHtml}
${teamHtml}
${outlook(model)}
</main>
<footer class="footer"><div class="wrap foot"><img src="${esc(assets.catHero)}" alt="Маскот УИИ"><div><strong>Проект выполнен на платформе УИИ</strong><p>Портфолио проектной команды</p></div></div></footer>
</body>
</html>
`;
}
