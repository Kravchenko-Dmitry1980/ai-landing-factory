# VR/AR Showcase (Stage P.5 MVP)

## 1. Purpose

VR/AR Showcase — это **надстройка** над обычным лендинг-пайплайном, а не его
замена. Она позволяет собрать «витрину» (exhibition stand) из нескольких
сгенерированных лендингов и прикрепить к ним ссылки на демо-проекты
(например, сделанные в AI Google Studio).

Поток данных:

```
generated landings → showcase registry → 3D/VR exhibition stand → demo links
```

Результат экспорта — один self-contained HTML-файл с 3D-сценой (A-Frame) и
доступным 2D-фолбэком.

## 2. Разница между landing export и showcase export

| | Landing export | Showcase export |
|---|---|---|
| Назначение | Один проект/лендинг | Витрина из нескольких проектов |
| Внешний JS | Нет (CSS-only) | A-Frame runtime (WebXR) |
| Режим | `PRODUCT_MODE=simple` | Отдельный режим P.5 |
| 3D | Нет | `<a-scene>` exhibition stand |
| Fallback | — | 2D-секция `.showcase-fallback` |

Обычный landing export **не меняется** и по-прежнему не содержит внешнего JS.

## 3. Почему A-Frame

- Декларативный HTML/WebXR — сцену можно генерировать как строку HTML,
  проще чем React Three Fiber export.
- Self-contained: одна `<script>`-ссылка на runtime + декларативные теги.
- Работает в обычном браузере без VR-гарнитуры; VR — опционально.

Runtime по умолчанию (P.5.1): **локальный vendored** файл
`vendor/aframe/aframe.min.js` — копируется рядом с экспортированным HTML.
Источник в репозитории: `frontend/public/vendor/aframe/aframe.min.js`
(A-Frame 1.7.0, MIT — см. `LICENSE.txt`).

Структура demo-экспорта:

```text
backend/data/exports/
  showcase_demo.html
  vendor/aframe/aframe.min.js
```

Открытие `showcase_demo.html` через `file://` или без интернета работает,
если рядом лежит скопированный vendor runtime.

**CDN override** (явный opt-in): query `?aframe_src=https://aframe.io/releases/1.7.0/aframe.min.js`
или флаг `--aframe-src` в demo-скрипте. Произвольные внешние домены отклоняются
(`sanitize_aframe_src`).

## 4. Почему не R3F / SuperSplat пока

- **React Three Fiber** — полезен позже для React preview/editor 3D, но в MVP
  усложнил бы simple-путь и сборку. Не подключаем.
- **SuperSplat** — future-модуль для photorealistic сцен/сканов. Не в MVP.
- **Open3D / Assimp** — backend/asset-processing слой для будущего. Не сейчас.
- **React Bits** — источник идей для оболочки/карточек, не обязательная
  зависимость.

## 5. Data contract

`backend/app/services/showcase/showcase_schema.py`:

```text
ShowcaseProject { id, title, description, landing_url?, demo_url?, demo_label?,
                  category?, tags?, accent?, source_project_id? }

ShowcaseConfig  { title, subtitle?, organization?,
                  layout: gallery_arc | grid_hall | circle_booths,
                  mode: web3d | vr_ready,
                  theme: university | tech | dark,
                  projects: ShowcaseProject[] }

ShowcaseExportResult { html, project_count, mode, warnings[] }
```

## 6. Demo links

Каждая карточка проекта может нести `demo_url` (например, AI Google Studio) и
`landing_url`. В 3D-сцене карточка кликабельна (минимальный inline-обработчик
`alfOpen`), в 2D-фолбэке — обычные `<a target="_blank" rel="noopener">`.

Demo-скрипт `backend/scripts/export_showcase_demo.py` собирает витрину из трёх
проектов: Эндокринология+, Indlab News Assistant, KSK Platform.

Пример demo-ссылки на AI Google Studio в UI builder (`/showcase`):

```text
demo_url: https://aistudio.google.com/
demo_label: AI Studio демо
```

## 7. Security

URL-валидация (`showcase_safety.sanitize_url` и `sanitize_aframe_src`):

- Разрешены для project links: `http://`, `https://`, относительные пути.
- Отклоняются: `javascript:`, `data:`, `vbscript:`, `file:`, `blob:`, `about:`.
- `aframe_src`: relative paths, localhost dev URLs, allowlisted `aframe.io/releases/.../aframe.min.js`.
- Произвольные внешние CDN для A-Frame — **запрещены** по умолчанию.

Экранирование (`escape_text`, `js_string_literal`): title, description,
labels, tags и URL экранируются перед вставкой в HTML/атрибуты. Inline-обработчик
дополнительно перепроверяет схему URL во время выполнения (defense in depth).

Тесты подтверждают: вредоносный `<script>` в title экранируется и не
исполняется; `javascript:` URL отбрасывается и не попадает в вывод.

## 8. Future roadmap

1. **R3F preview editor** — интерактивный редактор 3D-сцены в React.
2. **SuperSplat booth background** — photorealistic фоны/сканы стендов.
3. **WebXR mode** — полноценный VR-режим с контроллерами.
4. **3D asset upload** — загрузка моделей (Open3D/Assimp на backend).

## 9. Команды

```powershell
cd C:\Dima\Projects\CURSOR\_uat\ai-landing-factory-fresh\backend

# демо-витрина (offline-ready) → HTML + vendor runtime рядом
..\.venv\Scripts\python.exe scripts\export_showcase_demo.py
# backend/data/exports/showcase_demo.html
# backend/data/exports/vendor/aframe/aframe.min.js

# открыть showcase_demo.html без интернета (file:// или локальный сервер)

# опциональный smoke (офлайн, проверка безопасности)
..\.venv\Scripts\python.exe scripts\smoke_showcase_export.py

# тесты
..\.venv\Scripts\python.exe -m pytest tests\test_showcase_exporter.py -q
```

Frontend: страница `/showcase` (`frontend/src/app/showcase/page.tsx`).

## 10. Release safety

Showcase **не** входит в default simple release gate и не влияет на `run.ps1`.
`smoke_showcase_export.py` — опциональный smoke, кандидат во Full gate позже.
