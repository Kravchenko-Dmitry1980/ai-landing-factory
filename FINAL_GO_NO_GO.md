# Final GO / NO-GO

Дата: 2026-07-26 · Основание: `UAT_ALGOFUSION_DOCX_REPAIR_REPORT.md`, `UAT_FREEMODEL_REPORT.md`, `SERVER_DEPLOY_PREP.md`, `DEPLOY_PREP_REPORT.md`

## Decision

| Контур | Решение |
|---|---|
| Локальная демонстрация | **GO** |
| DOCX Algofusion full-content pipeline | **GO** |
| Продукт без AI (`LLM_PROVIDER=mock`) | **GO** |
| Показ демо-пака offline | **GO** |
| Deploy prep (templates/scripts/archives) | **READY FOR SERVER PARAMS** |
| Static demo deploy | **READY WHEN SERVER PROVIDED** |
| Full systemd + nginx deploy | **READY WHEN SERVER PROVIDED** |
| Docker Compose | **DRAFT ONLY** (не primary) |
| FreeModel / AI-контур | **NO-GO** (кредиты не тратить) |
| Production deploy на сервер | **NO-GO** — нет параметров сервера |

Итог: **GO FOR DEMO + READY FOR SERVER PARAMS.**

## Facts (Algofusion repair)

- Root cause: DOCX с большой командой классифицировался как `team_list` → structured parser не вызывался.
- После фикса: `parser_mode=structured`, title/client/timeline/lead заполнены, team=11, stack=30, results=9, outlook=6.
- Standard HTML / WOW ZIP содержат ключевые факты.
- Targeted tests: Algofusion 9/9 + regression 39 passed (повторно в deploy prep).

## Facts (Deploy prep)

- Созданы Mode A/B/C артефакты в `deploy/`.
- Локальные zip: `.runtime/release/ai-landing-static-demo.zip`, `.runtime/release/ai-landing-full-product.zip`.
- Env production examples без секретов.
- Security audit: **PASS** (WARN только на string literals в vendored aframe).
- Backend health 200; frontend build/lint OK; runtime OK.
- `git push` / server deploy / FreeModel smoke — не выполнялись.

## Risks

| Риск | Уровень | Комментарий |
|---|---|---|
| Старые пустые contracts в `backend/data` | Низкий | Нужен re-upload/regenerate |
| Heuristic team role swap | Низкий | 1–2 участника могут иметь role↔contrib |
| FreeModel / JSON mode | Средний | Не тестировался; держать выключенным |
| Server deploy без параметров | Высокий | По-прежнему NO-GO на выполнение |
| Vendored aframe CDN strings | Низкий | Не сетевые загрузки нашего HTML |

## Blockers

- Нет параметров production-сервера → деплой запрещён.
- FreeModel не включать без явного запроса и бюджета.

## What to open locally

- Home: http://localhost:3000
- Showcase: http://localhost:3000/showcase
- Deploy prep report: `DEPLOY_PREP_REPORT.md`
- Static deploy: `deploy/static/README_STATIC_DEPLOY.md`
- Full deploy: `deploy/ubuntu/README_FULL_SYSTEMD_DEPLOY.md`
