/**
 * The single rendering engine of the landing: model → complete standalone HTML document.
 * The preview iframe and the downloaded file are the same bytes from this function.
 * No scripts: animation is CSS only, and every piece of text is escaped.
 */

import type { BeforeAfter, LandingModel, LandingTheme, Metric, Person, Point } from "./model";
import { landingCss, runTiming } from "./styles";
import { plural } from "@/lib/plural";

export { plural };

export interface LandingAssets {
  /** @font-face rules for Geologica and Golos Text (data URIs in the downloaded file). */
  fontFaces: string;
  /** Small UII cat logo for the header (data URI). */
  catMark: string;
  /** Large cat for the hero screen and the footer (data URI), embedded once through a CSS variable. */
  catHero: string;
}

/** The hero screen animates at most this many steps; the "Что сделали" section lists all of them. */
export const SCREEN_STEPS = 8;

export function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}


const RING_C = 2 * Math.PI * 42;

function ring(percent: number): string {
  const dash = (RING_C * Math.min(100, Math.max(0, percent))) / 100;
  return `<svg class="ring" viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="42" fill="none" stroke="var(--track)" stroke-width="9"/><circle cx="50" cy="50" r="42" fill="none" stroke="var(--figure)" stroke-width="9" stroke-linecap="round" stroke-dasharray="${dash.toFixed(1)} ${RING_C.toFixed(1)}"/></svg>`;
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

function paragraphs(text: string, style = ""): string {
  return text
    .split(/\r?\n/)
    .map((p) => p.trim())
    .filter(Boolean)
    .map((p) => `<p${style ? ` style="${style}"` : ""}>${esc(p)}</p>`)
    .join("");
}

function point(p: Point): string {
  return p.title ? `<li><span><strong>${esc(p.title)}.</strong> ${esc(p.text)}</span></li>` : `<li><span>${esc(p.text)}</span></li>`;
}

function headline(model: LandingModel): { value: string; label: string } | null {
  if (model.beforeAfter) {
    return { value: `${model.beforeAfter.beforeText} → ${model.beforeAfter.afterText}`, label: model.beforeAfter.label };
  }
  const best = [...model.metrics].sort((a, b) => (b.ring ?? -1) - (a.ring ?? -1))[0];
  return best ? { value: best.value, label: best.label } : null;
}

function screen(model: LandingModel): string {
  const shown = model.steps.slice(0, SCREEN_STEPS);
  if (shown.length < 2) return "";
  const top = headline(model);
  const steps = shown
    .map(
      (s, i) =>
        `<li class="run__step run__step--${i}"><span class="run__dot"></span><span class="run__text"><b>${esc(s.title)}</b>${
          s.text ? `<small>${esc(s.text)}</small>` : ""
        }</span><span class="run__done">готово</span></li>`,
    )
    .join("");
  const client = model.facts.find((f) => f.label === "Заказчик")?.value || "Проект";
  return `<figure class="screen" role="img" aria-label="Схема проекта: ${shown.length} ${plural(shown.length, "этап", "этапа", "этапов")}">
<div class="screen__frame" aria-hidden="true">
<div class="screen__bar"><span>${esc(client)}</span><span class="live"><i></i>Работает</span></div>
<div class="screen__body"><div class="scan"></div><ol class="run">${steps}</ol><div class="screen__progress"><span></span></div>${
    top ? `<div class="toast"><b>${esc(top.value)}</b><span>${esc(top.label)}</span></div>` : ""
  }</div>
</div>
<span class="screen__cat cat" aria-hidden="true"></span>
</figure>`;
}

function hero(model: LandingModel, hasResults: boolean, hasTeam: boolean): string {
  const facts = model.facts.map((f) => `<div><dt>${esc(f.label)}</dt><dd>${esc(f.value)}</dd></div>`).join("");
  const cta = [
    hasResults ? `<a class="btn btn--main" href="#results">Посмотреть результаты</a>` : "",
    hasTeam ? `<a class="btn${hasResults ? "" : " btn--main"}" href="#team">Команда проекта</a>` : "",
  ].join("");
  return `<section class="hero"><div class="wrap hero__in">
<div class="hero__text"><h1>${esc(model.title)}</h1>${model.description ? `<p class="lead">${esc(model.description)}</p>` : ""}${
    facts ? `<dl class="facts">${facts}</dl>` : ""
  }${cta ? `<div class="cta">${cta}</div>` : ""}</div>
${screen(model)}
</div></section>`;
}

function changeCard(c: BeforeAfter): string {
  const max = Math.max(c.before, c.after, 1);
  const phrase = changePhrase(c);
  return `<div class="card change"><h3>${esc(c.label)}</h3>
<div class="bar"><div class="bar__label"><span>Было</span><strong style="color:var(--bad)">${esc(c.beforeText)}</strong></div><div class="bar__track"><div class="bar__fill" style="width:${((c.before / max) * 100).toFixed(1)}%;background:var(--bad)"></div></div></div>
<div class="bar"><div class="bar__label"><span>Стало</span><strong style="color:var(--figure)">${esc(c.afterText)}</strong></div><div class="bar__track"><div class="bar__fill" style="width:${((c.after / max) * 100).toFixed(1)}%;background:var(--figure);box-shadow:0 0 12px var(--figure)"></div></div></div>
${phrase ? `<div class="change__big">${esc(phrase)}</div>` : ""}<p class="metric__detail">${esc(c.detail)}</p></div>`;
}

function metricCard(m: Metric): string {
  return `<div class="card metric">${m.ring !== null ? ring(m.ring) : ""}<div><div class="metric__value">${esc(m.value)}</div><div class="metric__label">${esc(
    m.label,
  )}</div>${m.detail ? `<div class="metric__detail">${esc(m.detail)}</div>` : ""}</div></div>`;
}

function results(model: LandingModel): string {
  const cards = [model.beforeAfter ? changeCard(model.beforeAfter) : "", ...model.metrics.map(metricCard)].join("");
  if (!cards && model.resultNotes.length === 0 && !model.resultsIntro) return "";
  return `<section id="results" class="sec band"><div class="wrap">
<div class="sec__head"><h2>${esc(model.titles.results)}</h2></div>
${model.resultsIntro ? `<div class="intro">${paragraphs(model.resultsIntro)}</div>` : ""}
${cards ? `<div class="results">${cards}</div>` : ""}
${model.resultNotes.length ? `<ul class="notes">${model.resultNotes.map(point).join("")}</ul>` : ""}
</div></section>`;
}

function about(model: LandingModel): string {
  const hasAbout = Boolean(model.essence) || model.essenceItems.length > 0;
  const hasPurpose = model.purpose.length > 0 || Boolean(model.purposeIntro);
  if (!hasAbout && !hasPurpose) return "";
  const essenceList = model.essenceItems.length
    ? `<ul class="points">${model.essenceItems.map((t) => `<li><span>${esc(t)}</span></li>`).join("")}</ul>`
    : "";
  return `<section id="about" class="sec"><div class="wrap two">
${hasAbout ? `<div><h2 class="h-gap">${esc(model.titles.about)}</h2><div class="essence">${paragraphs(model.essence)}${essenceList}</div></div>` : ""}
${
    hasPurpose
      ? `<div><h2 class="h-gap">${esc(model.titles.purpose)}</h2>${
          model.purposeIntro ? `<div class="intro">${paragraphs(model.purposeIntro)}</div>` : ""
        }${model.purpose.length ? `<ul class="points">${model.purpose.map(point).join("")}</ul>` : ""}</div>`
      : ""
  }
</div></section>`;
}

function io(model: LandingModel): string {
  if (model.inputs.length === 0 && model.outputs.length === 0) return "";
  const card = (title: string, items: string[]) =>
    items.length
      ? `<div class="card"><h3>${esc(title)}</h3><ul class="points">${items.map((t) => `<li><span>${esc(t)}</span></li>`).join("")}</ul></div>`
      : "";
  return `<section class="sec band"><div class="wrap"><div class="io">${card(model.titles.inputs, model.inputs)}${card(
    model.titles.outputs,
    model.outputs,
  )}</div></div></section>`;
}

function steps(model: LandingModel): string {
  if (model.steps.length === 0 && !model.workIntro) return "";
  const cards = model.steps
    .map((s) => `<div class="card"><h3>${esc(s.title)}</h3>${s.text ? `<p>${esc(s.text)}</p>` : ""}</div>`)
    .join("");
  return `<section id="work" class="sec"><div class="wrap"><div class="sec__head"><h2>${esc(model.titles.work)}</h2></div>${
    model.workIntro ? `<div class="intro">${paragraphs(model.workIntro)}</div>` : ""
  }${cards ? `<div class="steps">${cards}</div>` : ""}</div></section>`;
}

function stack(model: LandingModel): string {
  if (model.stack.length === 0) return "";
  const groups = model.stack
    .map((g) => `<div><div class="stack__name">${esc(g.name)}</div><div class="chips">${g.items.map((i) => `<span>${esc(i)}</span>`).join("")}</div></div>`)
    .join("");
  return `<section class="sec band"><div class="wrap"><div class="sec__head"><h2>${esc(model.titles.stack)}</h2></div><div class="stack">${groups}</div></div></section>`;
}

function personCard(p: Person): string {
  const contributions = p.contributions.length
    ? `<details><summary>Вклад в проект</summary><ul>${p.contributions.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></details>`
    : "";
  return `<li class="card person${p.isLead ? " person--lead" : ""}"><div class="person__head"><span class="avatar" aria-hidden="true">${esc(
    p.initials,
  )}</span><div><div class="person__name">${esc(p.name)}</div>${
    p.role || p.isLead ? `<div class="person__role">${esc(p.role || "Руководитель проекта")}</div>` : ""
  }</div></div>${contributions}</li>`;
}

function team(model: LandingModel): string {
  if (model.team.length === 0) return "";
  return `<section id="team" class="sec"><div class="wrap"><div class="sec__head"><h2>Команда</h2><p class="sec__note">${model.team.length} ${plural(
    model.team.length,
    "человек",
    "человека",
    "человек",
  )}</p></div><ul class="team">${model.team.map(personCard).join("")}</ul></div></section>`;
}

function outlook(model: LandingModel): string {
  if (model.outlook.length === 0 && !model.outlookIntro) return "";
  const items = model.outlook
    .map((p) => (p.title ? `<li><strong>${esc(p.title)}.</strong> ${esc(p.text)}</li>` : `<li>${esc(p.text)}</li>`))
    .join("");
  return `<section class="sec"><div class="wrap"><div class="sec__head"><h2>${esc(model.titles.outlook)}</h2></div>${
    model.outlookIntro ? `<div class="intro">${paragraphs(model.outlookIntro)}</div>` : ""
  }${items ? `<ol class="outlook">${items}</ol>` : ""}</div></section>`;
}

export function renderLandingHtml(model: LandingModel, options: { theme: LandingTheme; assets: LandingAssets }): string {
  const { theme, assets } = options;
  const resultsHtml = results(model);
  const teamHtml = team(model);
  const workHtml = steps(model);
  const nav = [
    workHtml ? `<a href="#work">${esc(model.titles.work)}</a>` : "",
    resultsHtml ? `<a href="#results">${esc(model.titles.results)}</a>` : "",
    teamHtml ? `<a href="#team">Команда</a>` : "",
  ].join("");
  // The large cat appears twice (screen and footer) but is embedded once, as a CSS variable.
  const catVar = `:root{--cat:url("${assets.catHero.replace(/["\\]/g, "")}")}`;
  return `<!doctype html>
<html lang="ru" data-theme="${theme}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(model.title)}</title>
${model.description ? `<meta name="description" content="${esc(model.description)}">` : ""}
<meta name="generator" content="Ленд, платформа УИИ">
<style>${assets.fontFaces}${catVar}${landingCss(runTiming(Math.min(model.steps.length, SCREEN_STEPS)))}</style>
</head>
<body>
<header class="top"><div class="wrap top__in"><span class="brand"><img src="${esc(assets.catMark)}" alt="Логотип УИИ">Проект на платформе УИИ</span>${
    nav ? `<nav aria-label="Разделы страницы">${nav}</nav>` : ""
  }</div></header>
<main>
${hero(model, Boolean(resultsHtml), Boolean(teamHtml))}
${resultsHtml}
${about(model)}
${io(model)}
${workHtml}
${stack(model)}
${teamHtml}
${outlook(model)}
</main>
<footer class="foot"><div class="wrap foot__in"><span class="foot__cat cat" aria-hidden="true"></span><div><b>Проект выполнен на платформе УИИ</b><span>Страница собрана в Ленде из материалов команды</span></div></div></footer>
</body>
</html>
`;
}
