# Web Quality Gate — AI Landing Factory

Чеклист качества **только для frontend preview и HTML export**.  
Не распространяется на backend, PII pipeline и renderer architecture.

## Reference

**Modern Web Guidance** (`~/.agents/skills/modern-web-guidance/`) — справочник best practices для аудита.  
Использовать **только как reference** при review; не внедрять паттерны автоматически и не переписывать frontend без явной задачи.

## Scope

| В scope | Вне scope |
|---------|-----------|
| `/preview/{id}` (в т.ч. `?style=university_platform`) | Backend API, БД, миграции |
| HTML export (`GET /api/v1/projects/{id}/export/html`) | PII pipeline, redaction, privacy |
| Responsive / a11y / perf preview & export | Renderer architecture, section registry |
| Theme `university_platform` | Editor UI, upload flow |

## Обязательный gate после изменений preview/export

```powershell
cd frontend
npm test
npm run build
```

Затем ручная проверка и smoke:

```powershell
# Backend должен быть запущен (127.0.0.1:8001)
cd frontend
npm run dev
# Открыть: http://localhost:3000/preview/{projectId}?style=university_platform

cd ..\backend
..\.venv\Scripts\python.exe scripts\smoke_university_export.py --project-id {projectId}
```

---

## Чеклист

### 1. Responsive (360 / 768 / 1440)

- [ ] **360px** — контент читаем, нет горизонтального скролла, CTA и навигация доступны
- [ ] **768px** — сетки и табы перестраиваются без наложений
- [ ] **1440px** — контент не растягивается бесконтрольно; `max-width` и отступы согласованы
- [ ] Изображения и диаграммы масштабируются без обрезки критичного контента

### 2. Accessibility

- [ ] **Heading hierarchy** — один `h1`, логичная цепочка `h2` → `h3`, без пропусков уровней
- [ ] **ARIA labels** — интерактивные элементы без видимого текста имеют `aria-label` / `aria-labelledby`
- [ ] **Keyboard navigation** — Tab проходит все интерактивные элементы; focus visible; Escape закрывает модалки/табы где применимо
- [ ] Ссылки и кнопки имеют понятный accessible name
- [ ] `lang` на `<html>` задан (в export — standalone HTML)

### 3. Contrast

- [ ] Текст на фоне соответствует WCAG AA (4.5:1 для body, 3:1 для крупного текста)
- [ ] Ссылки и состояния hover/focus различимы
- [ ] Для `university_platform`: светлая академическая палитра, без «приглушённого серого на сером»

### 4. Console & hydration

- [ ] **No console errors** — DevTools Console чист при загрузке preview и переключении табов/секций
- [ ] **No hydration errors** — нет React hydration mismatch в Next.js preview
- [ ] Нет необработанных rejected promises / failed fetch без UI feedback

### 5. Performance

- [ ] **No heavy animations** — нет бесконечных или GPU-тяжёлых эффектов на scroll/resize
- [ ] **No long blocking render** — первый meaningful paint без заметной блокировки main thread
- [ ] Framer Motion / Recharts не создают layout thrashing при resize
- [ ] Export HTML не тянет лишние runtime-зависимости

### 6. Modern CSS (только где оправдано)

- [ ] Container queries, `:has()`, view transitions — **только** если решают конкретную проблему preview/export
- [ ] Не добавлять experimental CSS ради «современности»
- [ ] Предпочитать существующие CSS vars из StyleProfile / theme tokens

### 7. Export HTML standalone

- [ ] Файл открывается двойным кликом **без** dev server и backend
- [ ] Стили inlined или embedded; нет broken relative paths к `/api/...`
- [ ] Все секции контракта отрендерены (hero, modules, team, stack и т.д.)
- [ ] Нет `localhost` URLs в assets и ссылках

### 8. Theme `university_platform`

- [ ] Светлый академический стиль: белый/светло-серый фон, тёмный текст, сдержанные акценты
- [ ] **Запрещено**: random gradients, dark theme, glassmorphism, neon glow
- [ ] Типографика: читаемая, «университетская» — без marketing-heavy hero
- [ ] Визуально согласовано с целевым референсом university platform landing

---

## Ограничения (hard rules)

1. **Не переписывать frontend** без явной задачи на изменение preview/export.
2. **Не менять backend**, PII pipeline, renderer architecture.
3. **Не добавлять новые npm-библиотеки** без обоснования в задаче.
4. Modern Web Guidance — **audit reference**, не источник автоматических рефакторингов.

## Связанные документы

- `frontend/docs/README_RENDERING.md` — renderer & style profiles
- `frontend/docs/ENDOCRINOLOGY_ACCEPTANCE_CHECKLIST.md` — пример domain-specific acceptance
